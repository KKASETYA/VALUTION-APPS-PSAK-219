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
# PARSER EXCEL MULTI-SHEET (TETAP, KONTRAK, CUTI)
# ==========================================
def parse_excel_universal(file_or_buffer, sheet_name):
    df = pd.read_excel(file_or_buffer, sheet_name=sheet_name, header=None)
    
    # Deteksi baris awal data berdasarkan angka '1' di kolom pertama atau kolom NIK/No
    data_start_idx = 7
    for idx, val in enumerate(df.iloc[:, 0]):
        if isinstance(val, (int, float)) and val == 1:
            data_start_idx = idx
            break
        # Cek juga jika kolom 1 berisi NIK atau angka
        if idx > 3 and not pd.isna(df.iloc[idx, 1]) and str(df.iloc[idx, 1]).strip().isdigit():
            data_start_idx = idx
            break
            
    clean_data = []
    total_benefit_paid = 0.0
    
    for idx in range(data_start_idx, len(df)):
        row = df.iloc[idx]
        
        # Format umum template: Col 1 = NIK, Col 2 = Nama, Col 3 = Lahir, Col 4 = Mulai Bekerja, Col 5 = Gaji, Col 6 = DPLK
        nik = row.iloc[1] if len(row) > 1 else None
        nama = row.iloc[2] if len(row) > 2 else None
        dob = row.iloc[3] if len(row) > 3 else None
        doe = row.iloc[4] if len(row) > 4 else None
        salary = row.iloc[5] if len(row) > 5 else 0.0
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
        
    return pd.DataFrame(clean_data), total_benefit_paid


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
        
        return {'PBO': pbo, 'CSC': csc, 'Undiscounted_PBO': undiscounted_benefit * (past_service/total_service), 'Retirement_Benefit': b_ret}


# ==========================================
# 2. GENERATOR PDF LAPORAN LENGKAP
# ==========================================
def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(36, 65, 576, 65)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(letter[0]/2.0, 50, "Konsultan Aktuaria Setya Gunawan")
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(letter[0]/2.0, 40, "Izin Perusahaan No. 4.21.0007 | Keputusan Menteri Keuangan RI No. 590/KM.1/2021 | AKAI - 21043")
    canvas.restoreState()

def generate_comprehensive_report(results_dict, dplk_dict, paid_dict, discount, salary_inc, ret_age, val_years, company_name, report_no):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=11, textColor=colors.black, spaceBefore=15, spaceAfter=8)
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
    
    elements.append(Paragraph(f"<b>PT. {company_name.upper()}</b>", title_style))
    elements.append(Paragraph(f"<b>ACTUARIAL VALUATION REPORT (PSAK 219)<br/>Valuation Year: {cur_yr}</b><br/><br/><b>FINAL REPORT NO. {report_no}</b>", sub_style))
    elements.append(PageBreak())
    
    elements.append(Paragraph("<b>I. Executive Summary & Employee Data Information</b>", h_style))
    data_info = [
        ["No.", "Description", f"Dec 31, {cur_yr}"],
        ["1", "Total Participant (Person)", fmt_num(total_participants)],
        ["2", "Total Monthly Payroll (Rp.)", fmt_num(total_payroll)],
        ["3", "Present Value of DBO (PBO) (Rp.)", fmt_num(total_pbo)],
        ["4", "Saldo DPLK (Rp.)", fmt_num(total_dplk)],
        ["5", "Net Liability (Rp.)", fmt_num(total_pbo - total_dplk)]
    ]
    t_info = Table(data_info, colWidths=[35, 270, 135])
    t_info.setStyle(std_tbl_style)
    elements.append(t_info)
    
    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 3. STREAMLIT WEB INTERFACE
# ==========================================
st.set_page_config(page_title="Valuasi Aktuaria Multi-Sheet", layout="wide")
st.title("📄 Generator Laporan Aktuaria (Multi-Sheet: Tetap, Kontrak, & Cuti)")

st.sidebar.header("⚙️ Pengaturan Dokumen & Klien")
input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT. GATRA MAPAN INDONESIA")
nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", "082/KAS-FR/PSAK/III/2026")

asumsi_diskonto = st.sidebar.number_input("Tingkat Diskonto (%)", value=6.7942, step=0.0001) / 100
asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=56, step=1)

uploaded_file = st.file_uploader("Unggah File Excel Template Karyawan Kontrak/Tetap (.xlsx / .xls)", type=["xlsx", "xls"])

