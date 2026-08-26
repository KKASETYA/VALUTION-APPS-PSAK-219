import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# ==========================================
# 1. DATABASE KURVA YIELD PHEI (2022 - 2025)
# ==========================================
MULTI_YEAR_PHEI_CURVE = {
    2022: {
        0.1: 4.9631/100, 1: 5.5201/100, 2: 5.9315/100, 3: 6.2163/100, 4: 6.4225/100, 5: 6.5785/100,
        6: 6.7012/100, 7: 6.8004/100, 8: 6.8823/100, 9: 6.9505/100, 10: 7.0077/100, 11: 7.0555/100,
        12: 7.0955/100, 13: 7.1288/100, 14: 7.1563/100, 15: 7.1789/100, 16: 7.1974/100, 17: 7.2125/100,
        18: 7.2247/100, 19: 7.2345/100, 20: 7.2423/100, 21: 7.2486/100, 22: 7.2536/100, 23: 7.2575/100,
        24: 7.2606/100, 25: 7.2631/100, 26: 7.2650/100, 27: 7.2664/100, 28: 7.2676/100, 29: 7.2685/100, 30: 7.2692/100
    },
    2023: {
        0.1: 6.3389/100, 1: 6.3682/100, 2: 6.3972/100, 3: 6.4245/100, 4: 6.4507/100, 5: 6.4763/100,
        6: 6.5016/100, 7: 6.5265/100, 8: 6.5511/100, 9: 6.5753/100, 10: 6.5991/100, 11: 6.6223/100,
        12: 6.6447/100, 13: 6.6664/100, 14: 6.6872/100, 15: 6.7070/100, 16: 6.7259/100, 17: 6.7437/100,
        18: 6.7604/100, 19: 6.7762/100, 20: 6.7908/100, 21: 6.8045/100, 22: 6.8171/100, 23: 6.8288/100,
        24: 6.8396/100, 25: 6.8495/100, 26: 6.8586/100, 27: 6.8669/100, 28: 6.8745/100, 29: 6.8814/100, 30: 6.8877/100
    },
    2024: {
        0.1: 6.7160/100, 1: 6.8790/100, 2: 6.9495/100, 3: 6.9768/100, 4: 6.9912/100, 5: 7.0037/100,
        6: 7.0171/100, 7: 7.0312/100, 8: 7.0451/100, 9: 7.0580/100, 10: 7.0694/100, 11: 7.0789/100,
        12: 7.0867/100, 13: 7.0930/100, 14: 7.0978/100, 15: 7.1015/100, 16: 7.1043/100, 17: 7.1064/100,
        18: 7.1080/100, 19: 7.1091/100, 20: 7.1099/100, 21: 7.1105/100, 22: 7.1109/100, 23: 7.1112/100,
        24: 7.1114/100, 25: 7.1115/100, 26: 7.1116/100, 27: 7.1117/100, 28: 7.1118/100, 29: 7.1118/100, 30: 7.1118/100
    },
    2025: {
        0.1: 4.4836/100, 1: 4.8119/100, 2: 5.1003/100, 3: 5.3330/100, 4: 5.5227/100, 5: 5.6792/100,
        6: 5.8099/100, 7: 5.9204/100, 8: 6.0148/100, 9: 6.0963/100, 10: 6.1675/100, 11: 6.2300/100,
        12: 6.2854/100, 13: 6.3346/100, 14: 6.3787/100, 15: 6.4182/100, 16: 6.4536/100, 17: 6.4855/100,
        18: 6.5143/100, 19: 6.5402/100, 20: 6.5634/100, 21: 6.5844/100, 22: 6.6032/100, 23: 6.6201/100,
        24: 6.6352/100, 25: 6.6488/100, 26: 6.6609/100, 27: 6.6717/100, 28: 6.6813/100, 29: 6.6899/100, 30: 6.6975/100
    }
}

def get_individual_phei_rate(duration, valuation_year):
    if valuation_year not in MULTI_YEAR_PHEI_CURVE:
        valuation_year = max(MULTI_YEAR_PHEI_CURVE.keys()) if valuation_year > max(MULTI_YEAR_PHEI_CURVE.keys()) else min(MULTI_YEAR_PHEI_CURVE.keys())
    
    curve = MULTI_YEAR_PHEI_CURVE[valuation_year]
    dur_int = int(round(duration))

    if dur_int in curve: return curve[dur_int]
    elif dur_int < 1: return curve[0.1]
    elif dur_int > 30: return curve[30]
    else:
        lower = max([t for t in curve.keys() if t <= duration])
        upper = min([t for t in curve.keys() if t >= duration])
        if lower == upper: return curve[lower]
        return curve[lower] + (curve[upper] - curve[lower]) * (duration - lower) / (upper - lower)


