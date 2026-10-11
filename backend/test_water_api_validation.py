import unittest

from app import create_app, db
from app.config import Config
from app.models.farm import Farm
from app.models.tank import Tank, WaterReading
from app.models.user import User


class IsolatedTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    DEFAULT_TANK_DEPTH_CM = 100.0
    TANK_DEPTHS_CM = {1: 120.0}
    HC_SR04_MIN_DISTANCE_CM = 2.0
    HC_SR04_MAX_DISTANCE_CM = 400.0


class WaterApiValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(IsolatedTestConfig)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            user = User(name='Test Farmer', email='test@example.invalid')
            user.set_password('not-a-real-password')
            db.session.add(user)
            db.session.flush()
            farm = Farm(user_id=user.id, farm_name='Test Farm')
            db.session.add(farm)
            db.session.flush()
            db.session.add(Tank(farm_id=farm.id, tank_name='Test Tank', capacity_liters=6000.0))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def _reading_count(self):
        with self.app.app_context():
            return WaterReading.query.count()

    def test_current_reading_is_unavailable_when_none_exists(self):
        response = self.client.get('/api/water/current')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()['data']
        self.assertFalse(data['available'])
        self.assertEqual(data['status'], 'UNAVAILABLE')
        self.assertIsNone(data['water_level_percent'])
        self.assertIsNone(data['water_volume_liters'])
        self.assertIsNone(data['distance_cm'])
        self.assertFalse(data['is_simulated'])

    def test_distance_only_uses_configured_tank_depth_and_capacity(self):
        response = self.client.post(
            '/api/water/readings',
            json={'tank_id': 1, 'distance_cm': 30.0}
        )

        self.assertEqual(response.status_code, 201)
        data = response.get_json()['data']
        self.assertEqual(data['water_level_percent'], 75.0)
        self.assertEqual(data['water_volume_liters'], 4500.0)

    def test_current_returns_the_persisted_tank_reading(self):
        self.client.post(
            '/api/water/readings',
            json={'tank_id': 1, 'distance_cm': 30.0}
        )

        response = self.client.get('/api/water/current?tank_id=1')

        self.assertEqual(response.status_code, 200)
        data = response.get_json()['data']
        self.assertTrue(data['available'])
        self.assertEqual(data['tank_id'], 1)
        self.assertEqual(data['water_level_percent'], 75.0)
        self.assertEqual(data['water_volume_liters'], 4500.0)

    def test_current_labels_seeded_and_unknown_origin_readings(self):
        with self.app.app_context():
            reading = WaterReading(
                tank_id=1,
                distance_cm=30.0,
                water_level_percent=75.0,
                water_volume_liters=4500.0,
                status='SIMULATED'
            )
            db.session.add(reading)
            db.session.commit()

        simulated = self.client.get('/api/water/current').get_json()['data']
        self.assertTrue(simulated['is_simulated'])
        self.assertEqual(simulated['source'], 'SEEDED_SIMULATION')

        with self.app.app_context():
            reading = WaterReading.query.first()
            reading.status = 'NORMAL'
            db.session.commit()

        unverified = self.client.get('/api/water/current').get_json()['data']
        self.assertIsNone(unverified['is_simulated'])
        self.assertEqual(unverified['source'], 'DATABASE_UNVERIFIED')

    def test_invalid_measurements_are_rejected_without_saving(self):
        invalid_payloads = [
            {'distance_cm': 1.9},
            {'distance_cm': 120.1},
            {'distance_cm': float('nan')},
            {'distance_cm': float('inf')},
            {'distance_cm': 'not-a-number'},
            {'distance_cm': True},
            {'water_level_percent': 100.1},
            {'water_level_percent': False},
            {'water_volume_liters': -1.0, 'water_level_percent': 50.0},
            {'water_volume_liters': 6001.0, 'water_level_percent': 50.0},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    '/api/water/readings',
                    json={'tank_id': 1, **payload}
                )
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.get_json()['success'])
                self.assertEqual(self._reading_count(), 0)

    def test_inconsistent_measurements_are_rejected(self):
        response = self.client.post(
            '/api/water/readings',
            json={
                'tank_id': 1,
                'distance_cm': 30.0,
                'water_level_percent': 68.0,
                'water_volume_liters': 4080.0,
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._reading_count(), 0)

    def test_unknown_tank_is_rejected(self):
        response = self.client.post(
            '/api/water/readings',
            json={'tank_id': 999, 'distance_cm': 30.0}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._reading_count(), 0)

    def test_malformed_or_non_object_json_is_rejected(self):
        malformed = self.client.post(
            '/api/water/readings',
            data='{bad json',
            content_type='application/json'
        )
        non_object = self.client.post('/api/water/readings', json=[1, 2, 3])

        self.assertEqual(malformed.status_code, 400)
        self.assertEqual(non_object.status_code, 400)
        self.assertEqual(self._reading_count(), 0)

    def test_invalid_tank_ids_are_rejected(self):
        for tank_id in (True, 0, -1, 1.0, 1.5, 'bad'):
            with self.subTest(tank_id=tank_id):
                response = self.client.post(
                    '/api/water/readings',
                    json={'tank_id': tank_id, 'distance_cm': 30.0}
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self._reading_count(), 0)


if __name__ == '__main__':
    unittest.main()
