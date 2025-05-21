from io import BytesIO
from datetime import datetime
import pandas as pd
from app.models import WasteOilPurchase
from app.extensions import db

def generate_monthly_purchase_dataframe():
    """Generate DataFrame pembelian bulan berjalan + total harga."""
    data = WasteOilPurchase.query.filter(
        db.extract('month', WasteOilPurchase.tanggal_pembelian) == datetime.now().month,
        db.extract('year', WasteOilPurchase.tanggal_pembelian) == datetime.now().year
    ).all()

    if data:
        data_dict = [{
            'Nama Pengepul': d.nama_pengepul,
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
