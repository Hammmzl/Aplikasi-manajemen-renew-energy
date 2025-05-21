from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response, Response, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import User, WasteOilPurchase
from app.extensions import db, login_manager
from app.models import WasteOilPurchase
from datetime import datetime
import io 
import pandas as pd
from weasyprint import HTML
from .forms import WasteOilPurchaseForm
from sqlalchemy import extract
import calendar
from app.main.utils import generate_monthly_purchase_dataframe
from io import BytesIO
from app.main.forms import SuratJalanForm, SuratJalanDetailForm
from app.models import SuratJalan, SuratJalanDetail


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

@main_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        print("Form manual valid, mulai simpan data...")
        try:
            nama_pengepul = request.form['nama_pengepul']
            tanggal_pembelian = datetime.strptime(request.form['tanggal_pembelian'], '%Y-%m-%d')
            jumlah = float(request.form['jumlah'])
            harga_per_liter = float(request.form['harga_per_liter'])
            total_harga = jumlah * harga_per_liter

            purchase = WasteOilPurchase(
                nama_pengepul=nama_pengepul,
                tanggal_pembelian=tanggal_pembelian,
                jumlah=jumlah,
                harga_per_liter=harga_per_liter,
                total_harga=total_harga,
                created_at=datetime.utcnow(),
                user_id=current_user.id
            )
            db.session.add(purchase)
            db.session.commit()
            flash('Data pembelian berhasil disimpan.', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            print("Gagal commit ke database:", e)
            flash('Terjadi kesalahan saat menyimpan data.', 'danger')

    return render_template('volt_dashboard/tambah.html')


@main_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    purchase = WasteOilPurchase.query.get_or_404(id)

    if request.method == 'POST':
        nama_pengepul = request.form['nama_pengepul']
        tanggal_pembelian = request.form['tanggal_pembelian']
        jumlah = request.form['jumlah']
        harga_per_liter = request.form['harga_per_liter']

        try:
            tanggal_obj = datetime.strptime(tanggal_pembelian, '%Y-%m-%d').date()
            jumlah_float = float(jumlah)
            harga_float = float(harga_per_liter)
        except Exception:
            flash('Input tidak valid, silakan coba lagi.', 'danger')
            return redirect(url_for('main.edit', id=id))

        purchase.nama_pengepul = nama_pengepul
        purchase.tanggal_pembelian = tanggal_obj
        purchase.jumlah = jumlah_float
        purchase.harga_per_liter = harga_float
        db.session.commit()
        flash('Data pembelian berhasil diperbarui', 'success')
        return redirect(url_for('main.index'))

    return render_template('volt_dashboard/edit.html', purchase=purchase)


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
            'Nama Pengepul': p.nama_pengepul,
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


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('volt_dashboard/dashboard.html')

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
    
    df = generate_monthly_purchase_dataframe()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pembelian Bulanan')
    output.seek(0)
    bulan_ini = datetime.now()
    nama_file = f"Data Pembelian {bulan_ini.strftime('%B %Y')}.xlsx"
    response = make_response(output.read())
    response.headers['Content-Disposition'] = f'attachment; filename={nama_file}'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response


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
