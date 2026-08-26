import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re

from reportlab.lib.pagesizes import letter
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
    """Fungsi mengambil diskonto individual matching spesifik per sisa masa kerja."""
    # Pastikan tahun ada dalam database, jika tidak gunakan batas terdekat
    if valuation_year not in MULTI_YEAR_PHEI_CURVE:
        valuation_year = max(MULTI_YEAR_PHEI_CURVE.keys()) if valuation_year > max(MULTI_YEAR_PHEI_CURVE.keys()) else min(MULTI_YEAR_PHEI_CURVE.keys())
    
    curve = MULTI_YEAR_PHEI_CURVE[valuation_year]
    dur_int = int(round(duration))

    if dur_int in curve:
        return curve[dur_int]
    elif dur_int < 1:
        return curve[0.1]
    elif dur_int > 30:
        return curve[30]
    else:
        # Interpolasi linear jika ada kebutuhan
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
        dplk = row.iloc[6] if len(row) > 6 else 0.0
        
        if pd.isna(nik) and pd.isna(nama): continue
            
        try: salary_val = float(salary) if not pd.isna(salary) else 0.0
        except: salary_val = 0.0
            
        try: dplk_val = float(dplk) if not pd.isna(dplk) else 0.0
        except: dplk_val = 0.0
            
        clean_data.append({
            'NIK': str(nik).strip() if not pd.isna(nik) else '',
            'Nama': str(nama).strip() if not pd.isna(nama) else '',
            'Tanggal Lahir': dob,
            'Tgl. Mulai Bekerja': doe,
            'Total Upah Bulanan (Gross)': salary_val,
            'Saldo DPLK': dplk_val
        })
        
    return pd.DataFrame(clean_data)


# ==========================================
# 2. ENGINE AKTUARIA (PHEI INDIVIDUAL MATCHING)
# ==========================================
class PSAK219Engine:
    def __init__(self, valuation_year, salary_increase, retirement_age):
        self.val_year = valuation_year # Tahun valuasi disimpan di init
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
            return {'PBO': 0, 'CSC': 0, 'Applied_Discount': 0, 'Undiscounted_PBO': 0, 'Tenor_Bracket': '> 5'}
            
        # [MODIFIKASI]: Ambil diskonto spesifik per individu berdasarkan tenor (future service)
        discount_rate = get_individual_phei_rate(years_to_retire, self.val_year)
        
        total_service = past_service + years_to_retire
        pvfb_death, pvfb_disability = 0, 0
        p_survival = 1.0 
        undiscounted_benefit = 0
        
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
            undiscounted_benefit += (b_death * (p_survival * q_m)) + (b_disab * (p_survival * q_d))
            p_survival *= (1 - (q_m + q_d + q_w))
            
        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((1.75 * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + discount_rate) ** years_to_retire)
        pvfb_ret = b_ret * v_ret * p_survival
        
        undiscounted_benefit += b_ret * p_survival
        total_pvfb = pvfb_death + pvfb_disability + pvfb_ret
        pbo = total_pvfb * (past_service / total_service)
        csc = total_pvfb / total_service
        
        if years_to_retire < 1: tenor = "< 1"
        elif years_to_retire <= 2: tenor = "1 - 2"
        elif years_to_retire <= 5: tenor = "2 - 5"
        else: tenor = "> 5"
        
        # Simpan diskonto yang digunakan agar bisa ditinjau di tabel
        return {
            'PBO': pbo, 'CSC': csc, 
            'Applied_Discount': discount_rate,
            'Undiscounted_PBO': undiscounted_benefit * (past_service/total_service), 
            'Tenor_Bracket': tenor, 'Retirement_Benefit': b_ret
        }


