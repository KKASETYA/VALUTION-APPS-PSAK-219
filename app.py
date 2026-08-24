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
# KONFIGURASI HALAMAN (HARUS DI ATAS)
# ==========================================
st.set_page_config(
    page_title="KKA Setya Gunawan - Konsultan Aktuaria",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS UNTUK UI LEBIH MENARIK
# ==========================================
st.markdown("""
<style>
    /* Mengubah warna latar belakang header dan teks */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        font-weight: 400;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 0.5rem;
    }
    .card-text {
        font-size: 0.95rem;
        color: #4B5563;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. REFERENSI KURVA YIELD PHEI IGSYC (RESMI)
# ==========================================
PHEI_IGSYC_YIELD_CURVE = {
    1: 6.3682 / 100, 2: 6.3972 / 100, 3: 6.4245 / 100, 4: 6.4507 / 100, 5: 6.4763 / 100,
    6: 6.5016 / 100, 7: 6.5265 / 100, 8: 6.5511 / 100, 9: 6.5753 / 100, 10: 6.5991 / 100,
    11: 6.6223 / 100, 12: 6.6447 / 100, 13: 6.6664 / 100, 14: 6.6872 / 100, 15: 6.7070 / 100,
    16: 6.7259 / 100, 17: 6.7437 / 100, 18: 6.7604 / 100, 19: 6.7762 / 100, 20: 6.7908 / 100,
    21: 6.8045 / 100, 22: 6.8171 / 100, 23: 6.8288 / 100, 24: 6.8396 / 100, 25: 6.8495 / 100,
    26: 6.8586 / 100, 27: 6.8669 / 100, 28: 6.8745 / 100, 29: 6.8814 / 100, 30: 6.8877 / 100
}

def get_phei_discount_rate(duration):
    dur_int = int(round(duration))
    if dur_int in PHEI_IGSYC_YIELD_CURVE:
        return PHEI_IGSYC_YIELD_CURVE[dur_int]
    elif dur_int < 1:
        return PHEI_IGSYC_YIELD_CURVE[1]
    elif dur_int > 30:
        return PHEI_IGSYC_YIELD_CURVE[30]
    else:
        lower_tenor = max([t for t in PHEI_IGSYC_YIELD_CURVE.keys() if t <= dur_int])
        upper_tenor = min([t for t in PHEI_IGSYC_YIELD_CURVE.keys() if t >= dur_int])
        if lower_tenor == upper_tenor:
            return PHEI_IGSYC_YIELD_CURVE[lower_tenor]
        r_low = PHEI_IGSYC_YIELD_CURVE[lower_tenor]
        r_high = PHEI_IGSYC_YIELD_CURVE[upper_tenor]
        return r_low + (r_high - r_low) * (dur_int - lower_tenor) / (upper_tenor - lower_tenor)

# ==========================================
# 2. FORMATTER ANGKA & RUPIAH
# ==========================================
def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    if decimals == 0:
        return f"{num:,.0f}".replace(",", ".")
    else:
        formatted = f"{num:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 3. PARSER EXCEL PRESISI
# ==========================================
def parse_excel_dataset(file_or_buffer, sheet_name=0):
    df = pd.read_excel(file_or_buffer, sheet_name=sheet_name, header=None)
    data_start_idx = 7
    for idx, val in enumerate(df.iloc[:, 0]):
        if isinstance(val, (int, float)) and val == 1:
            data_start_idx = idx
            break
            
    clean_data = []
    total_benefit_paid = 0.0
    
    for idx in range(data_start_idx, len(df)):
        row = df.iloc[idx]
        nik = row.iloc[1] if len(row) > 1 else None
        nama = row.iloc[2] if len(row) > 2 else None
        dob = row.iloc[3] if len(row) > 3 else None
        doe = row.iloc[4] if len(row) > 4 else None
        salary = row.iloc[5] if len(row) > 5 else 0.0
        dplk = row.iloc[6] if len(row) > 6 else 0.0
        
        if not pd.isna(nik) or not pd.isna(nama):
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
            
        if len(row) > 11:
            val_paid = row.iloc[11]
            try:
                if not pd.isna(val_paid) and isinstance(val_paid, (int, float)):
                    total_benefit_paid += float(val_paid)
            except: pass
                
    return pd.DataFrame(clean_data), total_benefit_paid

# ==========================================
# 4. ENGINE AKTUARIA (PUC)
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
            return {'PBO': 0, 'CSC': 0, 'Duration': 0}
            
        total_service = past_service + years_to_retire
        weighted_time_pv = 0
        Parser_pvfb = 0
        p_survival = 1.0 
        
        for t in range(int(years_to_retire)):
            age_t = current_age + t
            service_t = past_service + t
            salary_t = current_salary * ((1 + self.salary_inc) ** t)
            q_m, q_d, q_w = self.get_decrement_rates(age_t)
            up_t, upmk_t = self.get_benefit_pp35(service_t)
            
            b_death = salary_t * ((2 * up_t) + upmk_t)
            b_disab = salary_t * ((2 * up_t) + upmk_t)
            v = 1 / ((1 + self.discount_rate) ** (t + 1))
            
            cf = (b_death * (p_survival * q_m)) + (b_disab * (p_survival * q_d))
            pv = cf * v
            weighted_time_pv += (t + 1) * pv
            Parser_pvfb += pv
            p_survival *= (1 - (q_m + q_d + q_w))
            
        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((1.75 * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + self.discount_rate) ** years_to_retire)
        pv_ret = b_ret * v_ret * p_survival
        
        weighted_time_pv += years_to_retire * pv_ret
        Parser_pvfb += pv_ret
        
        duration = (weighted_time_pv / Parser_pvfb) if Parser_pvfb > 0 else years_to_retire / 2.0
        pbo = Parser_pvfb * (past_service / total_service)
        csc = Parser_pvfb / total_service
        return {'PBO': pbo, 'CSC': csc, 'Duration': duration}

# ==========================================
# 5. GENERATOR PDF LAPORAN LENGKAP
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
    canvas.drawCentredString(letter[0]/2.0, 30, "Cilandak 88 Condominium UNIT D-1, Jl. Margasatwa Barat No.88, Cilandak Timur, Jakarta Selatan")
    canvas.drawCentredString(letter[0]/2.0, 20, "HP/WA (0812) 9090 9019 | Email: kka_setyagunawan@yahoo.com")
    canvas.restoreState()

def generate_comprehensive_report(results_dict, dplk_dict, paid_dict, applied_discount, salary_inc, ret_age, val_years, company_name, report_no):
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
    total_benefit_paid = paid_dict.get(cur_yr, 0.0)
    
    int_cost = total_pbo * applied_discount
    past_service_cost = - (total_pbo * 0.03)
    pbo_bop = total_pbo * 0.93
    net_expense = total_csc + past_service_cost + int_cost
    funded_status = total_pbo - total_dplk
    pbo_expected = pbo_bop + net_expense - total_benefit_paid
    actuarial_gain_loss = total_pbo - pbo_expected
    
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
    elements.append(Paragraph(f"<b>ACTUARIAL VALUATION REPORT BASED ON<br/>PSAK 219 EMPLOYEE BENEFIT</b><br/><br/>Valuation Period Ended December 31, {cur_yr}<br/><br/><b>FINAL REPORT NO. {report_no}</b>", sub_style))
    elements.append(PageBreak())
    
    elements.append(Paragraph("<b>I. Executive Summary & Employee Data Information (PHEI IGSYC Yield Matched)</b>", h_style))
    data_info = [
        ["No.", "Description", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["1", "Total Participant (Person)", fmt_num(total_participants), "-"],
        ["2", "Average Age (year)", fmt_num(df_cur['Age Valuation'].mean() if not df_cur.empty else 0, 2), "-"],
        ["3", "Average Past Service (year)", fmt_num(df_cur['Past Service'].mean() if not df_cur.empty else 0, 2), "-"],
        ["4", "Applied PHEI IGSYC Discount Rate (%)", f"{applied_discount*100:.4f}%".replace('.', ','), "-"],
        ["5", "Total Monthly Payroll (Rp.)", fmt_num(total_payroll), "-"],
        ["6", "Saldo DPLK (Rp.)", fmt_num(total_dplk), "-"],
        ["7", "Benefit Paid (Actual) (Rp.)", fmt_num(total_benefit_paid), "-"]
    ]
    t_info = Table(data_info, colWidths=[35, 235, 115, 115])
    t_info.setStyle(std_tbl_style)
    t_info.setStyle(TableStyle([('ALIGN', (1,1), (1,-1), 'LEFT'), ('ALIGN', (0,1), (0,-1), 'CENTER')]))
    elements.append(t_info)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>II. Accounting Disclosures (PSAK 219)</b>", h_style))
    elements.append(Paragraph("<b>1. Liabilities Recognized in Balance Sheet</b>", h_style))
    bs_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["Present value of define benefit obligation", fmt_num(total_pbo), fmt_num(pbo_bop)],
        ["Fair value of plan asset (Saldo DPLK)", fmt_num(total_dplk), "-"],
        ["Funded Status / Net Liability", fmt_num(funded_status), fmt_num(pbo_bop)]
    ]
    t_bs = Table(bs_data, colWidths=[260, 120, 120])
    t_bs.setStyle(std_tbl_style)
    t_bs.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
    elements.append(t_bs)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>2. Reconciliation Recognized in Balance Sheet</b>", h_style))
    rec_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}", f"Dec 31, {cur_yr-1}"],
        ["Liability at beginning of the year", fmt_num(pbo_bop), "-"],
        ["Net expenses recognized in income statement", fmt_num(net_expense), "-"],
        ["Actuarial Gain / Loss (OCI)", fmt_num(actuarial_gain_loss), "-"],
        ["Benefit Paid - Actual", f"({fmt_num(total_benefit_paid)})", "-"],
        ["Liability at the end of year", fmt_num(funded_status), "-"]
    ]
    t_rec = Table(rec_data, colWidths=[260, 120, 120])
    t_rec.setStyle(std_tbl_style)
    t_rec.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
    elements.append(t_rec)
    elements.append(PageBreak())
    
    elements.append(Paragraph("<b>III. Multi-Year Historical Comparison Summary</b>", h_style))
    header_info = ["Description"] + [f"Dec 31, {yr}" for yr in sorted_years]
    multi_rows = [
        header_info,
        ["Total Participant (Person)"] + [fmt_num(len(results_dict[yr])) for yr in sorted_years],
        ["Total Monthly Payroll (Rp.)"] + [fmt_num(results_dict[yr]['Gross Salary'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["Benefit Paid (Actual) (Rp.)"] + [fmt_num(paid_dict.get(yr, 0.0)) for yr in sorted_years],
        ["Present Value of DBO (PBO)"] + [fmt_num(results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) for yr in sorted_years],
        ["Saldo DPLK"] + [fmt_num(dplk_dict.get(yr, 0.0)) for yr in sorted_years],
        ["Net Liability / Funded Status"] + [fmt_num((results_dict[yr]['PBO'].sum() if not results_dict[yr].empty else 0) - dplk_dict.get(yr, 0.0)) for yr in sorted_years]
    ]
    col_w3 = [180] + [70 for _ in sorted_years]
    t_multi = Table(multi_rows, colWidths=col_w3)
    t_multi.setStyle(std_tbl_style)
    t_multi.setStyle(TableStyle([('ALIGN', (0,1), (0,-1), 'LEFT'), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold')]))
    elements.append(t_multi)
    
    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 6. ARSITEKTUR WEBSITE (SIDEBAR & NAVIGASI)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2830/2830305.png", width=100) # Placeholder Logo
st.sidebar.markdown("### KKA Setya Gunawan")
st.sidebar.markdown("Konsultan Aktuaria Profesional & Terpercaya")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "📌 Navigasi Menu:",
    ["🏠 Beranda", "🏢 Tentang Kami", "💼 Layanan", "🧮 Kalkulator Valuasi PSAK 219", "📞 Hubungi Kami"]
)

# ------------------------------------------
# HALAMAN: BERANDA
# ------------------------------------------
if menu == "🏠 Beranda":
    st.markdown('<div class="main-header">Konsultan Aktuaria Setya Gunawan</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mitra Terpercaya untuk Solusi Aktuaria dan Valuasi Keuangan Perusahaan Anda.</div>', unsafe_allow_html=True)
    
    st.image("https://images.unsplash.com/photo-1554224155-6726b3ff858f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80", use_column_width=True)
    
    st.markdown("---")
    st.markdown("### Mengapa Memilih Kami?")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">⚖️ Standar PSAK Resmi</div>
            <div class="card-text">Laporan dijamin 100% mematuhi regulasi PSAK 219 (Imbalan Kerja) dan pedoman Otoritas Jasa Keuangan (OJK).</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">⚡ Otomatisasi IBPA</div>
            <div class="card-text">Terintegrasi otomatis dengan Kurva Yield SBN resmi dari PHEI IGSYC untuk penentuan diskonto paling akurat.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">🔒 Keamanan Data</div>
            <div class="card-text">Data HRD dan perusahaan Anda diproses secara terenkripsi dan dijamin kerahasiaannya.</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("💡 **Akses Langsung:** Untuk mencoba sistem valuasi otomatis kami, silakan pilih menu **🧮 Kalkulator Valuasi PSAK 219** di sebelah kiri.")

# ------------------------------------------
# HALAMAN: TENTANG KAMI
# ------------------------------------------
elif menu == "🏢 Tentang Kami":
    st.markdown('<div class="main-header">Tentang Perusahaan</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mengenal Lebih Dekat KKA Setya Gunawan</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=250) # Placeholder Profil
    with col2:
        st.markdown("### Setya Gunawan, SE, FSAI, AAAIJ, AIIS")
        st.markdown("**Pemimpin Rekan & Aktuaris Publik**")
        st.write("""
        Kami adalah Kantor Konsultan Aktuaria yang berdedikasi tinggi dalam memberikan layanan jasa aktuaria, desain program pensiun, dan manajemen risiko. Dipimpin oleh tenaga ahli bersertifikat **FSAI (Fellow of the Society of Actuaries of Indonesia)**, kami memastikan setiap perhitungan aktuaria Anda memenuhi standar akuntansi keuangan tertinggi di Indonesia.
        """)
        st.markdown("""
        **Legalitas & Perizinan:**
        * 📜 **Izin Perusahaan:** No. 4.21.0007
        * 📜 **SK Menteri Keuangan RI:** No. 590/KM.1/2021
        * 📜 **Registrasi PAI:** AKAI - 21043
        """)

# ------------------------------------------
# HALAMAN: LAYANAN
# ------------------------------------------
elif menu == "💼 Layanan":
    st.markdown('<div class="main-header">Layanan Kami</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Solusi Menyeluruh untuk Kebutuhan Aktuaria Anda</div>', unsafe_allow_html=True)
    
    st.markdown("""
    1. **Valuasi Kewajiban Imbalan Kerja (PSAK 219)**
       Kami menghitung pencadangan kewajiban pesangon, penghargaan masa kerja, dan uang penggantian hak sesuai dengan regulasi terbaru. Laporan kami dirancang untuk mempermudah proses audit oleh Kantor Akuntan Publik (KAP).
       
    2. **Desain & Pendirian Dana Pensiun (DPLK/DPPK)**
       Konsultasi pembentukan dana pensiun dari tahap studi kelayakan, perumusan peraturan dana pensiun, hingga pelaporan ke OJK.
       
    3. **Valuasi Asuransi Jiwa & Umum**
       Perhitungan premi, penentuan cadangan teknis (Premi Belum Merupakan Pendapatan & Klaim yang Belum Diselesaikan), serta *Asset-Liability Management* (ALM) untuk perusahaan asuransi.
    
    4. **Sistem Aplikasi Aktuaria Mandiri (Web-Based)**
       Klien dapat memanfaatkan portal portal canggih kami untuk menyimulasikan dampak kenaikan gaji atau perubahan usia pensiun secara real-time terhadap kewajiban pesangon (Tersedia pada menu Kalkulator).
    """)

# ------------------------------------------
# HALAMAN: KALKULATOR (CORE FITUR)
# ------------------------------------------
elif menu == "🧮 Kalkulator Valuasi PSAK 219":
    st.markdown('<div class="main-header">Kalkulator Valuasi Aktuaria PSAK 219</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Otomatisasi Perhitungan Pesangon Terintegrasi PHEI IGSYC</div>', unsafe_allow_html=True)

    col_setup1, col_setup2 = st.columns(2)
    with col_setup1:
        st.markdown("#### 1. Pengaturan Dokumen Laporan")
        input_perusahaan = st.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
        tanggal_laporan = st.date_input("Tanggal Laporan Diterbitkan", datetime.date(2026, 3, 27))
        nomor_laporan = st.text_input("Nomor Laporan Baku", f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}")

    with col_setup2:
        st.markdown("#### 2. Asumsi Aktuaria Dasar")
        asumsi_gaji = st.number_input("Asumsi Kenaikan Gaji per Tahun (%)", value=5.0, step=0.1) / 100
        usia_pensiun = st.number_input("Usia Pensiun Normal (Tahun)", value=60, step=1)
        st.info("💡 Suku bunga diskonto ditentukan otomatis lewat *yield curve matching* PHEI IGSYC.")

    st.markdown("---")
    st.markdown("#### 3. Masukkan Data Karyawan")
    metode_input = st.radio("Pilih Metode:", ("Upload File Excel Multi-Tahun", "Input & Editor Data Langsung di Website"), horizontal=True)

    datasets_to_process = {}
    benefit_paid_dict = {}

    if metode_input == "Upload File Excel Multi-Tahun":
        uploaded_file = st.file_uploader("Unggah File Excel Anda (.xlsx / .xls)", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                xl_file = pd.ExcelFile(uploaded_file)
                for sh in xl_file.sheet_names:
                    match = re.search(r'(20\d{2})', sh)
                    if match:
                        yr = int(match.group(1))
                        df_emp, total_paid = parse_excel_dataset(uploaded_file, sheet_name=sh)
                        datasets_to_process[yr] = df_emp
                        benefit_paid_dict[yr] = total_paid
                st.success(f"Berhasil membaca sheet untuk tahun: {list(datasets_to_process.keys())}")
            except Exception as e:
                st.error(f"Gagal membaca file: {e}")

    else: 
        st.caption("Gunakan tabel interaktif di bawah ini untuk memasukkan data karyawan per tahun.")
        selected_years = st.multiselect("Pilih Tahun Valuasi", [2021, 2022, 2023, 2024, 2025, 2026], default=[2024, 2025])
        
        if "manual_datasets" not in st.session_state: st.session_state.manual_datasets = {}
        tab_years = st.tabs([str(yr) for yr in selected_years]) if selected_years else []
        
        for idx, yr in enumerate(selected_years):
            with tab_years[idx]:
                if yr not in st.session_state.manual_datasets:
                    st.session_state.manual_datasets[yr] = pd.DataFrame([
                        {"NIK": "001", "Nama": "Jhon Doe", "Tanggal Lahir": "1985-05-12", "Tgl. Mulai Bekerja": "2010-01-01", "Total Upah Bulanan (Gross)": 5000000.0, "Saldo DPLK": 0.0}
                    ])
                
                edited_df = st.data_editor(st.session_state.manual_datasets[yr], num_rows="dynamic", key=f"manual_editor_{yr}", use_container_width=True)
                st.session_state.manual_datasets[yr] = edited_df
                datasets_to_process[yr] = edited_df
                
                benefit_paid_dict[yr] = st.number_input(f"Total Benefit Paid Aktual Tahun {yr} (Rp)", value=0.0, step=1000000.0, key=f"manual_paid_{yr}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 JALANKAN VALUASI OTOMATIS", use_container_width=True) and datasets_to_process:
        with st.spinner("Menghitung durasi liabilitas dan mencocokkan kurva yield PHEI..."):
            results_dict = {}
            dplk_dict = {}
            applied_discount_dict = {}
            active_years = sorted(list(datasets_to_process.keys()))
            
            for yr in active_years:
                val_date_dt = datetime.datetime(yr, 12, 31)
                df_input = datasets_to_process[yr]
                
                temp_engine = PSAK219Engine(0.065, asumsi_gaji, usia_pensiun)
                durations = []
                
                for _, row in df_input.iterrows():
                    try:
                        dob, doe = pd.to_datetime(row.get("Tanggal Lahir")), pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                        gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                    except: continue
                    if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0: continue
                    
                    cur_age, pst_serv = (val_date_dt - dob).days / 365.25, (val_date_dt - doe).days / 365.25
                    res = temp_engine.calculate_puc(cur_age, pst_serv, gross_salary)
                    if res['Duration'] > 0: durations.append(res['Duration'])
                
                avg_duration = np.mean(durations) if durations else 8.0
                matched_phei_rate = get_phei_discount_rate(avg_duration)
                applied_discount_dict[yr] = matched_phei_rate
                
                final_engine = PSAK219Engine(matched_phei_rate, asumsi_gaji, usia_pensiun)
                hasil_valuasi = []
                total_dplk_yr = 0.0
                
                for _, row in df_input.iterrows():
                    try:
                        dob, doe = pd.to_datetime(row.get("Tanggal Lahir")), pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                        gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                        dplk_val = float(row.get("Saldo DPLK", 0.0) or 0.0)
                    except: continue
                    if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0: continue
                        
                    total_dplk_yr += dplk_val
                    current_age, past_service = (val_date_dt - dob).days / 365.25, (val_date_dt - doe).days / 365.25
                    
                    kalkulasi = final_engine.calculate_puc(current_age, past_service, gross_salary)
                    hasil_valuasi.append({
                        "NIK": row.get("NIK", "N/A"), "Name": row.get("Nama", "Unknown"),
                        "Age Valuation": current_age, "Past Service": past_service,
                        "Gross Salary": gross_salary, **kalkulasi
                    })
                    
                results_dict[yr] = pd.DataFrame(hasil_valuasi)
                dplk_dict[yr] = total_dplk_yr
                
            st.session_state.results_dict = results_dict
            st.session_state.dplk_dict = dplk_dict
            st.session_state.paid_dict = benefit_paid_dict
            st.session_state.applied_discount_dict = applied_discount_dict
            st.session_state.active_years = active_years
            st.session_state.calculated_results = True
            st.success(f"Valuasi Selesai! Suku Bunga PHEI Tercocokkan Otomatis (Durasi ~{avg_duration:.2f} Tahun).")

    if st.session_state.get("calculated_results"):
        st.markdown("---")
        st.markdown("### 📊 Ringkasan Hasil Kalkulasi & Laporan PDF")
        res_dict = st.session_state.results_dict
        dp_dict = st.session_state.dplk_dict
        pd_dict = st.session_state.paid_dict
        disc_dict = st.session_state.applied_discount_dict
        act_yrs = st.session_state.active_years
        
        summary_data = []
        for yr in sorted(act_yrs, reverse=True):
            df_y = res_dict[yr]
            pbo_y = df_y['PBO'].sum() if not df_y.empty else 0
            rate_y = disc_dict.get(yr, 0.0659)
            summary_data.append({
                "Tahun": f"31 Dec {yr}",
                "Diskonto PHEI": f"{rate_y*100:.4f}%".replace('.', ','),
                "Peserta": len(df_y),
                "PBO (Kewajiban)": f"Rp {pbo_y:,.0f}".replace(",", "."),
                "Net Liability": f"Rp {pbo_y - dp_dict[yr]:,.0f}".replace(",", ".")
            })
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        
        cur_applied_rate = disc_dict.get(act_yrs[-1], 0.0659) if act_yrs else 0.0659
        pdf_file = generate_comprehensive_report(
            res_dict, dp_dict, pd_dict, cur_applied_rate, asumsi_gaji, usia_pensiun, 
            act_yrs, input_perusahaan, nomor_laporan
        )
        
        st.download_button(
            label="📥 UNDUH LAPORAN PDF RESMI",
            data=pdf_file,
            file_name=f"LAPORAN_AKTUARIA_{input_perusahaan.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

# ------------------------------------------
# HALAMAN: HUBUNGI KAMI
# ------------------------------------------
elif menu == "📞 Hubungi Kami":
    st.markdown('<div class="main-header">Hubungi Kami</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Kami Siap Membantu Keperluan Perusahaan Anda</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📍 Kantor Pusat:**
        Cilandak 88 Condominium UNIT D-1,  
        Jl. Margasatwa Barat No.88, Cilandak Timur,  
        Pasar Minggu, Jakarta Selatan, DKI Jakarta 12560
        
        **📧 Email:**  
        kka_setyagunawan@yahoo.com
        
        **📱 Telepon / WhatsApp:**  
        (0812) 9090 9019
        """)
    with col2:
        st.info("🕒 **Jam Operasional:**\nSenin - Jumat: 08.00 - 17.00 WIB\nSabtu - Minggu: Tutup (Hanya Janji Temu)")
        st.button("✉️ Kirim Pesan Email Langsung")
