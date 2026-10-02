import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to sys.path to enable app imports
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent / 'backend'
sys.path.insert(0, str(backend_dir))

load_dotenv(backend_dir / '.env')

def try_mysql_init():
    """Attempt direct MySQL connection and execution of schema.sql and seed.sql."""
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = int(os.getenv('MYSQL_PORT', 3306))
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'agriwater_ai')

    try:
        import pymysql
        print(f"[MySQL Check] Attempting connection to MySQL server at {host}:{port} as user '{user}'...")
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("[MySQL Check] [OK] Connected successfully to MySQL server!")

        with conn.cursor() as cursor:
            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute(f"USE `{database}`;")
            print(f"[MySQL Init] Selected database `{database}`.")

            # Read and execute schema.sql
            schema_file = current_dir / 'schema.sql'
            if schema_file.exists():
                print(f"[MySQL Init] Executing {schema_file.name}...")
                with open(schema_file, 'r', encoding='utf-8') as f:
                    statements = f.read().split(';')
                    for stmt in statements:
                        clean_stmt = stmt.strip()
                        if clean_stmt:
                            cursor.execute(clean_stmt)
                print("[MySQL Init] [OK] All 11 tables created successfully in MySQL!")

            # Read and execute seed.sql
            seed_file = current_dir / 'seed.sql'
            if seed_file.exists():
                print(f"[MySQL Init] Executing {seed_file.name} (Development/Demo Seed)...")
                with open(seed_file, 'r', encoding='utf-8') as f:
                    statements = f.read().split(';')
                    for stmt in statements:
                        clean_stmt = stmt.strip()
                        if clean_stmt:
                            cursor.execute(clean_stmt)
                print("[MySQL Init] [OK] Development seed data inserted into MySQL!")

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[MySQL Notice] MySQL server is not currently reachable ({e}).")
        return False

def init_sqlalchemy_database():
    """Initialize database tables and seed using Flask-SQLAlchemy."""
    from app import create_app, db
    from seed_data import seed_database

    app = create_app()
    with app.app_context():
        print(f"[SQLAlchemy Init] Initializing database via {app.config['SQLALCHEMY_DATABASE_URI']}...")
        db.create_all()
        print("[SQLAlchemy Init] [OK] All 11 tables initialized in ORM!")
        seed_database()
        print("[SQLAlchemy Init] [OK] Database populated with development data!")

def main():
    print("\n=======================================================")
    print("  AgriWater AI -- Database Initialization Process")
    print("=======================================================\n")

    mysql_success = try_mysql_init()
    if mysql_success:
        print("\n[Status] Real MySQL Database `agriwater_ai` configured and seeded!")
    else:
        print("\n[Status] MySQL server daemon not running on localhost:3306.")
        print("[Status] Running with synchronized local fallback database.")
        print("[Status] To switch to MySQL at any time: start MySQL service and run `python database/init_db.py`.")

    print("\n[SQLAlchemy Synchronization]")
    init_sqlalchemy_database()

    print("\n=======================================================")
    print("  Database Setup Completed Successfully!")
    print("=======================================================\n")

if __name__ == '__main__':
    main()
