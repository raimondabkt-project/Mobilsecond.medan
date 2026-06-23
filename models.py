from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ==================== TABEL USER (Admin + Seller) ====================
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='aktif')

    # ==================== KOLOM WHATSAPP ADMIN ====================
    whatsapp_number = db.Column(db.String(20), nullable=True)  # Format: 62812xxxxxxx
    # ============================================================

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Mobil(db.Model):
    __tablename__ = 'mobil'

    id = db.Column(db.Integer, primary_key=True)
    kode_mobil = db.Column(db.String(20), unique=True, nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    harga = db.Column(db.BigInteger, nullable=False)
    kilometer = db.Column(db.Integer, nullable=False)
    transmisi = db.Column(db.String(20), nullable=False)
    deskripsi = db.Column(db.Text)
    gambar = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Ready', nullable=False)
    
    # ==================== TAMBAHKAN BARIS INI ====================
    uploaded_by_role = db.Column(db.String(20), default='admin', nullable=False)
    # ============================================================

    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seller = db.relationship('User', backref=db.backref('mobils', lazy=True))

    is_recommended = db.Column(db.Boolean, default=False)    

    is_favorite = db.Column(db.Boolean, default=False)   # ← Tambahkan ini

    fotos = db.relationship('MobilFoto', backref='mobil', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Mobil {self.kode_mobil}>'
    
class MobilFoto(db.Model):
    __tablename__ = 'mobil_foto'
    
    id = db.Column(db.Integer, primary_key=True)
    mobil_id = db.Column(db.Integer, db.ForeignKey('mobil.id'), nullable=False)
    nama_file = db.Column(db.String(255), nullable=False)
    urutan = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())