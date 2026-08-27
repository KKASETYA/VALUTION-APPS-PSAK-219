import pandas as pd
import numpy as np
from main import PSAK219Engine, parse_excel_dataset # Sesuaikan dengan nama file utama Anda

def run_actuarial_validation(excel_path, sheet_name=2024):
    print(f"==================================================")
    print(f" MENJALANKAN VALIDASI ENGINE VS MACRO EXCEL")
    print(f" File: {excel_path} | Sheet: {sheet_name}")
    print(f"==================================================")

    # 1. Parse data menggunakan parser presisi yang sama
    df_raw, total_paid = parse_excel_dataset(excel_path, sheet_name=sheet_name)
    print(f"Total Karyawan dimuat: {len(df_raw)}")

    # Inisialisasi Engine Python (Gunakan asumsi standar makro, misal Gaji 8%, Pensiun 55)
    engine = PSAK219Engine(valuation_year=sheet_name, salary_increase=0.08, retirement_age=55, resign_rate=0.02)
    
    val_date_dt = pd.to_datetime(f"{sheet_name}-12-31")
    python_results = []

    for _, row in df_raw.iterrows():
        dob = pd.to_datetime(row.get("Tanggal Lahir"))
        doe = pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
        gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
        
        current_age = (val_date_dt - dob).days / 365.25
        past_service = (val_date_dt - doe).days / 365.25

        res = engine.calculate_puc(current_age, past_service, gross_salary)
        python_results.append({
            "NIK": row.get("NIK"),
            "Nama": row.get("Nama"),
            "Py_PBO": res['PBO'],
            "Py_CSC": res['CSC'],
            "Py_PVFB": res['PVFB'],
            "Py_Discount": res['Applied_Discount']
        })

    df_py_res = pd.DataFrame(python_results)
    
    # 2. Baca hasil dari Makro Excel (Asumsi sheet output makro bernama 'Output_Macro' atau kolom referensi di Excel)
    try:
        df_excel_macro = pd.read_excel(excel_path, sheet_name="Output_Macro") 
        print("✓ Berhasil memuat sheet pembanding Macro Excel.")
        
        # Gabungkan berdasarkan NIK untuk perbandingan selisih
        comparison = pd.merge(df_py_res, df_excel_macro, on="NIK", suffixes=('_Python', '_Macro'))
        
        # Hitung selisih PBO
        comparison['Diff_PBO'] = comparison['Py_PBO'] - comparison['PBO_Macro']
        comparison['Selisih_Persen_%'] = (comparison['Diff_PBO'] / comparison['PBO_Macro']) * 100

        print("\n--- HASIL ANALISIS SELISIH (VARIANCE) ---")
        print(comparison[['NIK', 'Nama', 'Py_PBO', 'PBO_Macro', 'Selisih_Persen_%']].head(10))
        
        max_diff = comparison['Diff_PBO'].abs().max()
        print(f"\nSelisih absolut maksimum antara Python dan Makro Excel: Rp {max_diff:,.2f}")
        
        if max_diff < 1.0:
            print("🎉 KECOCOKAN SEMPURNA! Engine Python menghasilkan angka yang identik dengan Makro Excel.")
        else:
            print("⚠️ Perhatian: Ada selisih. Periksa kembali asumsi kurva diskonto atau formula pembulatan di makro VBA.")

    except Exception as e:
        print(f"\nCatatan: Sheet pembanding 'Output_Macro' belum ada di Excel Anda ({e}).")
        print("Berikut adalah ringkasan hasil kalkulasi Engine Python:")
        print(df_py_res.head(10))

if __name__ == "__main__":
    # Ganti dengan path file Excel uji Anda
    run_actuarial_validation("data_klien_contoh.xlsx", sheet_name=2024)
