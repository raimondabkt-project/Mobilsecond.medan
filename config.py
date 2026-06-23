import os
from dotenv import load_dotenv

load_dotenv()  # Membaca file .env

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mobilsecond-medan-secret-key-2026')
    
    # Database MySQL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:password@localhost/mobilsecond_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Elasticsearch
    ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://localhost:9200')
    INDEX_NAME = 'katalog_mobil_bekas'
    
    # Folder upload gambar (kalau nanti butuh)
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

        # ==================== MAIL CONFIG (untuk fitur lupa password) ====================
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'Mobil Second Medan <no-reply@mobilsecond.medan>')
    # ============================================================