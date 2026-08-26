import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re
import base64
import time

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# ==========================================
# KONFIGURASI HALAMAN 
# ==========================================
st.set_page_config(
    page_title="Setya Gunawan | Konsultan Aktuaria",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS & TEMA KORPORAT KAS
# ==========================================
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

.calc-header {
    background: linear-gradient(135deg, #241A12 0%, #E85D25 100%);
    border-radius: 20px;
    padding: 30px 34px;
    color: white;
    margin-bottom: 28px;
}
.qris-box { border: 2px dashed #E85D25; padding: 20px; border-radius: 15px; text-align: center; background-color: #FFF5F0; }
</style>
""", unsafe_allow_html=True)

if 'payment_verified' not in st.session_state:
    st.session_state.payment_verified = False

# ==========================================
# 1. DATABASE KURVA YIELD PHEI MULTI-TAHUN (2022 - 2025)
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

def get_phei_discount_rate(duration, valuation_year):
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
        lower_tenor = max([t for t in curve.keys() if t <= duration])
        upper_tenor = min([t for t in curve.keys() if t >= duration])
        if lower_tenor == upper_tenor:
            return curve[lower_tenor]
        r_low = curve[lower_tenor]
        r_high = curve[upper_tenor]
        return r_low + (r_high - r_low) * (duration - lower_tenor) / (upper_tenor - lower_tenor)

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
# 3. PARSER EXCEL PRESISI (DENGAN SAFE FLOAT)
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

    def safe_float(val, default=0.0):
        try:
            if pd.isna(val):
                return default
            cleaned = re.sub(r'[^0-9.\-]', '', str(val))
            if cleaned == '' or cleaned == '-':
                return default
            return float(cleaned)
        except:
            return default

    for idx in range(data_start_idx, len(df)):
        row = df.iloc[idx]
        nik = row.iloc[1] if len(row) > 1 else None
        nama = row.iloc[2] if len(row) > 2 else None
        dob = row.iloc[3] if len(row) > 3 else None
        doe = row.iloc[4] if len(row) > 4 else None
        
        salary = safe_float(row.iloc[5] if len(row) > 5 else 0.0, 0.0)
        dplk = safe_float(row.iloc[6] if len(row) > 6 else 0.0, 0.0)

        pension_mult = safe_float(row.iloc[12] if len(row) > 12 else 1.75, 1.75)
        disability_mult = safe_float(row.iloc[13] if len(row) > 13 else 2.0, 2.0)
        death_mult = safe_float(row.iloc[14] if len(row) > 14 else 2.0, 2.0)
        resign_mult = safe_float(row.iloc[15] if len(row) > 15 else 1.0, 1.0)

        if not pd.isna(nik) or not pd.isna(nama):
            clean_data.append({
                'NIK': str(nik).strip() if not pd.isna(nik) else '',
                'Nama': str(nama).strip() if not pd.isna(nama) else '',
                'Tanggal Lahir': dob,
                'Tgl. Mulai Bekerja': doe,
                'Total Upah Bulanan (Gross)': salary,
                'Saldo DPLK': dplk,
                'Pension_Mult': pension_mult,
                'Disability_Mult': disability_mult,
                'Death_Mult': death_mult,
                'Resign_Mult': resign_mult
            })

        if len(row) > 11:
            val_paid = safe_float(row.iloc[11], 0.0)
            if val_paid > 0:
                total_benefit_paid += val_paid

    return pd.DataFrame(clean_data), total_benefit_paid

# ==========================================
# 4. ENGINE AKTUARIA (PUC DENGAN ISAK 35 & FAKTOR EXCEL)
# ==========================================
class PSAK219Engine:
    def __init__(self, valuation_year, salary_increase, retirement_age, resign_rate=0.0):
        self.val_year = valuation_year
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

    def calculate_puc(self, current_age, past_service, current_salary, p_mult=1.75, d_mult=2.0, death_mult=2.0, r_mult=1.0):
        years_to_retire = self.ret_age - current_age
        if pd.isna(current_age) or pd.isna(past_service) or pd.isna(current_salary) or years_to_retire <= 0:
            return {'PBO': 0, 'CSC': 0, 'Duration': 0, 'PVFB': 0, 'Applied_Discount': 0, 'Future_Service': 0}

        discount_rate = get_phei_discount_rate(years_to_retire, self.val_year)
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

            b_death = salary_t * ((death_mult * up_t) + upmk_t)
            b_disab = salary_t * ((d_mult * up_t) + upmk_t)
            b_resign = salary_t * (r_mult * upmk_t) if service_t >= 3 else 0
            
            v = 1 / ((1 + discount_rate) ** (t + 1))

            cf_death = b_death * p_survival * q_m
            cf_disab = b_disab * p_survival * q_d
            cf_resign = b_resign * p_survival * q_w

            pv_death = cf_death * v
            pv_disab = cf_disab * v
            pv_resign = cf_resign * v
            
            pvfb_death += pv_death
            pvfb_disability += pv_disab
            pvfb_resign += pv_resign
            
            weighted_time_pv += (t + 1) * (pv_death + pv_disab + pv_resign)
            p_survival *= (1 - (q_m + q_d + q_w))

        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((p_mult * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + discount_rate) ** years_to_retire)
        pv_ret = b_ret * v_ret * p_survival

        weighted_time_pv += years_to_retire * pv_ret
        total_pvfb = pvfb_death + pvfb_disability + pvfb_resign + pv_ret

        # --- PERHITUNGAN PBO & CSC FINAL DENGAN ISAK 35 ---
        pbo_death_dis_res = (pvfb_death + pvfb_disability + pvfb_resign) * (past_service / total_service) if total_service > 0 else 0
        csc_death_dis_res = (pvfb_death + pvfb_disability + pvfb_resign) / total_service if total_service > 0 else 0
        
        pbo_ret = pv_ret * (past_service_ret / total_service_ret) if total_service_ret > 0 else 0
        csc_ret = (pv_ret / total_service_ret) if (past_service >= unattributed_years and total_service_ret > 0) else 0

        pbo = pbo_death_dis_res + pbo_ret
        csc = csc_death_dis_res + csc_ret
        
        duration = (weighted_time_pv / total_pvfb) if total_pvfb > 0 else years_to_retire / 2.0
        
        return {
            'PBO': pbo, 
            'CSC': csc, 
            'Duration': duration, 
            'PVFB': total_pvfb, 
            'Applied_Discount': discount_rate,
            'Future_Service': years_to_retire
        }

# ==========================================
# 5. GENERATOR PDF LAPORAN LENGKAP (LANDSCAPE DETAIL)
# ==========================================
def draw_footer_landscape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1)
    canvas.line(36, 45, landscape(letter)[0] - 36, 45) 
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(landscape(letter)[0]/2.0, 30, "Konsultan Aktuaria Setya Gunawan")
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(landscape(letter)[0]/2.0, 20, "Izin Perusahaan No. 4.21.0007 | Keputusan Menteri Keuangan RI No. 590/KM.1/2021 | AKAI - 21043")
    canvas.restoreState()

def generate_detailed_report(results_dict, salary_inc, ret_age, val_years, company_name, report_no):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=60)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=1, spaceBefore=10, spaceAfter=10)
    sub_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=11, textColor=colors.black, alignment=1, spaceAfter=20)
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#E85D25'), spaceBefore=15, spaceAfter=10)
    
    sorted_years = sorted(val_years, reverse=True)
    detail_tbl_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#439A86')), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'), 
        ('ALIGN', (1,1), (2,-1), 'LEFT'),   
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ])
    
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=3*inch, height=3*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        
    elements.append(Paragraph(f"<b>PT. {company_name.upper()}</b>", title_style))
    elements.append(Paragraph(f"<b>DETAIL CALCULATION OF ACTUARIAL VALUATION (PSAK 219 & ISAK 35)</b><br/>Report No: {report_no}", sub_style))
    
    for yr in sorted_years:
        elements.append(Paragraph(f"<b>Rincian Perhitungan Tingkat Individu per 31 Desember {yr}</b>", h_style))
        df_yr = results_dict[yr]
        if df_yr.empty: continue
            
        table_data = [["No", "NIK", "Nama", "Tgl Lahir", "Gaji Kotor", "Umur", "Past\nSvc", "Future\nSvc", "Diskonto\nPHEI", "PVFB", "PBO", "CSC"]]
        for i, row in df_yr.iterrows():
            dob_str = row['Tanggal Lahir'].strftime('%d-%m-%Y') if pd.notnull(row['Tanggal Lahir']) else "-"
            table_data.append([
                str(i + 1), str(row['NIK']), str(row['Name'])[:18], dob_str,
                fmt_num(row['Gross Salary']), fmt_num(row['Age Valuation'], 2),
                fmt_num(row['Past Service'], 2), fmt_num(row['Future_Service'], 2),
                f"{row['Applied_Discount']*100:.2f}%", fmt_num(row['PVFB']),
                fmt_num(row['PBO']), fmt_num(row['CSC'])
            ])
            
        table_data.append([
            "", "", "TOTAL", "", fmt_num(df_yr['Gross Salary'].sum()), "", "", "", "", 
            fmt_num(df_yr['PVFB'].sum()), fmt_num(df_yr['PBO'].sum()), fmt_num(df_yr['CSC'].sum())
        ])
        
        col_widths = [25, 60, 120, 60, 65, 35, 35, 40, 50, 75, 75, 70]
        t_detail = Table(table_data, colWidths=col_widths, repeatRows=1)
        
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
# 6. KONSTANTA PERUSAHAAN & LOGO
# ==========================================
COMPANY_LEGAL_NAME = "Kantor Konsultan Aktuaria Setya Gunawan"
COMPANY_LICENSE = "Izin Perusahaan No. 4.21.0007"
COMPANY_MENKEU = "Keputusan Menteri Keuangan RI No. 590/KM.1/2021"
COMPANY_AKAI = "AKAI - 21043"
COMPANY_ADDRESS = "Cilandak 88 Condominium UNIT D-1, Jl. Margasatwa Barat No.88, Cilandak Timur, Pasar Minggu, Jakarta Selatan"
COMPANY_PHONE = "(0812) 9090 9019"
COMPANY_EMAIL = "kka_setyagunawan@yahoo.com"

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

# ==========================================
# 7. NAVIGASI STATE SIDEBAR
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
            dan pelaporan sesuai standar <b>PSAK 219 & ISAK 35</b> — didukung pencocokan kurva
            <i>yield</i> zero-coupon resmi <b>PHEI</b> per tahun valuasi.
        </div>
        <div>
            <span class="badge-soft">📐 PSAK 219 & ISAK 35</span>
            <span class="badge-soft">📈 PHEI Yield Matching</span>
            <span class="badge-soft">📄 Rincian Individu & Auditable</span>
            <span class="badge-soft">🗂️ Data Multi-Tahun</span>
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
        st.markdown('<div class="stat-box"><div class="stat-num">100%</div><div class="stat-label">Sesuai PSAK 219 & ISAK 35</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="stat-box"><div class="stat-num">30</div><div class="stat-label">Tenor Kurva PHEI (Tahun)</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown('<div class="stat-box"><div class="stat-num">Detail</div><div class="stat-label">Tampil Per Karyawan di Web</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown('<div class="stat-box"><div class="stat-num">24 Jam</div><div class="stat-label">Estimasi Laporan Instan</div></div>', unsafe_allow_html=True)

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Layanan Unggulan Kami</div><div class="section-sub">Solusi aktuaria menyeluruh, dari perhitungan rinci hingga laporan siap audit.</div>', unsafe_allow_html=True)

    fc1, fc2 = st.columns([1.4, 1])
    with fc1:
        st.markdown("""
        <div class="flagship-card">
            <div class="flagship-title">🧮 Valuasi Aktuaria PSAK 219 — Imbalan Kerja</div>
            <div class="flagship-desc">
                Layanan unggulan kami dengan penerapan logika <b>ISAK 35 (Capping 24 Tahun)</b>. 
                Sistem menghitung PBO, CSC, dan PVFB secara rinci untuk setiap karyawan, 
                lalu mencocokkan suku bunga diskonto secara otomatis dengan kurva yield PHEI resmi per tahun valuasi.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Buka Kalkulator Valuasi Aktuaria", key="cta_flagship"):
            go_to("🧮 Kalkulator Valuasi Aktuaria")
    with fc2:
        st.markdown("""
        <div class="info-box">
            <b>Fitur utama sistem ini:</b><br/><br/>
            📈 Pencocokan kurva yield PHEI otomatis<br/><br/>
            ⚖️ Atribusi ISAK 35 (Capping 24 Tahun)<br/><br/>
            👥 **Tabel rincian tingkat individu langsung di web**<br/><br/>
            📄 Ekspor Laporan PDF Landscape Resmi
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
            selaras dengan standar PSAK 219, ISAK 35, serta kurva yield resmi PHEI.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Legalitas & Perizinan</div>', unsafe_allow_html=True)
    l1, l2, l3 = st.columns(3)
    with l1:
        st.markdown(f'<div class="service-card"><div class="service-icon">📜</div><div class="service-title">Izin Perusahaan</div><div class="service-desc">{COMPANY_LICENSE}</div></div>', unsafe_allow_html=True)
    with l2:
        st.markdown(f'<div class="service-card"><div class="service-icon">🏛️</div><div class="service-title">Keputusan Menteri Keuangan</div><div class="service-desc">{COMPANY_MENKEU}</div></div>', unsafe_allow_html=True)
    with l3:
        st.markdown(f'<div class="service-card"><div class="service-icon">🪪</div><div class="service-title">Nomor Anggota AKAI</div><div class="service-desc">{COMPANY_AKAI}</div></div>', unsafe_allow_html=True)

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
        <div class="flagship-title">⭐ Layanan Unggulan: Kalkulator Valuasi Aktuaria PSAK 219 & ISAK 35</div>
        <div class="flagship-desc">
            Hitung liabilitas imbalan kerja perusahaan Anda secara instan dengan metode
            <i>Projected Unit Credit</i>, penerapan ISAK 35, dan perincian data individu lengkap di web.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Gunakan Kalkulator Sekarang", key="cta_service_page"):
        go_to("🧮 Kalkulator Valuasi Aktuaria")

# ==========================================
# 11. HALAMAN: KONTAK KAMI
# ==========================================
elif menu == "📞 Kontak Kami":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">HUBUNGI KAMI</div>
        <div class="hero-title" style="font-size:2.1rem;">Mari Diskusikan Kebutuhan Aktuaria Anda</div>
        <div class="hero-sub">Tim kami siap membantu perhitungan valuasi, konsultasi, hingga pelaporan imbalan kerja Anda.</div>
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
            st.text_input("Nama Lengkap")
            st.text_input("Nama Perusahaan")
            st.text_input("Email")
            st.text_area("Pesan / Kebutuhan Layanan", height=120)
            submitted = st.form_submit_button("Kirim Pesan")
            if submitted:
                st.success("Terima kasih! Pesan Anda telah dicatat.")

# ==========================================
# 12. HALAMAN: KALKULATOR VALUASI AKTUARIA
# ==========================================
elif menu == "🧮 Kalkulator Valuasi Aktuaria":
    st.markdown(f"""
    <div class="calc-header">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">LAYANAN UNGGULAN</div>
        <div class="hero-title" style="font-size:1.9rem; margin-bottom:8px;">📄 Generator Laporan Aktuaria PSAK 219 (ISAK 35)</div>
        <div class="hero-sub" style="font-size:0.98rem;">Menampilkan detail perhitungan per karyawan di web, lengkap dengan kurva yield PHEI.</div>
    </div>
    """, unsafe_allow_html=True)

    # Sistem Pembayaran / Paywall QRIS
    if not st.session_state.payment_verified:
        st.warning("🔒 **Akses Terkunci:** Silakan lakukan verifikasi pembayaran untuk menggunakan Kalkulator Aktuaria.")
        st.markdown('<div class="qris-box">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#E85D25;'>Biaya Akses Valuasi</h3>", unsafe_allow_html=True)
        st.markdown("<h2>Rp 5.000.000,-</h2>", unsafe_allow_html=True)
        st.image("https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg", width=200)
        ref_code = st.text_input("Masukkan Kode Referensi Transfer:")
        if st.button("✅ Verifikasi Pembayaran", use_container_width=True):
            if ref_code:
                with st.spinner("Memeriksa status pembayaran..."):
                    time.sleep(1.5)
                    st.session_state.payment_verified = True
                    st.rerun()
            else:
                st.error("Silakan masukkan kode referensi transfer.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("🎉 Pembayaran Terverifikasi! Sistem Kalkulator ISAK 35 & Perincian Individu Aktif.")

        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Pengaturan Dokumen & Klien")
        input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
        tanggal_laporan = st.sidebar.date_input("Tanggal Laporan Diterbitkan", datetime.date.today())
        nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}")

        asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
        usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=56, step=1)
        asumsi_resign = st.sidebar.number_input("Tingkat Pengunduran Diri / Resign (%)", value=0.0, step=0.1) / 100

        st.sidebar.info("💡 **Standar Aktuaris:** Suku bunga diskonto ditentukan otomatis lewat *yield curve matching* PHEI sesuai tahun valuasi dan sisa masa kerja individual.")

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
        if st.button("Jalankan Valuasi Otomatis (ISAK 35 & Perincian Individu) 🚀") and datasets_to_process:
            with st.spinner("Menghitung perincian aktuaria per karyawan dengan logika ISAK 35 dan kurva PHEI..."):
                results_dict = {}
                dplk_dict = {}
                active_years = sorted(list(datasets_to_process.keys()))

                for yr in active_years:
                    val_date_dt = datetime.datetime(yr, 12, 31)
                    df_input = datasets_to_process[yr]

                    final_engine = PSAK219Engine(valuation_year=yr, salary_increase=asumsi_gaji, retirement_age=usia_pensiun, resign_rate=asumsi_resign)
                    hasil_valuasi = []
                    total_dplk_yr = 0.0

                    for _, row in df_input.iterrows():
                        try:
                            dob = pd.to_datetime(row.get("Tanggal Lahir"))
                            doe = pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                            gross_salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                            dplk_val = float(row.get("Saldo DPLK", 0.0) or 0.0)
                            
                            p_mult = float(row.get("Pension_Mult", 1.75))
                            d_mult = float(row.get("Disability_Mult", 2.0))
                            death_mult = float(row.get("Death_Mult", 2.0))
                            r_mult = float(row.get("Resign_Mult", 1.0))
                        except:
                            continue

                        if pd.isna(dob) or pd.isna(doe) or gross_salary <= 0:
                            continue

                        total_dplk_yr += dplk_val
                        current_age = (val_date_dt - dob).days / 365.25
                        past_service = (val_date_dt - doe).days / 365.25

                        kalkulasi = final_engine.calculate_puc(current_age, past_service, gross_salary, p_mult, d_mult, death_mult, r_mult)
                        hasil_valuasi.append({
                            "NIK": row.get("NIK", "N/A"), "Name": row.get("Nama", "Unknown"),
                            "Tanggal Lahir": dob,
                            "Age Valuation": current_age, "Past Service": past_service,
                            "Gross Salary": gross_salary, **kalkulasi
                        })

                    results_dict[yr] = pd.DataFrame(hasil_valuasi)
                    dplk_dict[yr] = total_dplk_yr

                st.session_state.results_dict = results_dict
                st.session_state.dplk_dict = dplk_dict
                st.session_state.paid_dict = benefit_paid_dict
                st.session_state.active_years = active_years
                st.session_state.calculated_results = True
                st.success("Valuasi Selesai! Perincian perhitungan tingkat individu kini ditampilkan di bawah.")

        if st.session_state.get("calculated_results"):
            res_dict = st.session_state.results_dict
            act_yrs = st.session_state.active_years

            st.markdown("---")
            st.subheader("👥 Rincian Perhitungan Tingkat Individu per Karyawan")
            st.write("Berikut adalah rincian kalkulasi aktuaria per orang (mirip kertas kerja aktuaris):")

            for yr in sorted(act_yrs, reverse=True):
                st.markdown(f"#### 📅 Data Valuasi Tahun {yr}")
                df_y = res_dict[yr]
                if df_y.empty:
                    st.info(f"Tidak ada data untuk tahun {yr}.")
                    continue

                df_display = df_y.copy()
                df_display['Tanggal Lahir'] = pd.to_datetime(df_display['Tanggal Lahir']).dt.strftime('%d-%m-%Y')
                df_display['Gross Salary'] = df_display['Gross Salary'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
                df_display['Age Valuation'] = df_display['Age Valuation'].apply(lambda x: f"{x:.2f}")
                df_display['Past Service'] = df_display['Past Service'].apply(lambda x: f"{x:.2f}")
                df_display['Future_Service'] = df_display['Future_Service'].apply(lambda x: f"{x:.2f}")
                df_display['Discount Rate'] = df_display['Applied_Discount'].apply(lambda x: f"{x*100:.2f}%")
                df_display['PVFB'] = df_display['PVFB'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_display['PBO'] = df_display['PBO'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_display['CSC'] = df_display['CSC'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                cols_to_show = ['NIK', 'Name', 'Tanggal Lahir', 'Gross Salary', 'Age Valuation', 'Past Service', 'Future_Service', 'Discount Rate', 'PVFB', 'PBO', 'CSC']
                st.dataframe(df_display[cols_to_show], use_container_width=True)

            st.markdown("---")
            st.subheader("📥 Unduh Laporan Resmi PDF")
            pdf_file = generate_detailed_report(
                res_dict, asumsi_gaji, usia_pensiun,
                act_yrs, input_perusahaan, nomor_laporan
            )

            st.download_button(
                label="📥 Download Kertas Kerja Detail (PDF Landscape)",
                data=pdf_file,
                file_name=f"DETAIL_REPORT_PSAK219_{input_perusahaan.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
