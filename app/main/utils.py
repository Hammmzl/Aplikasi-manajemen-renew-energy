from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from app.models import WasteOilPurchase
from app.extensions import db


def build_month_window(year_month=None):
    if year_month:
        month_start = datetime.strptime(year_month, '%Y-%m').date().replace(day=1)
    else:
        today = date.today()
        month_start = today.replace(day=1)

    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    return month_start, next_month


def format_quantity(value):
    quantity = Decimal(str(value or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    text = format(quantity, '.2f')
    return text.rstrip('0').rstrip('.')


def generate_monthly_purchase_dataframe(year_month=None):
    """Generate DataFrame pembelian bulan berjalan + total harga."""
    month_start, next_month = build_month_window(year_month)
    data = WasteOilPurchase.query.filter(
        WasteOilPurchase.tanggal_pembelian >= month_start,
        WasteOilPurchase.tanggal_pembelian < next_month,
    ).all()

    if data:
        data_dict = [{
            'Nama Pengepul': d.client.nama_client if d.client else '-',
            'Tanggal': d.tanggal_pembelian.strftime('%Y-%m-%d'),
            'Jumlah (L)': d.jumlah,
            'Harga/Liter': d.harga_per_liter,
            'Total Harga': d.total_harga
        } for d in data]

        df = pd.DataFrame(data_dict)

        total_harga_keseluruhan = sum(d.total_harga for d in data)

        total_row = {
            'Nama Pengepul': 'TOTAL',
            'Tanggal': '',
            'Jumlah (L)': '',
            'Harga/Liter': '',
            'Total Harga': total_harga_keseluruhan
        }

        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

    else:
        df = pd.DataFrame(columns=['Nama Pengepul', 'Tanggal', 'Jumlah (L)', 'Harga/Liter', 'Total Harga'])

    return df
