import calendar
import io
from datetime import datetime
from io import BytesIO

import pandas as pd
from flask import abort, flash, make_response, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from weasyprint import HTML

from app.extensions import db
from app.main import main_bp
from app.main.forms import OtherTransactionForm, SuratJalanDetailForm, SuratJalanForm, WasteOilPurchaseForm
from app.main.utils import build_month_window, format_quantity
from app.models import Client, HargaModalBulanan, OtherTransaction, SuratJalan, SuratJalanDetail, WasteOilPurchase


def _apply_purchase_filters(query, search_query='', date_filter=''):
    if search_query:
        query = query.join(Client).filter(Client.nama_client.ilike(f'%{search_query}%'))

    if date_filter:
        try:
            selected_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            selected_date = None

        if selected_date:
            query = query.filter(WasteOilPurchase.tanggal_pembelian == selected_date)

    return query


def _normalize_year_month(value):
    if not value:
        return datetime.now().strftime('%Y-%m')

    try:
        datetime.strptime(value, '%Y-%m')
        return value
    except ValueError:
        return datetime.now().strftime('%Y-%m')


@main_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_query = request.args.get('search', '').strip()
    date_filter = request.args.get('date', '').strip()

    query = WasteOilPurchase.query.filter_by(is_closed=False)
    query = _apply_purchase_filters(query, search_query=search_query, date_filter=date_filter)

    pagination = query.order_by(WasteOilPurchase.tanggal_pembelian.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )
    purchases = pagination.items

    return render_template(
        'volt_dashboard/index.html',
        purchases=purchases,
        page=page,
        total_pages=pagination.pages,
        total_data=pagination.total,
        search_query=search_query,
        date_filter=date_filter,
    )


@main_bp.route('/tambah_pembelian', methods=['GET', 'POST'])
@login_required
def tambah_pembelian():
    form = WasteOilPurchaseForm()
    form.client_id.choices = [(client.id, client.nama_client) for client in Client.query.order_by(Client.nama_client).all()]

    if form.validate_on_submit():
        pembelian = WasteOilPurchase(
            client_id=form.client_id.data,
            tanggal_pembelian=form.tanggal_pembelian.data,
            jumlah=form.jumlah.data,
            harga_per_liter=form.harga_per_liter.data,
            total_harga=0,
            user_id=current_user.id,
        )
        pembelian.calculate_total()
        db.session.add(pembelian)
        db.session.commit()
        flash('Data pembelian berhasil ditambahkan.', 'success')
        return redirect(url_for('main.index'))

    return render_template('volt_dashboard/tambah.html', form=form)


@main_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    purchase = WasteOilPurchase.query.get_or_404(id)
    form = WasteOilPurchaseForm()
    form.client_id.choices = [(client.id, client.nama_client) for client in Client.query.order_by(Client.nama_client).all()]

    if form.validate_on_submit():
        purchase.client_id = form.client_id.data
        purchase.tanggal_pembelian = form.tanggal_pembelian.data
        purchase.jumlah = float(form.jumlah.data)
        purchase.harga_per_liter = float(form.harga_per_liter.data)
        purchase.calculate_total()
        db.session.commit()
        flash('Data pembelian berhasil diperbarui', 'success')
        return redirect(url_for('main.index'))

    form.client_id.data = purchase.client_id
    form.tanggal_pembelian.data = purchase.tanggal_pembelian
    form.jumlah.data = purchase.jumlah
    form.harga_per_liter.data = purchase.harga_per_liter

    return render_template('volt_dashboard/edit.html', form=form, purchase=purchase)


