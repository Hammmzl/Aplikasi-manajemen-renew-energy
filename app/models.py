from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
from sqlalchemy import Numeric

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relasi ke tabel waste_oil_purchases
    purchases = db.relationship('WasteOilPurchase', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @password.setter
    def password(self, password_plain):
        self.password_hash = generate_password_hash(password_plain)

    def verify_password(self, password_plain):
        return check_password_hash(self.password_hash, password_plain)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# WasteOilPurchase model
class WasteOilPurchase(db.Model):
    __tablename__ = 'waste_oil_purchases'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tanggal_pembelian = db.Column(db.Date, nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    harga_per_liter = db.Column(db.Integer, nullable=False)
    total_harga = db.Column(Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relasi ke Client
    client = db.relationship('Client', back_populates='pembelian')

    def __repr__(self):
        return f'<WasteOilPurchase {self.client_id} {self.tanggal_pembelian}>'


# Client model
class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    nama_client = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(255))
    no_hp = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke WasteOilPurchase
    pembelian = db.relationship('WasteOilPurchase', back_populates='client', lazy=True)

    def __repr__(self):
        return f'<Client {self.nama_client}>'

    
# SuratJalan model

class SuratJalan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(50), unique=True, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    no_kendaraan = db.Column(db.String(50), nullable=False)
    tujuan = db.Column(db.String(100), nullable=False)
    owner = db.Column(db.String(100))
    supir = db.Column(db.String(100))
    penerima = db.Column(db.String(100))
    details = db.relationship('SuratJalanDetail', backref='surat_jalan', cascade="all, delete-orphan")

class SuratJalanDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surat_jalan_id = db.Column(db.Integer, db.ForeignKey('surat_jalan.id'))
    nama_barang = db.Column(db.String(100), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    keterangan = db.Column(db.String(200))


class OtherTransaction(db.Model):
    __tablename__ = 'other_transactions'

    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    keterangan = db.Column(db.String(255), nullable=False)
    pemasukan = db.Column(Numeric(12, 2), default=0)
    pengeluaran = db.Column(Numeric(12, 2), default=0)
    metode_pembayaran = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<OtherTransaction {self.tanggal} - {self.keterangan}>'
    

class HargaModalBulanan(db.Model):
    __tablename__ = 'harga_modal_bulanan'
    id = db.Column(db.Integer, primary_key=True)
    bulan = db.Column(db.String(7), unique=True, nullable=False)  # '2025-05'
    harga_modal = db.Column(Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