# ==========================================
# 3. GENERATOR PDF MULTI-TAHUN
# ==========================================
def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(36, 65, 576, 65)
    
    footer_text1 = "Konsultan Aktuaria Setya Gunawan"
    footer_text2 = "Izin Perusahaan No. 4.21.0007 | Keputusan Menteri Keuangan RI No. 590/KM.1/2021 | AKAI - 21043"
    footer_text3 = "Cilandak 88 Condominium UNIT D-1, Jl. Margasatwa Barat No.88, Cilandak Timur, Pasar Minggu,"
    footer_text4 = "Jakarta Selatan, DKI Jakarta 12560 | HP/WA (0812) 9090 9019 | Email: kka_setyagunawan@yahoo.com"
    
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(letter[0]/2.0, 50, footer_text1)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(letter[0]/2.0, 40, footer_text2)
    canvas.drawCentredString(letter[0]/2.0, 30, footer_text3)
    canvas.drawCentredString(letter[0]/2.0, 20, footer_text4)
    canvas.restoreState()

def generate_multiyear_report(results_dict, dplk_dict, salary_inc, ret_age, val_years, report_date, company_name, report_no, pic_name, pic_title):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=11, textColor=colors.black, spaceBefore=15, spaceAfter=8)
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=1, spaceBefore=20, spaceAfter=10)
    sub_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=12, textColor=colors.black, alignment=1, spaceAfter=20)
    
    sorted_years = sorted(val_years, reverse=True)
    
    std_tbl_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F2F2F2')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ])
    
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=3*inch, height=3*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>PT. {company_name.upper()}</b>", title_style))
    elements.append(Paragraph(f"<b>MULTI-YEAR ACTUARIAL VALUATION BASED ON<br/>PSAK 219 EMPLOYEE BENEFIT</b><br/><br/>Valuation Years: {', '.join(map(str, sorted_years))}<br/><i>Discount Rate Method: Individual Yield Curve Matching (PHEI)</i><br/><br/><b>FINAL REPORT NO. {report_no}</b>", sub_style))
    elements.append(PageBreak())
    
    elements.append(Paragraph(f"<b>IV. Employee Data Information (Multi-Year Comparison)</b>", h_style))
    header_info = ["No.", "Description"] + [f"Dec 31, {yr}" for yr in sorted_years]
    info_rows = [
        header_info,
        ["1", "Total Participant (Person)"] + [fmt_num(len(results_dict[yr])) for yr in sorted_years],
        ["2", "Average Age (year)"] + [fmt_num(results_dict[yr]['Age Valuation'].mean() if not results_dict[yr].empty else 0, 2) for yr in sorted_years],
        ["3", "Average Past Service (year)"] + [fmt_num(results_dict[yr]['Past Service'].mean() if not results_dict[yr].empty else 0, 2) for yr in sorted_years],
        ["4", "Future Service (year)"] + [fmt_num(ret_age - results_dict[yr]['Age Valuation'].mean() if not results_dict[yr].empty else 0, 2) for yr in sorted_years],
        ["5", "Total Monthly Payroll (Rp.)"] + [fmt_num(results_dict[yr]['Gross Salary'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["6", "Saldo DPLK (Rp.)"] + [fmt_num(dplk_dict.get(yr, 0.0)) for yr in sorted_years]
    ]
    col_w = [35, 215] + [85 for _ in sorted_years]
    t_info = Table(info_rows, colWidths=col_w)
    t_info.setStyle(std_tbl_style)
    t_info.setStyle(TableStyle([('ALIGN', (1,1), (1,-1), 'LEFT'), ('ALIGN', (0,1), (0,-1), 'CENTER')]))
    elements.append(t_info)
    elements.append(PageBreak())
    
    elements.append(Paragraph("<b>1. Liabilities Recognized in Balance Sheet</b>", h_style))
    bs_rows = [
        ["DESCRIPTION"] + [f"Dec 31, {yr}" for yr in sorted_years],
        ["Present value of define benefit obligation"] + [fmt_num(results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["Fair value of plan asset (Saldo DPLK)"] + [fmt_num(dplk_dict.get(yr, 0.0)) for yr in sorted_years],
        ["Funded Status"] + [fmt_num((results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) - dplk_dict.get(yr, 0.0)) for yr in sorted_years],
        ["The Effect of the Assets Limitation"] + ["-" for _ in sorted_years],
        ["(Assets) / Liability in Balance Sheet"] + [fmt_num((results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) - dplk_dict.get(yr, 0.0)) for yr in sorted_years]
    ]
    col_w2 = [240] + [85 for _ in sorted_years]
    t_bs = Table(bs_rows, colWidths=col_w2)
    t_bs.setStyle(std_tbl_style)
    t_bs.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'), ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold')]))
    elements.append(t_bs)
    elements.append(Spacer(1, 15))
    
    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 4. STREAMLIT WEB INTERFACE (DUAL MODE)
# ==========================================
st.set_page_config(page_title="Valuasi Aktuaria Multi-Tahun", layout="wide")
st.title("📄 Generator Laporan Aktuaria Multi-Tahun (PHEI Individual Matching)")

st.sidebar.header("⚙️ Pengaturan Dokumen & Klien")
input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
nama_pic = st.sidebar.text_input("Nama PIC Klien", "Toar P.A. Weku")
jabatan_pic = st.sidebar.text_input("Jabatan PIC Klien", "Direktur Keuangan")

st.sidebar.markdown("---")
tanggal_laporan = st.sidebar.date_input("Tanggal Laporan Diterbitkan", datetime.date(2026, 3, 27))
auto_report_no = f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}"
nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", auto_report_no)

