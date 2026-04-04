from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange



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

#pemabahan class untuk form transaksi lain-lain
class OtherTransactionForm(FlaskForm):
    tanggal = DateField('Tanggal', format='%Y-%m-%d', validators=[DataRequired()])
    keterangan = StringField('Keterangan', validators=[DataRequired()])
    pemasukan = IntegerField('Pemasukan', default=0)
    pengeluaran = IntegerField('Pengeluaran', default=0)
    metode_pembayaran = SelectField('Metode Pembayaran', choices=[('cash', 'Cash'), ('transfer', 'Transfer')])
    submit = SubmitField('Simpan')


