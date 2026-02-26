from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash
from database import db
from config import Config
from dotenv import load_dotenv
import redis
import os

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='/static')
app.config.from_object(Config)

# initialize extensions
db.init_app(app)
CORS(app)
mail = Mail(app)
jwt = JWTManager(app)

# redis cache connection
cache = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
app.config['CACHE'] = cache

# register blueprints
from models import *
from routes import *

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(doctor_bp, url_prefix='/api/doctor')
app.register_blueprint(patient_bp, url_prefix='/api/patient')

# serve frontend
@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_frontend(path):
    frontend_path = os.path.join('../frontend', path)
    if os.path.exists(frontend_path) and os.path.isfile(frontend_path):
        return send_from_directory('../frontend', path)
    return send_from_directory('../frontend', 'index.html')

# error handlers
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Endpoint not found'}), 404
    return send_from_directory('../frontend', 'index.html')

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

# create database and admin user
def setup_db():
    with app.app_context():
        db.create_all()
        
        # create admin if not exists
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@medsync.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('✓ Admin created: admin / admin123')

if __name__ == '__main__':
    setup_db()
    app.run(debug=True, port=5000)