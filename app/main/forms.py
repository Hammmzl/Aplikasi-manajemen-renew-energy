from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, DateField, IntegerField, FieldList, FormField, SubmitField, SelectField
from wtforms.validators import DataRequired
from wtforms.validators import DataRequired, NumberRange
from app.models import Client

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')



class WasteOilPurchaseForm(FlaskForm):
    client_id = SelectField('Nama Client', coerce=int, validators=[DataRequired()])
    tanggal_pembelian = DateField('Tanggal Pembelian', validators=[DataRequired()])
    jumlah = DecimalField('Jumlah (liter)', validators=[DataRequired(), NumberRange(min=0)])
    harga_per_liter = DecimalField('Harga per Liter', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Simpan')



class SuratJalanDetailForm(FlaskForm):
    nama_barang = StringField('Nama Barang', validators=[DataRequired()])
    jumlah = IntegerField('Jumlah', validators=[DataRequired()])
    keterangan = StringField('Keterangan')
    submit = SubmitField('Simpan')

class SuratJalanForm(FlaskForm):
    nomor = StringField('No. Surat Jalan', validators=[DataRequired()])
    tanggal = DateField('Tanggal', validators=[DataRequired()])
    no_kendaraan = StringField('No. Kendaraan', validators=[DataRequired()])
    tujuan = StringField('Tujuan', validators=[DataRequired()])
    owner = StringField('Owner', validators=[DataRequired()])
    supir = StringField('Supir', validators=[DataRequired()])
    penerima = StringField('Penerima', validators=[DataRequired()])
    submit = SubmitField('Simpan')


class OtherTransactionForm(FlaskForm):
    tanggal = DateField('Tanggal', format='%Y-%m-%d', validators=[DataRequired()])
    keterangan = StringField('Keterangan', validators=[DataRequired()])
    pemasukan = IntegerField('Pemasukan', default=0)
    pengeluaran = IntegerField('Pengeluaran', default=0)
    metode_pembayaran = SelectField('Metode Pembayaran', choices=[('cash', 'Cash'), ('transfer', 'Transfer')])
    submit = SubmitField('Simpan')


