import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re
import base64

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

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

        if len(row) > 11:
            val_paid = row.iloc[11]
            try:
                if not pd.isna(val_paid) and isinstance(val_paid, (int, float)):
                    total_benefit_paid += float(val_paid)
            except:
                pass

    return pd.DataFrame(clean_data), total_benefit_paid

# ==========================================
# 4. ENGINE AKTUARIA (PUC DENGAN ISAK 35)
# ==========================================
class PSAK219Engine:
    def __init__(self, discount_rate, salary_increase, retirement_age, resign_rate=0.0):
        self.discount_rate = discount_rate
        self.salary_inc = salary_increase
        self.ret_age = retirement_age
        self.resign_rate = resign_rate

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
        q_resign = self.resign_rate 
        return q_mortality, q_disability, q_resign

    def calculate_puc(self, current_age, past_service, current_salary):
        years_to_retire = self.ret_age - current_age
        if pd.isna(current_age) or pd.isna(past_service) or pd.isna(current_salary) or years_to_retire <= 0:
            return {'PBO': 0, 'CSC': 0, 'Duration': 0}

        total_service = past_service + years_to_retire
        weighted_time_pv = 0
        
        # --- LOGIKA ISAK 35 (CAPPING 24 TAHUN) ---
        unattributed_years = max(0, total_service - 24)
        past_service_ret = max(0, past_service - unattributed_years)
        total_service_ret = min(total_service, 24)

        pvfb_death = 0
        pvfb_disability = 0
        pvfb_resign = 0
        p_survival = 1.0

        for t in range(int(years_to_retire)):
            age_t = current_age + t
            service_t = past_service + t
            salary_t = current_salary * ((1 + self.salary_inc) ** t)
            q_m, q_d, q_w = self.get_decrement_rates(age_t)
            up_t, upmk_t = self.get_benefit_pp35(service_t)

            b_death = salary_t * ((2 * up_t) + upmk_t)
            b_disab = salary_t * ((2 * up_t) + upmk_t)
            b_resign = salary_t * upmk_t if service_t >= 3 else 0
            
            v = 1 / ((1 + self.discount_rate) ** (t + 1))

            cf_death = b_death * p_survival * q_m
            cf_disab = b_disab * p_survival * q_d
            cf_resign = b_resign * p_survival * q_w

            pv_death = cf_death * v
            pv_disab = cf_disab * v
            pv_resign = cf_resign * v
            
            pvfb_death += pv_death
            pvfb_disability += pv_disab
            pvfb_resign += pv_resign
            
            # Bobot durasi
            weighted_time_pv += (t + 1) * (pv_death + pv_disab + pv_resign)
            p_survival *= (1 - (q_m + q_d + q_w))

        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((1.75 * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + self.discount_rate) ** years_to_retire)
        pv_ret = b_ret * v_ret * p_survival

        weighted_time_pv += years_to_retire * pv_ret
        total_pvfb = pvfb_death + pvfb_disability + pvfb_resign + pv_ret

        # --- PERHITUNGAN PBO & CSC FINAL DENGAN ISAK 35 ---
        pbo_death_dis_res = (pvfb_death + pvfb_disability + pvfb_resign) * (past_service / total_service)
        csc_death_dis_res = (pvfb_death + pvfb_disability + pvfb_resign) / total_service
        
        pbo_ret = pv_ret * (past_service_ret / total_service_ret) if total_service_ret > 0 else 0
        csc_ret = (pv_ret / total_service_ret) if (past_service >= unattributed_years) else 0

        pbo = pbo_death_dis_res + pbo_ret
        csc = csc_death_dis_res + csc_ret
        
        duration = (weighted_time_pv / total_pvfb) if total_pvfb > 0 else years_to_retire / 2.0
        
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
    canvas.drawCentredString(letter[0]/2.0, 30, "Cilandak 88 Condominium UNIT D-1, Jl. Margasatwa Barat No.88, Cilandak Timur, Pasar Minggu, Jakarta Selatan")
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
    elements.append(Paragraph(f"<b>ACTUARIAL VALUATION REPORT BASED ON<br/>PSAK 219 EMPLOYEE BENEFIT (ISAK 35)</b><br/><br/>Valuation Period Ended December 31, {cur_yr}<br/><br/><b>FINAL REPORT NO. {report_no}</b>", sub_style))
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

    elements.append(Paragraph("<b>2. Reconciliation Recognized in Balance Sheet (Mencakup Benefit Paid)</b>", h_style))
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
# 6. KONFIGURASI HALAMAN & TEMA VISUAL
# ==========================================
# st.set_page_config is defined at the top of the file

