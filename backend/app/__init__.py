import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Import and register blueprints
    from app.routes.auth import auth_bp
    from app.routes.farms import farms_bp
    from app.routes.crops import crops_bp
    from app.routes.tanks import tanks_bp
    from app.routes.water import water_bp
    from app.routes.weather import weather_bp
    from app.routes.irrigation import irrigation_bp
    from app.routes.ai import ai_bp
    from app.routes.alerts import alerts_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(farms_bp, url_prefix='/api')
    app.register_blueprint(crops_bp, url_prefix='/api')
    app.register_blueprint(tanks_bp, url_prefix='/api')
    app.register_blueprint(water_bp, url_prefix='/api')
    app.register_blueprint(weather_bp, url_prefix='/api')
    app.register_blueprint(irrigation_bp, url_prefix='/api')
    app.register_blueprint(ai_bp, url_prefix='/api')
    app.register_blueprint(alerts_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')

    @app.route('/', methods=['GET'])
    @app.route('/api', methods=['GET'])
    def root():
        return jsonify({
            'success': True,
            'service': 'AgriWater AI Backend API',
            'version': '1.0.0',
            'documentation': '/api/health'
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        db_type = 'sqlite'
        if 'mysql' in str(app.config.get('SQLALCHEMY_DATABASE_URI', '')):
            db_type = 'mysql'
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'AgriWater AI Backend API',
            'version': '1.0.0',
            'database': db_type
        })

    # Standard error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            'success': False,
            'error': str(e.description if hasattr(e, 'description') else 'Bad Request')
        }), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({
            'success': False,
            'error': str(e.description if hasattr(e, 'description') else 'Resource not found')
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed'
        }), 405

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            'success': False,
            'error': 'Internal Server Error'
        }), 500

    # Auto-create tables in app context
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"[Warning] Table creation exception: {e}")

    return app
