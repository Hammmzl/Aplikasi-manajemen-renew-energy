from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional, Email

class ClientForm(FlaskForm):
    nama_client = StringField('Nama Client', validators=[DataRequired()])
    alamat = StringField('Alamat', validators=[Optional()])
    no_hp = StringField('Nomor HP', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Simpan')