# ==========================================
# FUNGSI BANTUAN & PARSER EXCEL
# ==========================================
def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    if decimals == 0:
        return f"{num:,.0f}".replace(",", ".")
    else:
        formatted = f"{num:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

def parse_excel_dataset(file_or_buffer, sheet_name=0):
    df = pd.read_excel(file_or_buffer, sheet_name=sheet_name, header=None)
    data_start_idx = 7
    for idx, val in enumerate(df.iloc[:, 0]):
        if isinstance(val, (int, float)) and val == 1:
            data_start_idx = idx
            break
            
    clean_data = []
    for idx in range(data_start_idx, len(df)):
        row = df.iloc[idx]
        nik = row.iloc[1]
        nama = row.iloc[2]
        dob = row.iloc[3]
        doe = row.iloc[4]
        salary = row.iloc[5]
        
        if pd.isna(nik) and pd.isna(nama): continue
            
        try: salary_val = float(salary) if not pd.isna(salary) else 0.0
        except: salary_val = 0.0
            
        clean_data.append({
            'NIK': str(nik).strip() if not pd.isna(nik) else '',
            'Nama': str(nama).strip() if not pd.isna(nama) else '',
            'Tanggal Lahir': dob,
            'Tgl. Mulai Bekerja': doe,
            'Total Upah Bulanan (Gross)': salary_val
        })
        
    return pd.DataFrame(clean_data)


# ==========================================
# 2. ENGINE AKTUARIA (DENGAN OUTPUT DETAIL)
# ==========================================
class PSAK219Engine:
    def __init__(self, valuation_year, salary_increase, retirement_age):
        self.val_year = valuation_year 
        self.salary_inc = salary_increase
        self.ret_age = retirement_age
        
    def get_benefit_pp35(self, service_years):
        if service_years < 1: up = 1
        elif service_years < 2: up = 2
        elif service_years < 3: up = 3
        elif service_years < 4: up = 4
        elif service_years < 5: up = 5
        elif service_years < 6: up = 6
        elif service_years < 7: up = 7
        elif service_years < 8: up = 8
        else: up = 9
            
        if service_years < 3: upmk = 0
        elif service_years < 6: upmk = 2
        elif service_years < 9: upmk = 3
        elif service_years < 12: upmk = 4
        elif service_years < 15: upmk = 5
        elif service_years < 18: upmk = 6
        elif service_years < 21: upmk = 7
        elif service_years < 24: upmk = 8
        else: upmk = 10
            
        return up, upmk

    def get_decrement_rates(self, age):
        q_mortality = 0.0005 * (1.09 ** (age - 20))
        q_disability = q_mortality * 0.10
        if age < 30: q_resign = 0.05
        elif age < 40: q_resign = 0.04
        elif age < 50: q_resign = 0.02
        elif age < 55: q_resign = 0.01
        else: q_resign = 0.00
        return q_mortality, q_disability, q_resign

    def calculate_puc(self, current_age, past_service, current_salary):
        years_to_retire = self.ret_age - current_age
        if pd.isna(current_age) or pd.isna(past_service) or pd.isna(current_salary) or years_to_retire <= 0:
            return {'Future Service': 0, 'Total Service': past_service, 'Applied_Discount': 0, 'PVFB': 0, 'PBO': 0, 'CSC': 0}
            
        discount_rate = get_individual_phei_rate(years_to_retire, self.val_year)
        total_service = past_service + years_to_retire
        pvfb_death, pvfb_disability = 0, 0
        p_survival = 1.0 
        
        for t in range(int(years_to_retire)):
            age_t = current_age + t
            service_t = past_service + t
            salary_t = current_salary * ((1 + self.salary_inc) ** t)
            q_m, q_d, q_w = self.get_decrement_rates(age_t)
            up_t, upmk_t = self.get_benefit_pp35(service_t)
            
            b_death = salary_t * ((2 * up_t) + upmk_t)
            b_disab = salary_t * ((2 * up_t) + upmk_t)
            v = 1 / ((1 + discount_rate) ** (t + 1))
            
            pvfb_death += b_death * v * (p_survival * q_m)
            pvfb_disability += b_disab * v * (p_survival * q_d)
            p_survival *= (1 - (q_m + q_d + q_w))
            
        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((1.75 * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + discount_rate) ** years_to_retire)
        pvfb_ret = b_ret * v_ret * p_survival
        
        total_pvfb = pvfb_death + pvfb_disability + pvfb_ret
        pbo = total_pvfb * (past_service / total_service)
        csc = total_pvfb / total_service
        
        return {
            'Future Service': years_to_retire,
            'Total Service': total_service,
            'Applied_Discount': discount_rate,
            'PVFB': total_pvfb,
            'PBO': pbo,
            'CSC': csc
        }


