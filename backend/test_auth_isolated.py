"""
AgriWater AI — Isolated In-Memory Authentication Test Suite
===========================================================
Executes exclusively against an in-memory SQLite database (sqlite:///:memory:).
Validates:
1. Public registration and login.
2. Cryptographic token generation and verification.
3. Protected route enforcement (@token_required).
4. Rejection of missing, tampered, or malformed tokens.
5. Backward compatibility for unauthenticated frontend telemetry polling.
"""

import unittest
import sys
from pathlib import Path

# Add backend directory to path
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from app import create_app, db
from app.models.user import User
from app.models.farm import Farm
from app.models.tank import Tank, WaterReading
from app.models.alert import Alert
from app.utils.auth import generate_auth_token, verify_auth_token


class TestAuthIsolated(unittest.TestCase):
    def setUp(self):
        """Initializes an ephemeral in-memory SQLite test app."""
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key-agriwater-2026'
        })
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Seed isolated test user
            user = User(name="Test Farmer", email="farmer@agriwater.io")
            user.set_password("SecureFarmer123!")
            db.session.add(user)

            # Seed isolated test farm
            farm = Farm(user_id=1, farm_name="Isolated Test Farm", area=2.5, location="Plot A")
            db.session.add(farm)

            # Seed isolated test tank and reading for dashboard verification
            tank = Tank(farm_id=1, tank_name="Test Reservoir", capacity_liters=10000.0, current_level_percent=60.0)
            db.session.add(tank)

            reading = WaterReading(tank_id=1, distance_cm=12.0, water_level_percent=60.0, water_volume_liters=6000.0, status='NORMAL')
            db.session.add(reading)

            # Seed isolated test alert
            alert = Alert(farm_id=1, alert_type="TEST", message="Test alert item", severity="info")
            db.session.add(alert)

            db.session.commit()

    def tearDown(self):
        """Drops ephemeral in-memory schema."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_01_public_registration(self):
        """Verify user registration remains public and stores hashed password."""
        payload = {
            "name": "Jane Doe",
            "email": "jane@agriwater.io",
            "password": "JanePassword456!"
        }
        r = self.client.post('/api/auth/register', json=payload)
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['email'], "jane@agriwater.io")
        self.assertNotIn('password', data['data'])

        # Verify password hash in memory database
        with self.app.app_context():
            u = User.query.filter_by(email="jane@agriwater.io").first()
            self.assertIsNotNone(u)
            self.assertTrue(u.check_password("JanePassword456!"))

    def test_02_login_issues_genuine_signed_token(self):
        """Verify login issues a real cryptographically signed token rather than mock string."""
        payload = {
            "email": "farmer@agriwater.io",
            "password": "SecureFarmer123!"
        }
        r = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data['success'])

        token = data['data']['token']
        self.assertIsInstance(token, str)
        self.assertNotIn('mock-jwt-token', token)
        self.assertEqual(data['data'].get('token_type'), 'Bearer')
        self.assertEqual(data['data'].get('expires_in'), 86400)

        # Verify token can be decoded by verify_auth_token
        with self.app.app_context():
            verified_user = verify_auth_token(token)
            self.assertIsNotNone(verified_user)
            self.assertEqual(verified_user.email, "farmer@agriwater.io")

    def test_03_login_rejects_invalid_credentials(self):
        """Verify login rejects incorrect credentials with HTTP 401."""
        payload = {
            "email": "farmer@agriwater.io",
            "password": "WrongPassword!"
        }
        r = self.client.post('/api/auth/login', json=payload)
        self.assertEqual(r.status_code, 401)
        data = r.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Invalid email or password')

    def test_04_auth_me_endpoint_with_valid_token(self):
        """Verify GET /api/auth/me returns current user identity with valid bearer token."""
        with self.app.app_context():
            token = generate_auth_token(1)

        headers = {'Authorization': f'Bearer {token}'}
        r = self.client.get('/api/auth/me', headers=headers)
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['email'], "farmer@agriwater.io")

    def test_05_protected_route_rejects_missing_token(self):
        """Verify mutating farm routes reject requests lacking an Authorization header with HTTP 401."""
        r_del = self.client.delete('/api/farms/1')
        self.assertEqual(r_del.status_code, 401)
        data_del = r_del.get_json()
        self.assertFalse(data_del['success'])
        self.assertIn('Authentication token is required', data_del['error'])

        r_post = self.client.post('/api/farms', json={'farm_name': 'Hacker Farm'})
        self.assertEqual(r_post.status_code, 401)

        r_clear = self.client.delete('/api/alerts')
        self.assertEqual(r_clear.status_code, 401)

    def test_06_protected_route_rejects_tampered_token(self):
        """Verify mutating routes reject forged or modified tokens with HTTP 401."""
        fake_token = "eyJhbGciOiJIUzI1NiJ9.tampered.token"
        headers = {'Authorization': f'Bearer {fake_token}'}
        r = self.client.delete('/api/farms/1', headers=headers)
        self.assertEqual(r.status_code, 401)
        data = r.get_json()
        self.assertFalse(data['success'])
        self.assertIn('Invalid, tampered, or expired token', data['error'])

    def test_07_protected_route_accepts_valid_token(self):
        """Verify mutating routes succeed when supplied with a valid Bearer token."""
        with self.app.app_context():
            token = generate_auth_token(1)

        headers = {'Authorization': f'Bearer {token}'}

        # 1. Create farm with token
        r_post = self.client.post('/api/farms', json={'farm_name': 'Authenticated Farm', 'area': 4.0}, headers=headers)
        self.assertEqual(r_post.status_code, 201)
        created_id = r_post.get_json()['data']['id']

        # 2. Update farm with token
        r_put = self.client.put(f'/api/farms/{created_id}', json={'farm_name': 'Updated Farm Name'}, headers=headers)
        self.assertEqual(r_put.status_code, 200)

        # 3. Delete farm with token
        r_del = self.client.delete(f'/api/farms/{created_id}', headers=headers)
        self.assertEqual(r_del.status_code, 200)

        # 4. Clear alerts with token
        r_clear = self.client.delete('/api/alerts', headers=headers)
        self.assertEqual(r_clear.status_code, 200)

    def test_08_public_dashboard_endpoints_remain_accessible(self):
        """Verify read-only endpoints accessed by frontend dashboard do NOT require tokens."""
        # Frontend dashboard calls these unauthenticated:
        endpoints = [
            '/api/health',
            '/api',
            '/api/farms',
            '/api/farms/1',
            '/api/water/current',
            '/api/water/readings',
            '/api/crops',
            '/api/tanks',
            '/api/alerts'
        ]

        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(
                r.status_code, 200,
                f"Dashboard endpoint {ep} broke with status {r.status_code}: {r.get_data(as_text=True)}"
            )
            data = r.get_json()
            self.assertTrue(data.get('success', False))


def run_tests():
    print("\n=======================================================")
    print("  AgriWater AI — Isolated Authentication Test Suite")
    print("  Target: In-Memory SQLite (sqlite:///:memory:)")
    print("=======================================================\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuthIsolated)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
