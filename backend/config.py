import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # app settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'medsync-secret-key-2024')
    
    # database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///medsync.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # jwt settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'medsync-jwt-key-2024')
    
    # redis settings
    REDIS_URL = 'redis://localhost:6379/0'
    
    # celery settings
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    
    # email settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')