# ==========================================
# 3. GENERATOR PDF DETAIL (LANDSCAPE)
# ==========================================
def draw_footer_landscape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(36, 45, landscape(letter)[0] - 36, 45) # Disesuaikan lebar landscape
    
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(landscape(letter)[0]/2.0, 30, "Konsultan Aktuaria Setya Gunawan")
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(landscape(letter)[0]/2.0, 20, "Izin Perusahaan No. 4.21.0007 | Keputusan Menteri Keuangan RI No. 590/KM.1/2021 | AKAI - 21043")
    canvas.restoreState()

def generate_detailed_report(results_dict, salary_inc, ret_age, val_years, company_name, report_no):
    pdf_buffer = io.BytesIO()
    # Menggunakan orientasi LANDSCAPE agar tabel rinci muat
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=60)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=1, spaceBefore=10, spaceAfter=10)
    sub_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=11, textColor=colors.black, alignment=1, spaceAfter=20)
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceBefore=15, spaceAfter=10)
    
    sorted_years = sorted(val_years, reverse=True)
    
    detail_tbl_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2E86C1')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'), # Ratakan angka ke kanan
        ('ALIGN', (1,1), (2,-1), 'LEFT'),   # NIK & Nama rata kiri
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ])
    
    elements.append(Paragraph(f"<b>PT. {company_name.upper()}</b>", title_style))
    elements.append(Paragraph(f"<b>DETAIL CALCULATION OF ACTUARIAL VALUATION (PSAK 219)</b><br/>Report No: {report_no}", sub_style))
    
    for yr in sorted_years:
        elements.append(Paragraph(f"<b>Rincian Perhitungan Tingkat Individu per 31 Desember {yr}</b>", h_style))
        
        df_yr = results_dict[yr]
        if df_yr.empty:
            continue
            
        # Membuat Header Tabel (Mirip Kertas Kerja Aktuaris)
        table_data = [["No", "NIK", "Nama", "Tgl Lahir", "Gaji Kotor", "Umur", "Past\nSvc", "Future\nSvc", "Diskonto\nPHEI", "PVFB", "PBO", "CSC"]]
        
        for i, row in df_yr.iterrows():
            dob_str = row['Tanggal Lahir'].strftime('%d-%m-%Y') if pd.notnull(row['Tanggal Lahir']) else "-"
            table_data.append([
                str(i + 1),
                str(row['NIK']),
                str(row['Name'])[:20], # Potong nama jika terlalu panjang
                dob_str,
                fmt_num(row['Gross Salary']),
                fmt_num(row['Age Valuation'], 2),
                fmt_num(row['Past Service'], 2),
                fmt_num(row['Future Service'], 2),
                f"{row['Applied_Discount']*100:.2f}%",
                fmt_num(row['PVFB']),
                fmt_num(row['PBO']),
                fmt_num(row['CSC'])
            ])
            
        # Total Row
        table_data.append([
            "", "", "TOTAL", "", 
            fmt_num(df_yr['Gross Salary'].sum()), 
            "", "", "", "", 
            fmt_num(df_yr['PVFB'].sum()), 
            fmt_num(df_yr['PBO'].sum()), 
            fmt_num(df_yr['CSC'].sum())
        ])
        
        # Lebar Kolom Disesuaikan untuk Landscape Letter (Total Lebar ~720 points)
        col_widths = [25, 65, 120, 60, 70, 35, 35, 40, 50, 75, 75, 70]
        t_detail = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style khusus untuk baris Total
        row_style = detail_tbl_style
        row_style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D5D8DC'))
        row_style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        
        t_detail.setStyle(row_style)
        elements.append(t_detail)
        elements.append(PageBreak())
        
    doc.build(elements, onFirstPage=draw_footer_landscape, onLaterPages=draw_footer_landscape)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 4. STREAMLIT WEB INTERFACE 
# ==========================================
st.set_page_config(page_title="Valuasi Aktuaria Terperinci", layout="wide")
st.title("📄 Generator Laporan Aktuaria Tingkat Individu (Individual Duration Matching)")

st.sidebar.header("⚙️ Pengaturan Parameter")
input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
tanggal_laporan = st.sidebar.date_input("Tanggal Laporan Diterbitkan", datetime.date.today())
nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}")

asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=56, step=1) # Disesuaikan dengan gambar referensi

st.info("Unggah Data Karyawan untuk melihat rincian Aktuaria per Individu seperti Nilai PVFB, PBO, dan CSC dengan tingkat diskonto PHEI yang presisi.")