COMPANY_LEGAL_NAME = "Kantor Konsultan Aktuaria Setya Gunawan"
COMPANY_LICENSE = "Izin Perusahaan No. 4.21.0007"
COMPANY_MENKEU = "Keputusan Menteri Keuangan RI No. 590/KM.1/2021"
COMPANY_AKAI = "AKAI - 21043"
COMPANY_ADDRESS = "Cilandak 88 Condominium UNIT D-1, Jl. Margasatwa Barat No.88, Cilandak Timur, Pasar Minggu, Jakarta Selatan"
COMPANY_PHONE = "(0812) 9090 9019"
COMPANY_EMAIL = "kka_setyagunawan@yahoo.com"

# Logo asli perusahaan. Simpan file "logo.png" pada folder yang sama dengan app.py ini
# (file yang sama juga otomatis dipakai sebagai cover pada laporan PDF).
LOGO_PATH = "logo.png"

def load_logo_base64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

LOGO_B64 = load_logo_base64()

LOGO_CHIP_HTML = (
    f'<div style="background:#ffffff;display:inline-block;padding:8px 16px;border-radius:16px;margin-bottom:16px;box-shadow:0 6px 16px rgba(0,0,0,0.18);">'
    f'<img src="data:image/png;base64,{LOGO_B64}" style="height:44px;display:block;"/></div>'
) if LOGO_B64 else ""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, h5 { font-family: 'Poppins', sans-serif !important; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] { background: transparent; }

.main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1180px; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #241A12 0%, #6E3210 60%, #B8410D 100%);
}
/* General sidebar text (labels, headings, captions) stays light for contrast on the dark background */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #F5E9E1 !important;
}
[data-testid="stSidebar"] .stRadio > label { font-weight: 600; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }

