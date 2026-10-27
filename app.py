from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from flask_mail import Mail
import os

def create_app():
    app = Flask(__name__, 
                static_folder='static', 
                static_url_path='/static')

    app.config.from_object(Config)

    
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print("✅ Static folder:", app.static_folder)
    print("✅ Static URL path:", app.static_url_path)

    
    def format_rupiah(value):
        if value is None:
            return "Rp 0,00"
        try:
            angka = int(float(value))
            formatted = f"{angka:,.0f}".replace(",", ".")
            return f"Rp {formatted},00"
        except:
            return "Rp 0,00"

    app.jinja_env.filters['format_rupiah'] = format_rupiah

    # Inisialisasi Database
    db.init_app(app)

    # Inisialisasi Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
        # Inisialisasi Flask-Mail untuk fitur lupa password
    mail = Mail()
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprint
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    
    with app.app_context():
        db.create_all()

        # Seed Admin
        if not User.query.filter_by(email='admin@mobilsecond.medan').first():
            admin = User(nama='Admin Utama', email='admin@mobilsecond.medan', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Akun Admin dibuat")

        # Seed Seller
        if not User.query.filter_by(email='seller@mobilsecond.medan').first():
            seller = User(nama='Seller Medan', email='seller@mobilsecond.medan', role='seller')
            seller.set_password('seller123')
            db.session.add(seller)
            print("✅ Akun Seller dibuat")

        db.session.commit()

    
    @app.context_processor
    def inject_admin_whatsapp():
        from models import User
        admin = User.query.filter_by(role='admin').first()
        if admin and admin.whatsapp_number:
            return dict(admin_whatsapp=admin.whatsapp_number)
        return dict(admin_whatsapp=None)

    print("✅ Aplikasi Mobilsecond.medan siap dijalankan!")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)