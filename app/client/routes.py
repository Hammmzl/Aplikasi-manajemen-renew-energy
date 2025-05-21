from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db
from app.models import Client
from app.client.forms import ClientForm

client_bp = Blueprint('client', __name__, url_prefix='/client')



@client_bp.route('/clients')
def client_index():
    clients = Client.query.all()
    return render_template('volt_dashboard/client/client_index.html', clients=clients)

@client_bp.route('/clients/tambah', methods=['GET', 'POST'])
def client_tambah():
    form = ClientForm()
    if form.validate_on_submit():
        new_client = Client(
            nama_client=form.nama_client.data,
            alamat=form.alamat.data,
            no_hp=form.no_hp.data,
            email=form.email.data
        )
        db.session.add(new_client)
        db.session.commit()
        flash('Data client berhasil ditambahkan!', 'success')
        return redirect(url_for('client.client_index'))
    return render_template('volt_dashboard/client/client_tambah.html', form=form)

@client_bp.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
def client_edit(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        client.nama_client = form.nama_client.data
        client.alamat = form.alamat.data
        client.no_hp = form.no_hp.data
        client.email = form.email.data
        db.session.commit()
        flash('Data client berhasil diperbarui!', 'success')
        return redirect(url_for('client.client_index'))
    return render_template('volt_dashboard/client/client_edit.html', form=form, client=client)

@client_bp.route('/clients/hapus/<int:id>', methods=['POST'])
def client_hapus(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Data client berhasil dihapus!', 'success')
    return redirect(url_for('client.client_index'))