datasets_to_process = {}
benefit_paid_dict = {}

if uploaded_file is not None:
    try:
        xl_file = pd.ExcelFile(uploaded_file)
        sheet_names = xl_file.sheet_names
        st.success(f"Sheet terdeteksi: {sheet_names}")
        
        for sh in sheet_names:
            # Cari sheet yang mengandung tahun atau kata 'kontrak'
            match = re.search(r'(20\d{2})', sh)
            if match:
                yr = int(match.group(1))
                df_emp, total_paid = parse_excel_universal(uploaded_file, sheet_name=sh)
                datasets_to_process[yr] = df_emp
                benefit_paid_dict[yr] = total_paid
            elif 'kontrak' in sh.lower():
                df_emp, total_paid = parse_excel_universal(uploaded_file, sheet_name=sh)
                datasets_to_process['Kontrak'] = df_emp
                benefit_paid_dict['Kontrak'] = total_paid
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")

st.markdown("---")
if "calculated_results" not in st.session_state:
    st.session_state.calculated_results = None

if st.button("Jalankan Valuasi Multi-Sheet 🚀") and datasets_to_process:
    with st.spinner("Memproses perhitungan aktuaria..."):
        results_dict = {}
        dplk_dict = {}
        
        for key, df_input in datasets_to_process.items():
            val_yr = 2025 if isinstance(key, int) else 2025 # Default tahun valuasi
            val_date_dt = datetime.datetime(val_yr, 12, 31)
            hasil_valuasi = []
            total_dplk_yr = 0.0
            
            for _, row in df_input.iterrows():
                try:
                    dob = pd.to_datetime(row.get("Tanggal Lahir"))
                    doe = pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                    gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                    dplk_val = float(row.get("Saldo DPLK", 0.0) or 0.0)
                except:
                    continue
                    
                if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0:
                    continue
                    
                total_dplk_yr += dplk_val
                current_age = (val_date_dt - dob).days / 365.25
                past_service = (val_date_dt - doe).days / 365.25
                
                engine = PSAK219Engine(asumsi_diskonto, asumsi_gaji, usia_pensiun)
                kalkulasi = engine.calculate_puc(current_age, past_service, gross_salary)
                
                hasil_payroll = gross_salary
                hasil_valuasi.append({
                    "NIK": row.get("NIK", "N/A"), "Name": row.get("Nama", "Unknown"),
                    "Age Valuation": current_age, "Past Service": past_service,
                    "Gross Salary": hasil_payroll, **kalkulasi
                })
                
            results_dict[key] = pd.DataFrame(hasil_valuasi)
            dplk_dict[key] = total_dplk_yr
            
        st.session_state.results_dict = results_dict
        st.session_state.dplk_dict = dplk_dict
        st.session_state.paid_dict = benefit_paid_dict
        st.session_state.calculated_results = True
        st.success("Perhitungan Selesai!")

if st.session_state.get("calculated_results"):
    st.subheader("📊 Ringkasan Hasil Kalkulasi per Kategori / Sheet")
    res_dict = st.session_state.results_dict
    dp_dict = st.session_state.dplk_dict
    
    summary_data = []
    for key, df_y in res_dict.items():
        pbo_y = df_y['PBO'].sum() if not df_y.empty else 0
        summary_data.append({
            "Kategori / Sheet": f"Sheet: {key}",
            "Total Peserta": len(df_y),
            "Total Payroll": f"Rp {df_y['Gross Salary'].sum():,.0f}".replace(",", "."),
            "Present Value of DBO (PBO)": f"Rp {pbo_y:,.0f}".replace(",", "."),
            "Saldo DPLK": f"Rp {dp_dict[key]:,.0f}".replace(",", "."),
            "Net Liability": f"Rp {pbo_y - dp_dict[key]:,.0f}".replace(",", ".")
        })
    
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    # Ambil tahun numerik pertama untuk laporan PDF
    numeric_years = [k for k in res_dict.keys() if isinstance(k, int)]
    pdf_file = generate_comprehensive_report(
        res_dict, dp_dict, st.session_state.paid_dict, asumsi_diskonto, asumsi_gaji, usia_pensiun, 
        numeric_years if numeric_years else [2025], input_perusahaan, nomor_laporan
    )
    
    st.download_button(
        label="📥 Download Laporan PDF Valuasi",
        data=pdf_file,
        file_name=f"FINAL_REPORT_KONTRAK_{input_perusahaan.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