uploaded_file = st.file_uploader("Unggah File Excel Berisi Sensus (Contoh: Sheet 2022)", type=["xlsx", "xls"])
datasets_to_process = {}

if uploaded_file is not None:
    try:
        xl_file = pd.ExcelFile(uploaded_file)
        for sh in xl_file.sheet_names:
            match = re.search(r'(20\d{2})', sh)
            if match:
                yr = int(match.group(1))
                datasets_to_process[yr] = parse_excel_dataset(uploaded_file, sheet_name=sh)
                
        if not datasets_to_process: # Fallback jika nama sheet tidak ada tahunnya
            datasets_to_process[2022] = parse_excel_dataset(uploaded_file, sheet_name=0)
            
        st.success(f"Berhasil mendeteksi Sensus Karyawan untuk tahun: {list(datasets_to_process.keys())}")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")

st.markdown("---")

if st.button("🚀 Jalankan Valuasi Detail & Buat Laporan", type="primary") and datasets_to_process:
    with st.spinner("Menarik data Kurva PHEI dan menghitung PVFB, PBO, CSC per karyawan..."):
        results_dict = {}
        active_years = sorted(list(datasets_to_process.keys()))
        
        for yr in active_years:
            val_date_dt = datetime.datetime(yr, 12, 31)
            df_input = datasets_to_process[yr]
            hasil_valuasi = []
            
            for idx, row in df_input.iterrows():
                try:
                    dob = pd.to_datetime(row.get("Tanggal Lahir"))
                    doe = pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                    gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                except: continue
                    
                if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0: continue
                    
                current_age = (val_date_dt - dob).days / 365.25
                past_service = (val_date_dt - doe).days / 365.25
                
                engine = PSAK219Engine(valuation_year=yr, salary_increase=asumsi_gaji, retirement_age=usia_pensiun)
                kalkulasi = engine.calculate_puc(current_age, past_service, gross_salary)
                
                hasil_valuasi.append({
                    "NIK": row.get("NIK", "N/A"), 
                    "Name": row.get("Nama", "Unknown"),
                    "Tanggal Lahir": dob,
                    "Gross Salary": gross_salary,
                    "Age Valuation": current_age, 
                    "Past Service": past_service,
                    **kalkulasi
                })
                
            results_dict[yr] = pd.DataFrame(hasil_valuasi)
            
        st.session_state.results_dict = results_dict
        st.session_state.active_years = active_years
        st.session_state.calculated = True

if st.session_state.get("calculated"):
    st.success("✅ Perhitungan Selesai! Berikut adalah rincian tingkat individu:")
    
    res_dict = st.session_state.results_dict
    act_yrs = st.session_state.active_years
    
    # Menampilkan DataFrame terperinci di antarmuka Web
    for yr in sorted(act_yrs, reverse=True):
        st.subheader(f"Data Valuasi Aktuaria - Tahun {yr}")
        
        df_display = res_dict[yr].copy()
        
        # Formatting untuk tampilan web yang enak dibaca
        df_display['Tanggal Lahir'] = df_display['Tanggal Lahir'].dt.strftime('%d-%m-%Y')
        df_display['Gross Salary'] = df_display['Gross Salary'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        df_display['Age Valuation'] = df_display['Age Valuation'].apply(lambda x: f"{x:.2f}")
        df_display['Past Service'] = df_display['Past Service'].apply(lambda x: f"{x:.2f}")
        df_display['Future Service'] = df_display['Future Service'].apply(lambda x: f"{x:.2f}")
        df_display['Discount Rate'] = df_display['Applied_Discount'].apply(lambda x: f"{x*100:.2f}%")
        df_display['PVFB'] = df_display['PVFB'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_display['PBO'] = df_display['PBO'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_display['CSC'] = df_display['CSC'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Atur urutan kolom yang ditampilkan agar persis kertas kerja aktuaris
        kolom_pilihan = ['NIK', 'Name', 'Tanggal Lahir', 'Gross Salary', 'Age Valuation', 'Past Service', 'Future Service', 'Discount Rate', 'PVFB', 'PBO', 'CSC']
        
        st.dataframe(df_display[kolom_pilihan], use_container_width=True)
    
    # Tombol Unduh PDF Terperinci Landscape
    pdf_file = generate_detailed_report(
        res_dict, asumsi_gaji, usia_pensiun, act_yrs, input_perusahaan, nomor_laporan
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 UNDUH LAPORAN DETAIL (PDF LANDSCAPE)",
        data=pdf_file,
        file_name=f"DETAIL_PSAK219_{input_perusahaan.replace(' ', '_')}.pdf",
        mime="application/pdf",
        type="primary"
    )
