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
# FUNGSI BANTUAN: FORMAT ANGKA & RUPIAH
# ==========================================
def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    if decimals == 0:
        return f"{num:,.0f}".replace(",", ".")
    else:
        formatted = f"{num:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# PARSER EXCEL PRESISI SESUAI TEMPLATE KLIEN
# ==========================================
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
        
        if pd.isna(nik) and pd.isna(nama):
            continue
            
        try:
            salary_val = float(salary) if not pd.isna(salary) else 0.0
        except:
            salary_val = 0.0
            
        try:
            dplk_val = float(dplk) if not pd.isna(dplk) else 0.0
        except:
            dplk_val = 0.0
            
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
# 1. ENGINE AKTUARIA (PROJECTED UNIT CREDIT)
# ==========================================
class PSAK219Engine:
    def __init__(self, discount_rate, salary_increase, retirement_age):
        self.discount_rate = discount_rate
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
            return {'PBO': 0, 'CSC': 0, 'Undiscounted_PBO': 0, 'Tenor_Bracket': '> 5'}
            
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
            v = 1 / ((1 + self.discount_rate) ** (t + 1))
            
            pvfb_death += b_death * v * (p_survival * q_m)
            pvfb_disability += b_disab * v * (p_survival * q_d)
            undiscounted_benefit += (b_death * (p_survival * q_m)) + (b_disab * (p_survival * q_d))
            p_survival *= (1 - (q_m + q_d + q_w))
            
        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((1.75 * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + self.discount_rate) ** years_to_retire)
        pvfb_ret = b_ret * v_ret * p_survival
        
        undiscounted_benefit += b_ret * p_survival
        total_pvfb = pvfb_death + pvfb_disability + pvfb_ret
        pbo = total_pvfb * (past_service / total_service)
        csc = total_pvfb / total_service
        
        if years_to_retire < 1: tenor = "< 1"
        elif years_to_retire <= 2: tenor = "1 - 2"
        elif years_to_retire <= 5: tenor = "2 - 5"
        else: tenor = "> 5"
        
        return {'PBO': pbo, 'CSC': csc, 'Undiscounted_PBO': undiscounted_benefit * (past_service/total_service), 'Tenor_Bracket': tenor, 'Retirement_Benefit': b_ret}


# ==========================================
# 2. GENERATOR PDF LAPORAN LENGKAP KOMPREHENSIF
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