@main_bp.route('/hapus/<int:id>', methods=['POST'])
@login_required
def hapus(id):
    purchase = WasteOilPurchase.query.get_or_404(id)
    db.session.delete(purchase)
    db.session.commit()
    flash('Data berhasil dihapus', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/export_excel')
@login_required
def export_excel():
    purchases = WasteOilPurchase.query.order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    data = []
    for purchase in purchases:
        data.append(
            {
                'Nama Pengepul': purchase.client.nama_client if purchase.client else '-',
                'Tanggal Pembelian': purchase.tanggal_pembelian.strftime('%d-%m-%Y'),
                'Jumlah (Liter)': purchase.jumlah,
                'Harga per Liter (Rp)': purchase.harga_per_liter,
                'Total Harga (Rp)': purchase.total_harga,
            }
        )

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pembelian Minyak Jelantah')

    output.seek(0)

    return send_file(output, download_name='pembelian_minyak_jelantah.xlsx', as_attachment=True)


@main_bp.route('/cetak_pdf')
@login_required
def cetak_pdf():
    search_query = request.args.get('search', '', type=str).strip()
    date_filter = request.args.get('date', '', type=str).strip()

    query = WasteOilPurchase.query
    query = _apply_purchase_filters(query, search_query=search_query, date_filter=date_filter)
    purchases = query.order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    rendered = render_template(
        'volt_dashboard/pdf_template.html',
        purchases=purchases,
        generated_at=datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
    )

    try:
        pdf = HTML(string=rendered).write_pdf()
    except Exception as e:
        flash(f'Gagal membuat PDF: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=pembelian_minyak_jelantah.pdf'
    return response


@main_bp.route('/data-all')
@login_required
def data_bulanan():
    from app.models import TutupBukuHistory
    riwayat = TutupBukuHistory.query.order_by(TutupBukuHistory.tanggal_tutup.desc()).all()

    return render_template(
        'volt_dashboard/data_bulanan.html',
        riwayat=riwayat,
    )


@main_bp.route('/export_excel_laporan/<int:id>')
@login_required
def export_excel_laporan(id):
    from app.models import TutupBukuHistory
    history = TutupBukuHistory.query.get_or_404(id)
    purchases = WasteOilPurchase.query.filter_by(tutup_buku_id=id).order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    data = []
    for i, purchase in enumerate(purchases, 1):
        data.append(
            {
                'No': i,
                'Nama Pengepul': purchase.client.nama_client if purchase.client else '-',
                'Tanggal Pembelian': purchase.tanggal_pembelian.strftime('%d %b %Y'),
                'Jumlah (Liter)': float(purchase.jumlah),
                'Harga per Liter (Rp)': float(purchase.harga_per_liter),
                'Total Harga (Rp)': float(purchase.total_harga),
            }
        )

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan Keuangan', startrow=4)
        workbook  = writer.book
        worksheet = writer.sheets['Laporan Keuangan']

        title_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        subtitle_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#1F2937', 'font_color': 'white', 'border': 1, 'align': 'center'})
        money_format = workbook.add_format({'num_format': 'Rp #,##0', 'border': 1})
        float_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'align': 'center'})
        border_format = workbook.add_format({'border': 1})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})

        worksheet.merge_range('A1:F2', 'LAPORAN REKAPITULASI PEMBELIAN MINYAK JELANTAH', title_format)
        worksheet.merge_range('A3:F3', f'Periode Keuangan: Laporan {history.nama_periode}', subtitle_format)

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(4, col_num, value, header_format)

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 22)
        worksheet.set_column('F:F', 22)

        for row_num in range(5, 5 + len(df)):
            worksheet.write(row_num, 0, df.iloc[row_num-5, 0], center_format)
            worksheet.write(row_num, 1, df.iloc[row_num-5, 1], border_format)
            worksheet.write(row_num, 2, df.iloc[row_num-5, 2], center_format)
            worksheet.write(row_num, 3, df.iloc[row_num-5, 3], float_format)
            worksheet.write(row_num, 4, df.iloc[row_num-5, 4], money_format)
            worksheet.write(row_num, 5, df.iloc[row_num-5, 5], money_format)

    output.seek(0)
    nama_file = f'Laporan_{history.nama_periode.replace(" ", "_")}.xlsx'

    return send_file(
        output,
        download_name=nama_file,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@main_bp.route('/export_pdf_laporan/<int:id>')
@login_required
def export_pdf_laporan(id):
    from app.models import TutupBukuHistory
    history = TutupBukuHistory.query.get_or_404(id)
    data = WasteOilPurchase.query.filter_by(tutup_buku_id=id).order_by(WasteOilPurchase.tanggal_pembelian.desc()).all()

    total_harga = sum((item.total_harga or 0) for item in data)

    rendered = render_template(
        'volt_dashboard/pdf_template_bulanan.html',
        data=data,
        total_harga=total_harga,
        bulan=history.nama_periode,
    )

    try:
        pdf_file = io.BytesIO()
        HTML(string=rendered).write_pdf(pdf_file)
        pdf_file.seek(0)
    except Exception as e:
        flash(f'Gagal membuat PDF: {str(e)}', 'danger')
        return redirect(url_for('main.data_bulanan'))

    filename = f'Laporan_{history.nama_periode.replace(" ", "_")}.pdf'

    response = make_response(pdf_file.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@main_bp.route('/surat-jalan')
@login_required
def list_surat_jalan():
    surat_list = SuratJalan.query.order_by(SuratJalan.tanggal.desc()).all()
    return render_template('volt_dashboard/surat_jalan/list.html', surat_list=surat_list)


@main_bp.route('/surat-jalan/tambah', methods=['GET', 'POST'])
@login_required
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
            penerima=form.penerima.data,
        )
        db.session.add(surat_jalan)
        db.session.commit()
        flash('Surat Jalan berhasil disimpan!', 'success')
        return redirect(url_for('main.tambah_detail_barang', surat_jalan_id=surat_jalan.id))

    return render_template('volt_dashboard/surat_jalan/tambah.html', form=form)


@main_bp.route('/surat-jalan/<int:surat_jalan_id>/tambah_detail', methods=['GET', 'POST'])
@login_required
def tambah_detail_barang(surat_jalan_id):
    surat_jalan = SuratJalan.query.get_or_404(surat_jalan_id)
    form = SuratJalanDetailForm()
    details = SuratJalanDetail.query.filter_by(surat_jalan_id=surat_jalan_id).all()

    if form.validate_on_submit():
        detail = SuratJalanDetail(
            surat_jalan_id=surat_jalan_id,
            nama_barang=form.nama_barang.data,
            jumlah=form.jumlah.data,
            keterangan=form.keterangan.data,
        )
        db.session.add(detail)
        db.session.commit()
        flash('Detail barang berhasil ditambahkan!', 'success')
        return redirect(url_for('main.tambah_detail_barang', surat_jalan_id=surat_jalan_id))

    return render_template(
        'volt_dashboard/surat_jalan/tambah_detail.html',
        form=form,
        surat_jalan=surat_jalan,
        details=details,
    )


@main_bp.route('/surat-jalan/<int:surat_jalan_id>/hapus-detail/<int:detail_id>', methods=['POST'])
@login_required
def hapus_detail(surat_jalan_id, detail_id):
    detail = SuratJalanDetail.query.get_or_404(detail_id)
    db.session.delete(detail)
    db.session.commit()
    flash('Detail barang berhasil dihapus.', 'success')
    return redirect(url_for('main.tambah_detail_barang', surat_jalan_id=surat_jalan_id))


@main_bp.route('/surat-jalan/<int:surat_jalan_id>')
@login_required
def detail_surat_jalan(surat_jalan_id):
    surat_jalan = SuratJalan.query.get(surat_jalan_id)
    if not surat_jalan:
        abort(404)
    return render_template('volt_dashboard/surat_jalan/detail.html', surat_jalan=surat_jalan)


@main_bp.route('/surat-jalan/<int:surat_jalan_id>/print')
@login_required
def print_surat_jalan(surat_jalan_id):
    surat_jalan = SuratJalan.query.get_or_404(surat_jalan_id)

    rendered = render_template('volt_dashboard/surat_jalan/print.html', surat_jalan=surat_jalan)

    try:
        pdf = HTML(string=rendered, base_url=request.base_url).write_pdf()
    except Exception as e:
        flash(f'Gagal membuat PDF: {str(e)}', 'danger')
        return redirect(url_for('main.list_surat_jalan'))

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f'SuratJalan_{surat_jalan.nomor}.pdf'
    response.headers['Content-Disposition'] = f'inline; filename={filename}'

    return response


@main_bp.route('/pengeluaran')
@login_required
def pengeluaran_index():
    transaksi = OtherTransaction.query.filter_by(is_closed=False).order_by(OtherTransaction.tanggal.desc()).all()
    return render_template('volt_dashboard/other_transaction/index.html', transaksi=transaksi)


@main_bp.route('/pengeluaran-lainnya/tambah', methods=['GET', 'POST'])
@login_required
def pengeluaran_tambah():
    form = OtherTransactionForm()
    if form.validate_on_submit():
        transaksi = OtherTransaction(
            tanggal=form.tanggal.data,
            keterangan=form.keterangan.data,
            pemasukan=form.pemasukan.data or 0,
            pengeluaran=form.pengeluaran.data or 0,
            metode_pembayaran=form.metode_pembayaran.data,
        )
        db.session.add(transaksi)
        db.session.commit()
        flash('Data pengeluaran lainnya berhasil ditambahkan.', 'success')
        return redirect(url_for('main.pengeluaran_index'))
    return render_template('volt_dashboard/other_transaction/pengeluaran_tambah.html', form=form, title='Tambah Pengeluaran Lainnya')


@main_bp.route('/pengeluaran-lainnya/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def pengeluaran_edit(id):
    transaksi = OtherTransaction.query.get_or_404(id)
    form = OtherTransactionForm(obj=transaksi)
    if form.validate_on_submit():
        transaksi.tanggal = form.tanggal.data
        transaksi.keterangan = form.keterangan.data
        transaksi.pemasukan = form.pemasukan.data or 0
        transaksi.pengeluaran = form.pengeluaran.data or 0
        transaksi.metode_pembayaran = form.metode_pembayaran.data
        db.session.commit()
        flash('Data pengeluaran lainnya berhasil diperbarui.', 'success')
        return redirect(url_for('main.pengeluaran_index'))
    return render_template('volt_dashboard/other_transaction/edit.html', form=form)


@main_bp.route('/pengeluaran-lainnya/hapus/<int:id>', methods=['POST'])
@login_required
def pengeluaran_hapus(id):
    transaksi = OtherTransaction.query.get_or_404(id)
    db.session.delete(transaksi)
    db.session.commit()
    flash('Data pengeluaran lainnya berhasil dihapus.', 'success')
    return redirect(url_for('main.pengeluaran_index'))


@main_bp.route('/tutup-buku', methods=['POST'])
@login_required
def tutup_buku():
    from app.models import TutupBukuHistory
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    now = datetime.now()
    base_name = f"{months[now.month-1]} {now.year}"
    
    existing_count = TutupBukuHistory.query.filter(TutupBukuHistory.nama_periode.like(f"{base_name}%")).count()
    if existing_count > 0:
        nama_periode = f"{base_name} ({existing_count + 1})"
    else:
        nama_periode = base_name

    history = TutupBukuHistory(nama_periode=nama_periode)
    db.session.add(history)
    db.session.flush()

    WasteOilPurchase.query.filter_by(is_closed=False).update(dict(is_closed=True, tutup_buku_id=history.id))
    OtherTransaction.query.filter_by(is_closed=False).update(dict(is_closed=True, tutup_buku_id=history.id))
    db.session.commit()
    flash(f'Buku keuangan berhasil ditutup sebagai laporan "{nama_periode}".', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    harga_modal_entry = HargaModalBulanan.query.filter_by(bulan='current').first()
    harga_modal = harga_modal_entry.harga_modal if harga_modal_entry else 0

    purchases = WasteOilPurchase.query.filter_by(is_closed=False).all()
    total_quantity = sum((purchase.jumlah or 0) for purchase in purchases)
    total_harga_beli = sum((purchase.total_harga or 0) for purchase in purchases)

    pengeluaran_lain = db.session.query(
        db.func.sum(OtherTransaction.pengeluaran)
    ).filter_by(is_closed=False).scalar() or 0

    harga_modal = float(harga_modal)
    total_quantity = float(total_quantity)
    total_harga_beli = float(total_harga_beli)
    pengeluaran_lain = float(pengeluaran_lain)

    total_pengeluaran = total_harga_beli + pengeluaran_lain
    laba_bersih = (harga_modal * total_quantity) - total_pengeluaran
    total_clients = Client.query.count()

    return render_template(
        'volt_dashboard/dashboard.html',
        total_clients=total_clients,
        total_profit=laba_bersih,
        total_quantity=total_quantity,
        total_quantity_display=format_quantity(total_quantity),
        total_pengeluaran=total_pengeluaran,
        harga_modal=harga_modal,
        persentase_clients=0,
    )


@main_bp.route('/harga-modal', methods=['POST'])
@login_required
def input_harga_modal():
    try:
        harga_modal = float(request.form['harga_modal'])
    except (KeyError, ValueError):
        flash('Harga jual tidak valid.', 'danger')
        return redirect(url_for('main.dashboard'))

    existing = HargaModalBulanan.query.filter_by(bulan='current').first()

    if existing:
        existing.harga_modal = harga_modal
        existing.created_at = datetime.now()
        flash('Harga jual saat ini berhasil diperbarui.', 'success')
    else:
        new_modal = HargaModalBulanan(
            bulan='current',
            harga_modal=harga_modal,
            created_at=datetime.now(),
        )
        db.session.add(new_modal)
        flash('Harga jual saat ini berhasil ditambahkan.', 'success')

    db.session.commit()

    return redirect(url_for('main.dashboard'))
