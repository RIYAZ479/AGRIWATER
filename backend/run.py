import os
from app import create_app
from seed_data import seed_database

app = create_app()

if __name__ == '__main__':
    # Auto-seed default database if first run
    try:
        seed_database()
    except Exception as e:
        print(f"[Warning] Seed database error: {e}")

    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f"  AgriWater AI — Flask Backend Server Running")
    print(f"  API Root: http://127.0.0.1:{port}/api")
    print(f"  Health Check: http://127.0.0.1:{port}/api/health")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