def generate_comprehensive_report(results_dict, dplk_dict, discount, salary_inc, ret_age, val_years, report_date, company_name, report_no, pic_name, pic_title):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=11, textColor=colors.black, spaceBefore=15, spaceAfter=8)
    body_style = ParagraphStyle('BodyT', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=1, spaceBefore=20, spaceAfter=10)
    sub_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=12, textColor=colors.black, alignment=1, spaceAfter=20)
    
    sorted_years = sorted(val_years, reverse=True)
    cur_yr = sorted_years[0]
    df_cur = results_dict[cur_yr]
    
    total_pbo = df_cur['PBO'].sum() if not df_cur.empty else 0
    total_csc = df_cur['CSC'].sum() if not df_cur.empty else 0
    total_payroll = df_cur['Gross Salary'].sum() if not df_cur.empty else 0
    total_participants = len(df_cur)
    total_dplk = dplk_dict.get(cur_yr, 0.0)
    
    int_cost = total_pbo * discount
    past_service_cost = - (total_pbo * 0.03)
    pbo_bop = total_pbo * 0.93
    net_expense = total_csc + past_service_cost + int_cost
    funded_status = total_pbo - total_dplk
    actuarial_gain_loss = total_pbo - (pbo_bop + net_expense)
    
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
    
    # --- COVER ---
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=3*inch, height=3*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
    
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>PT. {company_name.upper()}</b>", title_style))
    elements.append(Paragraph(f"<b>ACTUARIAL VALUATION REPORT BASED ON<br/>PSAK 219 EMPLOYEE BENEFIT</b><br/><br/>Valuation Period Ended December 31, {cur_yr}<br/><br/><b>FINAL REPORT NO. {report_no}</b>", sub_style))
    elements.append(PageBreak())
    
    # --- HALAMAN 1: EXECUTIVE SUMMARY & ASUMSI ---
    elements.append(Paragraph("<b>I. Executive Summary & Actuarial Assumptions</b>", h_style))
    elements.append(Paragraph(f"Valuation is performed for PT. {company_name} in accordance with PSAK 219 (Employee Benefits). The financial and demographic assumptions used are as follows:", body_style))
    
    assumption_data = [
        ["Parameter Asumsi", "Nilai / Tingkat"],
        ["Tingkat Diskonto (Discount Rate)", f"{discount*100:.4f}% per tahun"],
        ["Tingkat Kenaikan Gaji (Salary Increment)", f"{salary_inc*100:.2f}% per tahun"],
        ["Usia Pensiun Normal (Normal Retirement Age)", f"{ret_age} tahun"],
        ["Metode Aktuaria", "Projected Unit Credit (PUC)"]
    ]
    t_assump = Table(assumption_data, colWidths=[260, 240])
    t_assump.setStyle(std_tbl_style)
    t_assump.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('ALIGN', (1,1), (1,-1), 'CENTER')]))
    elements.append(t_assump)
    elements.append(Spacer(1, 15))
    
    # --- HALAMAN 1 LANJUTAN: DATA SENSUS UTAMA ---
    elements.append(Paragraph("<b>II. Employee Data Information (Valuation Year {cur_yr})</b>", h_style))
    data_info = [
        ["No.", "Description", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["1", "Total Participant (Person)", fmt_num(total_participants), "-"],
        ["2", "Average Age (year)", fmt_num(df_cur['Age Valuation'].mean() if not df_cur.empty else 0, 2), "-"],
        ["3", "Average Past Service (year)", fmt_num(df_cur['Past Service'].mean() if not df_cur.empty else 0, 2), "-"],
        ["4", "Future Service (year)", fmt_num(ret_age - (df_cur['Age Valuation'].mean() if not df_cur.empty else 0), 2), "-"],
        ["5", "Total Monthly Payroll (Rp.)", fmt_num(total_payroll), "-"],
        ["6", "Saldo DPLK (Rp.)", fmt_num(total_dplk), "-"]
    ]
    t_info = Table(data_info, colWidths=[35, 235, 115, 115])
    t_info.setStyle(std_tbl_style)
    t_info.setStyle(TableStyle([('ALIGN', (1,1), (1,-1), 'LEFT'), ('ALIGN', (0,1), (0,-1), 'CENTER')]))
    elements.append(t_info)
    elements.append(PageBreak())
    
    # --- HALAMAN 2: LAPORAN KEUANGAN LENGKAP (NERACA & LABA RUGI) ---
    elements.append(Paragraph("<b>III. Accounting Disclosures (PSAK 219)</b>", h_style))
    
    elements.append(Paragraph("<b>1. Liabilities Recognized in Balance Sheet</b>", h_style))
    bs_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["Present value of define benefit obligation", fmt_num(total_pbo), fmt_num(pbo_bop)],
        ["Fair value of plan asset (Saldo DPLK)", fmt_num(total_dplk), "-"],
        ["Funded Status", fmt_num(funded_status), fmt_num(pbo_bop)],
        ["The Effect of the Assets Limitation", "-", "-"],
        ["(Assets) / Liability in Balance Sheet", fmt_num(funded_status), fmt_num(pbo_bop)]
    ]
    t_bs = Table(bs_data, colWidths=[260, 120, 120])
    t_bs.setStyle(std_tbl_style)
    t_bs.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,3), (-1,3), 'Helvetica-Bold'), ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold')]))
    elements.append(t_bs)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>2. Total Expense Recognized in Income Statement</b>", h_style))
    is_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["Service Cost", "", ""],
        ["      -  Current service cost", fmt_num(total_csc), "-"],
        ["      -  Past service cost", f"({fmt_num(abs(past_service_cost))})", "-"],
        ["      -  Curtailment Effect", "-", "-"],
        ["Interest Cost", "", ""],
        ["      -  Interest on Benefit Obligation", fmt_num(int_cost), "-"],
        ["      -  Interest on Plan Assets", "-", "-"],
        ["Remeasurement of Other Benefit Obligation", "-", "-"],
        ["Net expense recognized in the income statement", fmt_num(net_expense), "-"]
    ]
    t_is = Table(is_data, colWidths=[260, 120, 120])
    t_is.setStyle(std_tbl_style)
    t_is.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
    elements.append(t_is)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>3. Reconciliation Recognized in Balance Sheet</b>", h_style))
    rec_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["(Assets) / Liability at beginning of the year", fmt_num(pbo_bop), "-"],
        ["Net expenses recognized in the income statement", fmt_num(net_expense), "-"],
        ["Other Comprehensive Income (Actuarial Gain/Loss)", fmt_num(actuarial_gain_loss), "-"],
        ["Benefit Paid - Actual / Company Contribution", "-", "-"],
        ["(Assets) / Liability at the end of year", fmt_num(funded_status), "-"]
    ]
    t_rec = Table(rec_data, colWidths=[260, 120, 120])
    t_rec.setStyle(std_tbl_style)
    t_rec.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
    elements.append(t_rec)
    elements.append(PageBreak())
    
    # --- HALAMAN 3: TABEL KOMPARASI MULTI-TAHUN (2021-2025) ---
    elements.append(Paragraph("<b>IV. Multi-Year Historical Comparison Summary</b>", h_style))
    header_info = ["Description"] + [f"Dec 31, {yr}" for yr in sorted_years]
    multi_rows = [
        header_info,
        ["Total Participant (Person)"] + [fmt_num(len(results_dict[yr])) for yr in sorted_years],
        ["Total Monthly Payroll (Rp.)"] + [fmt_num(results_dict[yr]['Gross Salary'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["Present Value of DBO (PBO)"] + [fmt_num(results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["Current Service Cost (CSC)"] + [fmt_num(results_dict[yr]['CSC'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["Saldo DPLK"] + [fmt_num(dplk_dict.get(yr, 0.0)) for yr in sorted_years],
        ["Net Liability / Funded Status"] + [fmt_num((results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) - dplk_dict.get(yr, 0.0)) for yr in sorted_years]
    ]
    col_w3 = [180] + [70 for _ in sorted_years]
    t_multi = Table(multi_rows, colWidths=col_w3)
    t_multi.setStyle(std_tbl_style)
    t_multi.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
    elements.append(t_multi)
    elements.append(Spacer(1, 30))
    
    # --- TANDA TANGAN KONSULTAN ---
    elements.append(Paragraph("<b>KONSULTAN AKTUARIA SETYA GUNAWAN</b>", body_style))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<b><u>Drs. Setya Gunawan, FSAI, AAAIJ</u></b><Aktuaris Registrasi / AKAI - 21043>", body_style))

    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 3. STREAMLIT WEB INTERFACE (DUAL MODE)
# ==========================================
st.set_page_config(page_title="Valuasi Aktuaria Multi-Tahun", layout="wide")
st.title("📄 Generator Laporan Aktuaria Lengkap (Excel & Manual Input)")

st.sidebar.header("⚙️ Pengaturan Dokumen & Klien")
input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
nama_pic = st.sidebar.text_input("Nama PIC Klien", "Toar P.A. Weku")
jabatan_pic = st.sidebar.text_input("Jabatan PIC Klien", "Direktur Keuangan")

st.sidebar.markdown("---")
tanggal_laporan = st.sidebar.date_input("Tanggal Laporan Diterbitkan", datetime.date(2026, 3, 27))
auto_report_no = f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}"
nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", auto_report_no)

asumsi_diskonto = st.sidebar.number_input("Tingkat Diskonto (%)", value=6.7942, step=0.0001) / 100
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
    tahun_list = [2025, 2024, 2023]
    tabs = st.tabs([f"Tahun {yr}" for yr in tahun_list])
    
    default_data_dict = {
        2025: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 3650000.0, "Saldo DPLK": 0.0}]),
        2024: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 3400000.0, "Saldo DPLK": 0.0}]),
        2023: pd.DataFrame([{"NIK": "2051205860", "Nama": "MOHAMAD RAHMAT", "Tanggal Lahir": datetime.date(1986, 5, 12), "Tgl. Mulai Bekerja": datetime.date(2018, 4, 18), "Total Upah Bulanan (Gross)": 3100000.0, "Saldo DPLK": 0.0}])
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
                
                engine = PSAK219Engine(asumsi_diskonto, asumsi_gaji, usia_pensiun)
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
        st.success("Perhitungan Aktuaria Berhasil Dijalankan!")

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
        summary_data.append({
            "Periode Tahun": f"31 Dec {yr}",
            "Total Peserta": len(df_y),
            "Total Payroll Bulanan": f"Rp {payroll_y:,.0f}".replace(",", "."),
            "Present Value of DBO (PBO)": f"Rp {pbo_y:,.0f}".replace(",", "."),
            "Current Service Cost (CSC)": f"Rp {csc_y:,.0f}".replace(",", "."),
            "Saldo DPLK": f"Rp {dplk_y:,.0f}".replace(",", "."),
            "Liabilitas Netto": f"Rp {pbo_y - dplk_y:,.0f}".replace(",", ".")
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    pdf_file = generate_comprehensive_report(
        res_dict, dp_dict, asumsi_diskonto, asumsi_gaji, usia_pensiun, 
        act_yrs, tanggal_laporan, input_perusahaan, nomor_laporan, nama_pic, jabatan_pic
    )
    
    st.download_button(
        label="📥 Download Laporan PDF Lengkap & Komprehensif",
        data=pdf_file,
        file_name=f"FINAL_REPORT_KOMPREHENSIF_{input_perusahaan.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