st.sidebar.info("💡 **Tingkat Diskonto:** Diambil secara otomatis berdasarkan Kurva PHEI (2022-2025) untuk setiap individu sesuai dengan tenor masa depan mereka.")

asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=60, step=1)

metode_utama = st.radio(
    "Pilih Metode Masukan Data:", 
    ["Upload Excel Multi-Tahun (Auto-Detect Sheet 2021-2025)", "Input / Edit Manual Langsung di Web (Multi-Tab Tahun)"]
)

datasets_to_process = {}

if metode_utama == "Upload Excel Multi-Tahun (Auto-Detect Sheet 2021-2025)":
    st.subheader("Unggah File Excel Berisi Sheet Multi-Tahun")
    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls)", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            xl_file = pd.ExcelFile(uploaded_file)
            sheet_names = xl_file.sheet_names
            st.success(f"Berhasil mendeteksi {len(sheet_names)} sheet: {sheet_names}")
            
            detected_years = []
            sheet_map = {}
            for sh in sheet_names:
                match = re.search(r'(20\d{2})', sh)
                if match:
                    yr = int(match.group(1))
                    detected_years.append(yr)
                    sheet_map[yr] = sh
                    
            if detected_years:
                detected_years = sorted(list(set(detected_years)))
                st.info(f"Tahun terdeteksi secara otomatis dari nama sheet: {detected_years}")
                for yr in detected_years:
                    datasets_to_process[yr] = parse_excel_dataset(uploaded_file, sheet_name=sheet_map[yr])
            else:
                st.warning("Nama sheet tidak mengandung tahun. Menggunakan tahun 2025 sebagai default.")
                datasets_to_process[2025] = parse_excel_dataset(uploaded_file, sheet_name=0)
        except Exception as e:
            st.error(f"Gagal membaca file Excel: {e}")
else:
    st.subheader("Input / Edit Manual Data Sensus per Tahun")
    tahun_list = [2025, 2024, 2023, 2022]
    tabs = st.tabs([f"Tahun {yr}" for yr in tahun_list])
    
    default_data_dict = {
        2025: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 3650000.0, "Saldo DPLK": 0.0}]),
        2024: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 3400000.0, "Saldo DPLK": 0.0}]),
        2023: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 3100000.0, "Saldo DPLK": 0.0}]),
        2022: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 2800000.0, "Saldo DPLK": 0.0}])
    }
    
    for i, yr in enumerate(tahun_list):
        with tabs[i]:
            st.write(f"Masukkan data karyawan per 31 Desember {yr}:")
            datasets_to_process[yr] = st.data_editor(default_data_dict[yr], num_rows="dynamic", key=f"manual_edit_{yr}", use_container_width=True)

st.markdown("---")
st.subheader("Proses & Unduh Hasil Perhitungan")

if "calculated_results" not in st.session_state:
    st.session_state.calculated_results = None

