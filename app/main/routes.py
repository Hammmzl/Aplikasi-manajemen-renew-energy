from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response, Response, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, WasteOilPurchase, SuratJalan, SuratJalanDetail, Client
from app.extensions import db, login_manager
from app.models import WasteOilPurchase
from datetime import datetime
import io 
import pandas as pd
from weasyprint import HTML
from .forms import WasteOilPurchaseForm
from sqlalchemy import extract, func
import calendar
from app.main.utils import generate_monthly_purchase_dataframe
from io import BytesIO
from app.main.forms import SuratJalanForm, SuratJalanDetailForm
from dateutil.relativedelta import relativedelta



main_bp = Blueprint('main', __name__, template_folder='templates/volt_dashboard')


@main_bp.route('/')
@login_required
def index():
    # Ambil parameter filter dan pagination dari query string
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '').strip()

    # Mulai query dasar
    query = WasteOilPurchase.query

    # Filter nama pengepul kalau ada input search
    if search_query:
        query = query.filter(WasteOilPurchase.nama_pengepul.ilike(f'%{search_query}%'))

    # Filter tanggal pembelian kalau ada input date
    if date_filter:
        query = query.filter(WasteOilPurchase.tanggal_pembelian == date_filter)

    # Paginate hasil query
    pagination = query.order_by(WasteOilPurchase.tanggal_pembelian.desc()).paginate(page=page, per_page=per_page, error_out=False)
    purchases = pagination.items

    return render_template('volt_dashboard/index.html',
                           purchases=purchases,
                           page=page,
                           total_pages=pagination.pages,
                           total_data=pagination.total,
                           search_query=search_query,
                           date_filter=date_filter)



@main_bp.route('/tambah_pembelian', methods=['GET', 'POST'])
def tambah_pembelian():
    form = WasteOilPurchaseForm()
    form.client_id.choices = [(client.id, client.nama_client) for client in Client.query.all()]

    if form.validate_on_submit():
        pembelian = WasteOilPurchase(
            client_id=form.client_id.data,
            tanggal_pembelian=form.tanggal_pembelian.data,
            jumlah=form.jumlah.data,
            harga_per_liter=form.harga_per_liter.data,
            total_harga=form.jumlah.data * form.harga_per_liter.data,
            user_id=current_user.id  # kalau kamu pakai flask-login
        )
        db.session.add(pembelian)
        db.session.commit()
        flash('Data pembelian berhasil ditambahkan.', 'success')
        return redirect(url_for('main.index'))

    return render_template('volt_dashboard/tambah.html', form=form)


@main_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    purchase = WasteOilPurchase.query.get_or_404(id)
    form = WasteOilPurchaseForm()

    # isi pilihan client
    form.client_id.choices = [(client.id, client.nama_client) for client in Client.query.all()]

    if form.validate_on_submit():
        purchase.client_id = form.client_id.data
        purchase.tanggal_pembelian = form.tanggal_pembelian.data
        purchase.jumlah = float(form.jumlah.data)
        purchase.harga_per_liter = float(form.harga_per_liter.data)
        purchase.total_harga = purchase.jumlah * purchase.harga_per_liter
        db.session.commit()
        flash('Data pembelian berhasil diperbarui', 'success')
        return redirect(url_for('main.index'))

    # isi data lama ke form waktu GET
    form.client_id.data = purchase.client_id
    form.tanggal_pembelian.data = purchase.tanggal_pembelian
    form.jumlah.data = purchase.jumlah
    form.harga_per_liter.data = purchase.harga_per_liter

    return render_template('volt_dashboard/edit.html', form=form, purchase=purchase)



# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