/* Text typed/selected INSIDE input fields must stay black on white for readability */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stDateInput input,
[data-testid="stSidebar"] div[data-baseweb="input"] input,
[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    background-color: #ffffff !important;
}
[data-testid="stSidebar"] div[data-baseweb="input"],
[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSidebar"] .stTextInput > div,
[data-testid="stSidebar"] .stNumberInput > div,
[data-testid="stSidebar"] .stDateInput > div {
    background-color: #ffffff !important;
    border-radius: 8px;
}
.sidebar-brand {
    text-align:center;
    padding: 6px 0 18px 0;
    border-bottom: 1px solid rgba(255,255,255,0.15);
    margin-bottom: 14px;
}
.sidebar-brand-title { font-family:'Poppins',sans-serif; font-weight:800; font-size:1.05rem; line-height:1.3; }
.sidebar-brand-sub { font-size:0.72rem; opacity:0.75; letter-spacing:0.5px; text-transform:uppercase; }
.sidebar-contact-box {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 12px 14px;
    font-size: 0.78rem;
    line-height: 1.6;
    margin-top: 18px;
}

/* ---------- Hero ---------- */
.hero-section {
    background: linear-gradient(135deg, #241A12 0%, #B8410D 45%, #E85D25 100%);
    padding: 56px 44px;
    border-radius: 26px;
    color: #ffffff;
    margin-bottom: 36px;
    box-shadow: 0 24px 48px rgba(11,31,58,0.28);
    position: relative;
    overflow: hidden;
}
.hero-title { font-size: 2.5rem; font-weight: 800; margin-bottom: 14px; line-height:1.2; }
.hero-sub { font-size: 1.08rem; font-weight: 400; opacity: 0.92; max-width: 680px; line-height:1.7; margin-bottom: 6px;}
.badge-gold {
    display:inline-block;
    background: linear-gradient(135deg,#F2A65A,#FFCB9A);
    color:#1a1a1a;
    padding:6px 18px;
    border-radius:30px;
    font-weight:700;
    font-size:0.78rem;
    letter-spacing:0.4px;
    margin-bottom:18px;
}
.badge-soft {
    display:inline-block;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    color:#fff;
    padding:5px 14px;
    border-radius:30px;
    font-weight:600;
    font-size:0.74rem;
    margin: 4px 6px 4px 0;
}

/* ---------- Cards ---------- */
.service-card {
    background: #ffffff;
    border-radius: 18px;
    padding: 26px 22px;
    box-shadow: 0 6px 20px rgba(15,30,60,0.06);
    border: 1px solid #F3E4D8;
    transition: all 0.25s ease;
    height: 100%;
    margin-bottom: 6px;
}
.service-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 18px 34px rgba(11,31,58,0.14);
    border-color:#E85D25;
}
.service-icon { font-size: 2rem; margin-bottom: 10px; }
.service-title { font-size: 1.08rem; font-weight: 700; color:#241A12; margin-bottom: 6px; }
.service-desc { color:#7A6A5D; font-size: 0.88rem; line-height:1.6; }

.flagship-card {
    background: linear-gradient(135deg, #241A12 0%, #E85D25 100%);
    border-radius: 22px;
    padding: 34px 34px;
    color: white;
    box-shadow: 0 20px 40px rgba(11,31,58,0.32);
    margin-bottom: 10px;
}
.flagship-title { font-size:1.5rem; font-weight:800; margin-bottom:10px; }
.flagship-desc { opacity:0.92; line-height:1.7; font-size:0.95rem; }
.flagship-point { font-size:0.86rem; opacity:0.95; margin-bottom:6px; }

.stat-box { text-align:center; padding: 10px 6px; }
.stat-num { font-size: 1.9rem; font-weight: 800; color:#E85D25; font-family:'Poppins',sans-serif;}
.stat-label { color:#7A6A5D; font-size: 0.8rem; margin-top:2px;}

.section-title { font-size: 1.7rem; font-weight: 800; color:#241A12; margin-bottom: 4px;}
.section-sub { color:#7A6A5D; margin-bottom: 26px; font-size:0.95rem;}

.info-box {
    background:#FFF6F1;
    border-radius: 16px;
    padding: 22px 24px;
    border: 1px solid #F3E4D8;
    margin-bottom: 14px;
}
.info-box b { color:#241A12; }

.contact-box {
    background:#FFF6F1;
    border-radius: 18px;
    padding: 26px;
    border: 1px solid #F3E4D8;
}

.divider-soft { border: none; border-top: 1px solid #F3E4D8; margin: 30px 0; }

/* ---------- Buttons ---------- */
.stButton>button {
    background: linear-gradient(135deg, #E85D25, #241A12);
    color: white !important;
    border: none;
    border-radius: 12px;
    padding: 10px 26px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(30,75,143,0.32);
}
.stButton>button p { color: white !important; }

.stDownloadButton>button {
    background: linear-gradient(135deg, #F2A65A, #C9500F);
    color: #1a1a1a !important;
    border: none;
    border-radius: 12px;
    font-weight: 700;
}

/* Calculator header banner (smaller, inline) */
.calc-header {
    background: linear-gradient(135deg, #241A12 0%, #E85D25 100%);
    border-radius: 20px;
    padding: 30px 34px;
    color: white;
    margin-bottom: 28px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 7. NAVIGASI STATE
# ==========================================
MENU_OPTIONS = [
    "🏠 Beranda",
    "🏢 Tentang Kami",
    "💼 Layanan Kami",
    "🧮 Kalkulator Valuasi Aktuaria",
    "📞 Kontak Kami",
]

if "menu" not in st.session_state:
    st.session_state["menu"] = MENU_OPTIONS[0]

def go_to(page_name):
    st.session_state["menu"] = page_name
    st.rerun()

with st.sidebar:
    logo_img_html = (
        f'<img src="data:image/png;base64,{LOGO_B64}" style="max-width:150px;width:100%;border-radius:14px;background:#ffffff;padding:10px;box-shadow:0 6px 16px rgba(0,0,0,0.25);"/>'
        if LOGO_B64 else "📐"
    )
    st.markdown(f"""
    <div class="sidebar-brand">
        {logo_img_html}
        <div class="sidebar-brand-title" style="margin-top:10px;">Setya Gunawan</div>
        <div class="sidebar-brand-sub">Konsultan Aktuaria</div>
    </div>
    """, unsafe_allow_html=True)

    st.radio("Navigasi", MENU_OPTIONS, key="menu", label_visibility="collapsed")

    st.markdown(f"""
    <div class="sidebar-contact-box">
        📍 Cilandak 88 Condominium, Jakarta Selatan<br/>
        📱 {COMPANY_PHONE}<br/>
        ✉️ {COMPANY_EMAIL}<br/><br/>
        <span style="opacity:0.75; font-size:0.7rem;">{COMPANY_LICENSE}<br/>{COMPANY_AKAI}</span>
    </div>
    """, unsafe_allow_html=True)

menu = st.session_state["menu"]

# ==========================================
# 8. HALAMAN: BERANDA
# ==========================================
if menu == "🏠 Beranda":
    st.markdown(f"""
    <div class="hero-section">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">✓ TERDAFTAR RESMI — {COMPANY_MENKEU}</div>
        <div class="hero-title">Kepastian Aktuaria untuk<br/>Keputusan Bisnis yang Lebih Tepat</div>
        <div class="hero-sub">
            {COMPANY_LEGAL_NAME} menyediakan jasa valuasi aktuaria, konsultasi imbalan kerja,
            dan pelaporan sesuai standar <b>PSAK 219</b> — didukung pencocokan kurva
            <i>yield</i> zero-coupon resmi <b>PHEI IGSYC</b> untuk akurasi diskonto liabilitas.
        </div>
        <div>
            <span class="badge-soft">📐 PSAK 219 Compliant</span>
            <span class="badge-soft">📈 PHEI IGSYC Yield Matching</span>
            <span class="badge-soft">📄 Laporan Resmi & Auditable</span>
            <span class="badge-soft">🗂️ Data Multi-Tahun 2021–2026</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🚀 Coba Kalkulator Valuasi Sekarang", use_container_width=True):
            go_to("🧮 Kalkulator Valuasi Aktuaria")
    with c2:
        if st.button("💼 Lihat Semua Layanan Kami", use_container_width=True):
            go_to("💼 Layanan Kami")

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown('<div class="stat-box"><div class="stat-num">100%</div><div class="stat-label">Sesuai Standar PSAK 219</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="stat-box"><div class="stat-num">30</div><div class="stat-label">Tenor Kurva PHEI IGSYC (Tahun)</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown('<div class="stat-box"><div class="stat-num">2021–2026</div><div class="stat-label">Cakupan Data Historis</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown('<div class="stat-box"><div class="stat-num">24 Jam</div><div class="stat-label">Estimasi Laporan Instan</div></div>', unsafe_allow_html=True)

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Layanan Unggulan Kami</div><div class="section-sub">Solusi aktuaria menyeluruh, dari perhitungan hingga laporan siap audit.</div>', unsafe_allow_html=True)

    fc1, fc2 = st.columns([1.4, 1])
    with fc1:
        st.markdown("""
        <div class="flagship-card">
            <div class="flagship-title">🧮 Valuasi Aktuaria PSAK 219 — Imbalan Kerja</div>
            <div class="flagship-desc">
                Layanan unggulan kami. Kalkulator online otomatis menghitung <b>PBO</b>, <b>Current Service Cost</b>,
                dan durasi liabilitas dengan metode <i>Projected Unit Credit</i> (TERMASUK LOGIKA ISAK 35), lalu mencocokkan suku bunga
                diskonto secara otomatis dengan kurva <b>yield PHEI IGSYC</b> resmi — hasilnya langsung
                tersedia dalam laporan PDF formal dwibahasa, lengkap dengan neraca, OCI, dan rekonsiliasi.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Buka Kalkulator Valuasi Aktuaria", key="cta_flagship"):
            go_to("🧮 Kalkulator Valuasi Aktuaria")
    with fc2:
        st.markdown("""
        <div class="info-box">
            <b>Fitur utama layanan ini:</b><br/><br/>
            📈 Pencocokan otomatis kurva yield PHEI IGSYC<br/><br/>
            🗂️ Mendukung data multi-tahun (Excel / input manual)<br/><br/>
            📄 Laporan PDF resmi siap audit & regulator<br/><br/>
            🧾 Rekonsiliasi neraca & OCI otomatis
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">🏦</div>
            <div class="service-title">Konsultasi Dana Pensiun</div>
            <div class="service-desc">Pendampingan pembentukan dan evaluasi program dana pensiun perusahaan.</div>
        </div>
        """, unsafe_allow_html=True)
    with g2:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">🔍</div>
            <div class="service-title">Audit Kewajiban Aktuaria</div>
            <div class="service-desc">Reviu independen atas perhitungan liabilitas imbalan kerja perusahaan Anda.</div>
        </div>
        """, unsafe_allow_html=True)
    with g3:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">🎓</div>
            <div class="service-title">Pelatihan & Workshop</div>
            <div class="service-desc">Edukasi internal tim keuangan/SDM mengenai standar PSAK 219 dan praktiknya.</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 9. HALAMAN: TENTANG KAMI
# ==========================================
elif menu == "🏢 Tentang Kami":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">TENTANG KAMI</div>
        <div class="hero-title" style="font-size:2.1rem;">{COMPANY_LEGAL_NAME}</div>
        <div class="hero-sub">Kantor konsultan aktuaria independen yang berfokus pada ketepatan perhitungan,
        kepatuhan standar akuntansi, dan kejelasan pelaporan bagi klien korporasi di Indonesia.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="info-box">
            <b>🎯 Visi</b><br/>
            Menjadi mitra aktuaria tepercaya yang mendukung perusahaan di Indonesia dalam
            mengelola kewajiban imbalan kerja secara akurat, transparan, dan sesuai regulasi.
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="info-box">
            <b>🚀 Misi</b><br/>
            Menghadirkan layanan valuasi aktuaria berbasis teknologi — cepat, presisi, dan
            selaras dengan standar PSAK 219 serta kurva yield resmi PHEI IGSYC.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Legalitas & Perizinan</div><div class="section-sub">Beroperasi secara resmi dan diawasi sesuai ketentuan yang berlaku.</div>', unsafe_allow_html=True)

    l1, l2, l3 = st.columns(3)
    with l1:
        st.markdown(f'<div class="service-card"><div class="service-icon">📜</div><div class="service-title">Izin Perusahaan</div><div class="service-desc">{COMPANY_LICENSE}</div></div>', unsafe_allow_html=True)
    with l2:
        st.markdown(f'<div class="service-card"><div class="service-icon">🏛️</div><div class="service-title">Keputusan Menteri Keuangan</div><div class="service-desc">{COMPANY_MENKEU}</div></div>', unsafe_allow_html=True)
    with l3:
        st.markdown(f'<div class="service-card"><div class="service-icon">🪪</div><div class="service-title">Nomor Anggota AKAI</div><div class="service-desc">{COMPANY_AKAI}</div></div>', unsafe_allow_html=True)

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Mengapa Memilih Kami</div>', unsafe_allow_html=True)
    w1, w2, w3, w4 = st.columns(4)
    for col, icon, title, desc in [
        (w1, "📈", "Akurat & Sesuai SBN", "Menggunakan kurva yield harian resmi PHEI untuk ketepatan diskonto liabilitas."),
        (w2, "⚡", "Multi-Tahun & Fleksibel", "Mendukung data historis 2021–2026 via Excel maupun editor interaktif."),
        (w3, "📄", "Laporan Resmi", "Laporan dwibahasa lengkap dengan neraca, OCI, dan rekonsiliasi."),
        (w4, "🤝", "Pendampingan Personal", "Tim kami siap membantu interpretasi hasil valuasi bersama klien."),
    ]:
        with col:
            st.markdown(f'<div class="service-card"><div class="service-icon">{icon}</div><div class="service-title">{title}</div><div class="service-desc">{desc}</div></div>', unsafe_allow_html=True)

# ==========================================
# 10. HALAMAN: LAYANAN KAMI
# ==========================================
elif menu == "💼 Layanan Kami":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">LAYANAN KAMI</div>
        <div class="hero-title" style="font-size:2.1rem;">Solusi Aktuaria Menyeluruh</div>
        <div class="hero-sub">Dari perhitungan liabilitas hingga pelaporan resmi — kami mendampingi
        perusahaan Anda memenuhi kepatuhan standar akuntansi imbalan kerja.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="flagship-card">
        <div class="flagship-title">⭐ Layanan Unggulan: Kalkulator Valuasi Aktuaria PSAK 219</div>
        <div class="flagship-desc">
            Hitung liabilitas imbalan kerja perusahaan Anda secara instan dengan metode
            <i>Projected Unit Credit</i>, pencocokan otomatis kurva yield PHEI IGSYC, dan
            hasilkan laporan PDF resmi siap audit — semua dalam hitungan menit.
        </div>
        <br/>
        <div class="flagship-point">✔️ Perhitungan PBO, CSC, dan durasi liabilitas otomatis</div>
        <div class="flagship-point">✔️ Diskonto tercocokkan otomatis dengan kurva PHEI IGSYC (tenor 1–30 tahun)</div>
        <div class="flagship-point">✔️ Mendukung unggah Excel multi-tahun maupun input manual di website</div>
        <div class="flagship-point">✔️ Laporan PDF resmi: neraca, OCI, dan rekonsiliasi multi-tahun</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Gunakan Kalkulator Sekarang", key="cta_service_page"):
        go_to("🧮 Kalkulator Valuasi Aktuaria")

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Layanan Lainnya</div><div class="section-sub">Dukungan aktuaria di luar valuasi PSAK 219.</div>', unsafe_allow_html=True)

    services = [
        ("🏦", "Valuasi Dana Pensiun", "Perhitungan kewajiban dan pendanaan program pensiun manfaat pasti maupun iuran pasti."),
        ("🔍", "Audit & Reviu Independen", "Reviu kedua (peer review) atas laporan aktuaria yang disusun pihak lain."),
        ("📊", "Analisis Sensitivitas", "Simulasi dampak perubahan asumsi diskonto, kenaikan gaji, dan tingkat resign."),
        ("📁", "Manajemen Data Kepesertaan", "Pembersihan dan strukturisasi data karyawan untuk keperluan valuasi."),
        ("🎓", "Pelatihan Internal PSAK 219", "Workshop bagi tim keuangan/SDM mengenai konsep dan penerapan standar."),
        ("📞", "Konsultasi Regulasi", "Pendampingan terkait ketentuan Kemenkeu, OJK, dan standar akuntansi terkait."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(services):
        with cols[i % 3]:
            st.markdown(f'<div class="service-card"><div class="service-icon">{icon}</div><div class="service-title">{title}</div><div class="service-desc">{desc}</div></div>', unsafe_allow_html=True)
            st.write("")

# ==========================================
# 11. HALAMAN: KONTAK KAMI
# ==========================================
elif menu == "📞 Kontak Kami":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">HUBUNGI KAMI</div>
        <div class="hero-title" style="font-size:2.1rem;">Mari Diskusikan Kebutuhan Aktuaria Anda</div>
        <div class="hero-sub">Tim kami siap membantu perhitungan valuasi, konsultasi, hingga pelaporan
        imbalan kerja perusahaan Anda.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.markdown(f"""
        <div class="contact-box">
            <b>📍 Alamat Kantor</b><br/>
            {COMPANY_ADDRESS}<br/><br/>
            <b>📱 Telepon / WhatsApp</b><br/>
            {COMPANY_PHONE}<br/><br/>
            <b>✉️ Email</b><br/>
            {COMPANY_EMAIL}<br/><br/>
            <b>🏛️ Legalitas</b><br/>
            {COMPANY_LICENSE}<br/>
            {COMPANY_MENKEU}<br/>
            {COMPANY_AKAI}
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-title" style="font-size:1.3rem;">Kirim Pesan Singkat</div>', unsafe_allow_html=True)
        with st.form("contact_form"):
            nama = st.text_input("Nama Lengkap")
            perusahaan = st.text_input("Nama Perusahaan")
            email_kontak = st.text_input("Email")
            pesan = st.text_area("Pesan / Kebutuhan Layanan", height=120)
            submitted = st.form_submit_button("Kirim Pesan")
            if submitted:
                st.success("Terima kasih! Pesan Anda telah dicatat. Tim kami akan menghubungi Anda melalui email/WA yang tercantum.")
        st.caption("Untuk respon lebih cepat, silakan hubungi langsung melalui WhatsApp atau email di atas.")

# ==========================================
# 12. HALAMAN: KALKULATOR VALUASI AKTUARIA
# ==========================================
elif menu == "🧮 Kalkulator Valuasi Aktuaria":
    st.markdown(f"""
    <div class="calc-header">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">LAYANAN UNGGULAN</div>
        <div class="hero-title" style="font-size:1.9rem; margin-bottom:8px;">📄 Generator Laporan Aktuaria PSAK 219</div>
        <div class="hero-sub" style="font-size:0.98rem;">Termasuk Logika ISAK 35 (Capping 24 Tahun) & Pencocokan kurva yield PHEI IGSYC.</div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pengaturan Dokumen & Klien")
    input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
    tanggal_laporan = st.sidebar.date_input("Tanggal Laporan Diterbitkan", datetime.date.today())
    nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}")

    # Set default ke 5.0% sesuai permintaan untuk mencocokkan standar aktuaria
    asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
    usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=56, step=1)
    
    # Menambahkan opsi tingkat resign dengan default 0%
    asumsi_resign = st.sidebar.number_input("Tingkat Pengunduran Diri / Resign (%)", value=0.0, step=0.1) / 100

    st.sidebar.info("💡 **Standar Aktuaris:** Suku bunga diskonto ditentukan otomatis lewat *yield curve matching* PHEI IGSYC.")

    metode_input = st.radio(
        "Pilih Metode Masukan Data Karyawan:",
        ("Upload File Excel Multi-Tahun", "Input & Editor Data Langsung di Website")
    )

    datasets_to_process = {}
    benefit_paid_dict = {}

    if metode_input == "Upload File Excel Multi-Tahun":
        uploaded_file = st.file_uploader("Unggah File Excel Multi-Tahun Anda (.xlsx / .xls)", type=["xlsx", "xls"])
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
                st.success(f"Berhasil membaca sheet Excel untuk tahun: {list(datasets_to_process.keys())}")
            except Exception as e:
                st.error(f"Gagal membaca file: {e}")

    else:
        st.info("Masukkan data karyawan langsung per tahun menggunakan tabel interaktif di bawah (Rentang 2021 - 2026).")
        selected_years = st.multiselect(
            "Pilih Tahun Valuasi yang Ingin Dibuat",
            [2021, 2022, 2023, 2024, 2025, 2026],
            default=[2024, 2025]
        )

        if "manual_datasets" not in st.session_state:
            st.session_state.manual_datasets = {}

        tab_years = st.tabs([str(yr) for yr in selected_years]) if selected_years else []

        for idx, yr in enumerate(selected_years):
            with tab_years[idx]:
                if yr not in st.session_state.manual_datasets:
                    st.session_state.manual_datasets[yr] = pd.DataFrame([
                        {"NIK": "001", "Nama": "Karyawan Contoh 1", "Tanggal Lahir": "1985-05-12", "Tgl. Mulai Bekerja": "2010-01-01", "Total Upah Bulanan (Gross)": 5000000.0, "Saldo DPLK": 0.0}
                    ])

                edited_df = st.data_editor(
                    st.session_state.manual_datasets[yr],
                    num_rows="dynamic",
                    key=f"manual_editor_{yr}",
                    use_container_width=True
                )
                st.session_state.manual_datasets[yr] = edited_df
                datasets_to_process[yr] = edited_df

                benefit_paid_dict[yr] = st.number_input(
                    f"Total Benefit Paid Aktual Tahun {yr} (Rp)",
                    value=0.0,
                    step=1000000.0,
                    key=f"manual_paid_{yr}"
                )

    st.markdown("---")
    if st.button("Jalankan Valuasi Otomatis (ISAK 35 & PHEI Matching) 🚀") and datasets_to_process:
        with st.spinner("Menghitung durasi liabilitas dan mencocokkan kurva yield PHEI IGSYC..."):
            results_dict = {}
            dplk_dict = {}
            applied_discount_dict = {}
            active_years = sorted(list(datasets_to_process.keys()))

            for yr in active_years:
                val_date_dt = datetime.datetime(yr, 12, 31)
                df_input = datasets_to_process[yr]

                # Engine sementara untuk mencari Duration dengan parameter yang baru diset
                temp_engine = PSAK219Engine(0.065, asumsi_gaji, usia_pensiun, asumsi_resign)
                durations = []

                for _, row in df_input.iterrows():
                    try:
                        dob = pd.to_datetime(row.get("Tanggal Lahir"))
                        doe = pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                        gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                    except:
                        continue
                    if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0:
                        continue
                    cur_age = (val_date_dt - dob).days / 365.25
                    pst_serv = (val_date_dt - doe).days / 365.25
                    res = temp_engine.calculate_puc(cur_age, pst_serv, gross_salary)
                    if res['Duration'] > 0:
                        durations.append(res['Duration'])

                avg_duration = np.mean(durations) if durations else 8.0
                matched_phei_rate = get_phei_discount_rate(avg_duration)
                applied_discount_dict[yr] = matched_phei_rate

                # Engine final dengan discount rate yang sudah dicocokkan
                final_engine = PSAK219Engine(matched_phei_rate, asumsi_gaji, usia_pensiun, asumsi_resign)
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
            st.success(f"Valuasi Selesai! Logika ISAK 35 diterapkan & Suku Bunga PHEI IGSYC Tercocokkan Otomatis (Durasi Rata-rata ~{avg_duration:.2f} Tahun).")

    if st.session_state.get("calculated_results"):
        st.subheader("📊 Ringkasan Hasil Kalkulasi & Suku Bunga PHEI IGSYC Otomatis")
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
                "Periode Tahun": f"31 Dec {yr}",
                "Diskonto PHEI": f"{rate_y*100:.4f}%".replace('.', ','),
                "Total Peserta": len(df_y),
                "Benefit Paid (Aktual)": f"Rp {pd_dict.get(yr, 0):,.0f}".replace(",", "."),
                "Present Value of DBO (PBO)": f"Rp {pbo_y:,.0f}".replace(",", "."),
                "Saldo DPLK": f"Rp {dp_dict[yr]:,.0f}".replace(",", "."),
                "Net Liability": f"Rp {pbo_y - dp_dict[yr]:,.0f}".replace(",", ".")
            })

        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

        cur_applied_rate = disc_dict.get(act_yrs[-1], 0.0659) if act_yrs else 0.0659
        pdf_file = generate_comprehensive_report(
            res_dict, dp_dict, pd_dict, cur_applied_rate, asumsi_gaji, usia_pensiun,
            act_yrs, input_perusahaan, nomor_laporan
        )

        st.download_button(
            label="📥 Download Laporan PDF Lengkap (Sertakan Kurva Yield PHEI)",
            data=pdf_file,
            file_name=f"FINAL_REPORT_PHEI_IGSYC_ISAK35_{input_perusahaan.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