if st.button("Jalankan Valuasi & Tampilkan Hasil 🚀") and datasets_to_process:
    with st.spinner("Memproses perhitungan aktuaria..."):
        results_dict = {}
        dplk_dict = {}
        active_years = sorted(list(datasets_to_process.keys()))
        
        for yr in active_years:
            val_date_dt = datetime.datetime(yr, 12, 31)
            df_input = datasets_to_process[yr]
            hasil_valuasi = []
            total_dplk_yr = 0.0
            
            for _, row in df_input.iterrows():
                dob_val = row.get("Tanggal Lahir")
                doe_val = row.get("Tgl. Mulai Bekerja")
                gross_salary = row.get("Total Upah Bulanan (Gross)", 0)
                dplk_val = row.get("Saldo DPLK", 0.0)
                
                try:
                    dob = pd.to_datetime(dob_val)
                    doe = pd.to_datetime(doe_val)
                    gross_salary = float(gross_salary)
                    dplk_val = float(dplk_val) if not pd.isna(dplk_val) else 0.0
                except:
                    continue
                    
                if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0:
                    continue
                    
                total_dplk_yr += dplk_val
                current_age = (val_date_dt - dob).days / 365.25
                past_service = (val_date_dt - doe).days / 365.25
                
                # Masukkan parameter TAHUN agar mesin mengekstrak diskonto yang tepat
                engine = PSAK219Engine(valuation_year=yr, salary_increase=asumsi_gaji, retirement_age=usia_pensiun)
                kalkulasi = engine.calculate_puc(current_age, past_service, gross_salary)
                
                hasil_valuasi.append({
                    "NIK": row.get("NIK", "N/A"), 
                    "Name": row.get("Nama", "Unknown"),
                    "Age Valuation": current_age, 
                    "Past Service": past_service,
                    "Gross Salary": gross_salary, 
                    **kalkulasi
                })
                
            results_dict[yr] = pd.DataFrame(hasil_valuasi)
            dplk_dict[yr] = total_dplk_yr
            
        st.session_state.results_dict = results_dict
        st.session_state.dplk_dict = dplk_dict
        st.session_state.active_years = active_years
        st.session_state.calculated_results = True
        st.success("Perhitungan Aktuaria Berhasil Dijalankan! Penarikan diskonto individu aktif.")

if st.session_state.get("calculated_results"):
    st.subheader("📊 Ringkasan Hasil Kalkulasi di Website")
    res_dict = st.session_state.results_dict
    dp_dict = st.session_state.dplk_dict
    act_yrs = st.session_state.active_years
    
    summary_data = []
    for yr in sorted(act_yrs, reverse=True):
        df_y = res_dict[yr]
        pbo_y = df_y['PBO'].sum() if not df_y.empty else 0
        csc_y = df_y['CSC'].sum() if not df_y.empty else 0
        payroll_y = df_y['Gross Salary'].sum() if not df_y.empty else 0
        dplk_y = dp_dict[yr]
        avg_discount = df_y['Applied_Discount'].mean() if not df_y.empty else 0
        
        summary_data.append({
            "Periode Tahun": f"31 Dec {yr}",
            "Sistem Diskonto": f"PHEI Matched (~{avg_discount*100:.2f}%)",
            "Total Peserta": len(df_y),
            "Total Payroll Bulanan": f"Rp {payroll_y:,.0f}".replace(",", "."),
            "Present Value of DBO (PBO)": f"Rp {pbo_y:,.0f}".replace(",", "."),
            "Current Service Cost (CSC)": f"Rp {csc_y:,.0f}".replace(",", "."),
            "Saldo DPLK": f"Rp {dplk_y:,.0f}".replace(",", "."),
            "Liabilitas Netto": f"Rp {pbo_y - dplk_y:,.0f}".replace(",", ".")
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    pdf_file = generate_multiyear_report(
        res_dict, dp_dict, asumsi_gaji, usia_pensiun, 
        act_yrs, tanggal_laporan, input_perusahaan, nomor_laporan, nama_pic, jabatan_pic
    )
    
    st.download_button(
        label="📥 Download Laporan PDF Resmi Multi-Tahun",
        data=pdf_file,
        file_name=f"FINAL_REPORT_PSAK219_{input_perusahaan.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