@main_bp.route('/hapus/<int:id>', methods=['POST'])
def hapus(id):
    purchase = WasteOilPurchase.query.get_or_404(id)
    db.session.delete(purchase)
    db.session.commit()
    flash('Data berhasil dihapus', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/export_excel')
def export_excel():
    purchases = WasteOilPurchase.query.order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    data = []
    for p in purchases:
        data.append({
            'Nama Pengepul': p.client.nama_client if p.client else '-', 
            'Tanggal Pembelian': p.tanggal_pembelian.strftime('%d-%m-%Y'),
            'Jumlah (Liter)': p.jumlah,
            'Harga per Liter (Rp)': p.harga_per_liter,
            'Total Harga (Rp)': p.jumlah * p.harga_per_liter
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pembelian Minyak Jelantah')

    output.seek(0)

    return send_file(output, download_name='pembelian_minyak_jelantah.xlsx', as_attachment=True)


@main_bp.route('/cetak_pdf')
def cetak_pdf():
    search_query = request.args.get('search', '', type=str)
    date_filter = request.args.get('date', '', type=str)

    query = WasteOilPurchase.query
    if search_query:
        query = query.filter(WasteOilPurchase.nama_pengepul.ilike(f'%{search_query}%'))
    if date_filter:
        query = query.filter(WasteOilPurchase.tanggal_pembelian == date_filter)

    purchases = query.order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    rendered = render_template('volt_dashboard/pdf_template.html',
                               purchases=purchases,
                               generated_at=datetime.now().strftime('%d-%m-%Y %H:%M:%S'))

    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=pembelian_minyak_jelantah.pdf'
    return response




@main_bp.route('/data-bulanan')
@login_required
def data_bulanan():
    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year
    nama_bulan = calendar.month_name[bulan_ini]

    data_bulanan = WasteOilPurchase.query.filter(
        extract('month', WasteOilPurchase.tanggal_pembelian) == bulan_ini,
        extract('year', WasteOilPurchase.tanggal_pembelian) == tahun_ini
    ).order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    return render_template('volt_dashboard/data_bulanan.html', data=data_bulanan,nama_bulan=nama_bulan,
        tahun_ini=tahun_ini)


@main_bp.route('/export_excel_bulanan')
@login_required
def export_excel_bulanan():
    from datetime import datetime, date, timedelta

    # Hitung awal dan akhir bulan sekarang
    today = date.today()
    awal_bulan = today.replace(day=1)
    if today.month == 12:
        akhir_bulan = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        akhir_bulan = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Ambil data pembelian bulan ini
    purchases = WasteOilPurchase.query\
        .filter(WasteOilPurchase.tanggal_pembelian >= awal_bulan)\
        .filter(WasteOilPurchase.tanggal_pembelian <= akhir_bulan)\
        .order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    # Siapkan data buat ke DataFrame
    data = []
    for p in purchases:
        data.append({
            'Nama Pengepul': p.client.nama_client if p.client else '-',
            'Tanggal Pembelian': p.tanggal_pembelian.strftime('%d-%m-%Y'),
            'Jumlah (Liter)': p.jumlah,
            'Harga per Liter (Rp)': p.harga_per_liter,
            'Total Harga (Rp)': p.jumlah * p.harga_per_liter
        })

    # Convert ke DataFrame
    df = pd.DataFrame(data)

    # Simpan ke file Excel di memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pembelian Bulanan')
    output.seek(0)

    # Format nama file pakai bulan dan tahun sekarang
    bulan_ini_str = datetime.now().strftime('%B %Y')
    nama_file = f"Data Pembelian {bulan_ini_str}.xlsx"

    # Buat response buat download
    return send_file(output,
                     download_name=nama_file,
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@main_bp.route('/export-pdf-bulanan')
@login_required
def export_pdf_bulanan():
    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year
    data = WasteOilPurchase.query.filter(
        db.extract('month', WasteOilPurchase.tanggal_pembelian) == bulan_ini,
        db.extract('year', WasteOilPurchase.tanggal_pembelian) == tahun_ini
    ).all()

    total_harga = sum([d.total_harga for d in data])

    # Render template HTML
    rendered = render_template(
        'volt_dashboard/pdf_template_bulanan.html',
        data=data,
        total_harga=total_harga,
        bulan=datetime.now().strftime("%B %Y")
    )

    # Convert ke PDF via WeasyPrint
    pdf_file = io.BytesIO()
    HTML(string=rendered).write_pdf(pdf_file)
    pdf_file.seek(0)

    # Buat nama file
    filename = f"Data_Pembelian_{datetime.now().strftime('%B_%Y')}.pdf"

    # Kirim response
    response = make_response(pdf_file.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@main_bp.route('/surat-jalan')
def list_surat_jalan():
    surat_list = SuratJalan.query.order_by(SuratJalan.tanggal.desc()).all()
    return render_template('volt_dashboard/surat_jalan/list.html', surat_list=surat_list)


@main_bp.route('/surat-jalan/tambah', methods=['GET', 'POST'])
def tambah_surat_jalan():
    form = SuratJalanForm()
    if form.validate_on_submit():
        surat_jalan = SuratJalan(
            nomor=form.nomor.data,
            tanggal=form.tanggal.data,
            no_kendaraan=form.no_kendaraan.data,
            tujuan=form.tujuan.data,
            owner=form.owner.data,
            supir=form.supir.data,
            penerima=form.penerima.data
        )
        db.session.add(surat_jalan)
        db.session.commit()
        print('ID Surat Jalan:', surat_jalan.id)  # debug id muncul gak?
        flash('Surat Jalan berhasil disimpan!', 'success')
        return redirect(url_for('main.tambah_detail_barang', surat_jalan_id=surat_jalan.id))
    else:
        if request.method == 'POST':
            print("Form NOT valid")
            print(form.errors)
    return render_template('volt_dashboard/surat_jalan/tambah.html', form=form)

    

@main_bp.route('/surat-jalan/<int:surat_jalan_id>/tambah_detail', methods=['GET', 'POST'])
def tambah_detail_barang(surat_jalan_id):
    surat_jalan = SuratJalan.query.get_or_404(surat_jalan_id)
    form = SuratJalanDetailForm()
    details = SuratJalanDetail.query.filter_by(surat_jalan_id=surat_jalan_id).all()  # ⬅️ ini

    if form.validate_on_submit():
        detail = SuratJalanDetail(
            surat_jalan_id=surat_jalan_id,
            nama_barang=form.nama_barang.data,
            jumlah=form.jumlah.data,
            keterangan=form.keterangan.data
        )
        db.session.add(detail)
        db.session.commit()
        flash('Detail barang berhasil ditambahkan!', 'success')
        return redirect(url_for('main.tambah_detail_barang', surat_jalan_id=surat_jalan_id))

    return render_template(
        'volt_dashboard/surat_jalan/tambah_detail.html',
        form=form,
        surat_jalan=surat_jalan,
        details=details 
    )


@main_bp.route('/surat_jalan/<int:surat_jalan_id>/hapus_detail/<int:detail_id>', methods=['POST', 'GET'])
def hapus_detail(surat_jalan_id, detail_id):
    detail = SuratJalanDetail.query.get_or_404(detail_id)
    db.session.delete(detail)
    db.session.commit()
    flash('Detail barang berhasil dihapus.', 'success')
    return redirect(url_for('main.tambah_detail_barang', surat_jalan_id=surat_jalan_id))

@main_bp.route('/surat-jalan/<int:surat_jalan_id>')
def detail_surat_jalan(surat_jalan_id):
    surat_jalan = SuratJalan.query.get(surat_jalan_id)
    if not surat_jalan:
        abort(404)
    return render_template('volt_dashboard/surat_jalan/detail.html', surat_jalan=surat_jalan)

@main_bp.route('/surat-jalan/<int:surat_jalan_id>/print')
def print_surat_jalan(surat_jalan_id):
    surat_jalan = SuratJalan.query.get_or_404(surat_jalan_id)

    # Render template ke HTML string
    rendered = render_template('volt_dashboard/surat_jalan/print.html', surat_jalan=surat_jalan)

    # Generate PDF dari HTML
    pdf = HTML(string=rendered, base_url=request.base_url).write_pdf()

    # Buat response PDF
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"SuratJalan_{surat_jalan.nomor}.pdf"
    response.headers['Content-Disposition'] = f'inline; filename={filename}'

    return response



@main_bp.route('/dashboard')
@login_required
def dashboard():
    now = datetime.now()
    bulan_ini = now.month
    tahun_ini = now.year

    bulan_lalu = now - relativedelta(months=1)
    bulan_lalu_num = bulan_lalu.month
    tahun_lalu = bulan_lalu.year

    # Total clients sekarang dan bulan lalu
    total_clients_now = Client.query.count()
    # Misal kamu simpan tanggal daftar client di model Client dengan kolom created_at,
    # kalau gak ada, kamu bisa hitung jumlah clients baru bulan ini
    clients_bulan_ini = Client.query.filter(
        func.extract('month', Client.created_at) == bulan_ini,
        func.extract('year', Client.created_at) == tahun_ini
    ).count()
    clients_bulan_lalu = Client.query.filter(
        func.extract('month', Client.created_at) == bulan_lalu_num,
        func.extract('year', Client.created_at) == tahun_lalu
    ).count()
    # Persentase perubahan clients baru bulan ini dibanding bulan lalu
    if clients_bulan_lalu == 0:
        persentase_clients = 100 if clients_bulan_ini > 0 else 0
    else:
        persentase_clients = round((clients_bulan_ini - clients_bulan_lalu) / clients_bulan_lalu * 100, 2)

    # Total keuntungan bulan ini dan bulan lalu
    total_profit_now = db.session.query(
        func.sum(WasteOilPurchase.jumlah * WasteOilPurchase.harga_per_liter)
    ).filter(
        func.extract('month', WasteOilPurchase.tanggal_pembelian) == bulan_ini,
        func.extract('year', WasteOilPurchase.tanggal_pembelian) == tahun_ini
    ).scalar() or 0

    total_profit_lalu = db.session.query(
        func.sum(WasteOilPurchase.jumlah * WasteOilPurchase.harga_per_liter)
    ).filter(
        func.extract('month', WasteOilPurchase.tanggal_pembelian) == bulan_lalu_num,
        func.extract('year', WasteOilPurchase.tanggal_pembelian) == tahun_lalu
    ).scalar() or 0

    if total_profit_lalu == 0:
        persentase_keuntungan = 100 if total_profit_now > 0 else 0
    else:
        persentase_keuntungan = round((total_profit_now - total_profit_lalu) / total_profit_lalu * 100, 2)

    return render_template('volt_dashboard/dashboard.html',
                           total_clients=total_clients_now,
                           persentase_clients=persentase_clients,
                           total_profit=total_profit_now,
                           persentase_keuntungan=persentase_keuntungan)