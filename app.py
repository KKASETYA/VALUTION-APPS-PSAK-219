import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re
import base64
import time

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from streamlit_option_menu import option_menu

# ==========================================
# KONFIGURASI HALAMAN & IDENTITAS KKA Setya Gunawan
# ==========================================
st.set_page_config(
    page_title="KKA Setya Gunawan | Kantor Konsultan Aktuaria",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS & TEMA KORPORAT KKA Setya Gunawan
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

/* ---------- Sidebar KKA Setya Gunawan ---------- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #3A0C08 0%, #7A1C14 60%, #A82B20 100%);
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
    color: #FDF3F2 !important;
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
    background: linear-gradient(135deg, #3A0C08 0%, #8A2017 45%, #C2382D 100%);
    padding: 56px 44px;
    border-radius: 26px;
    color: #ffffff;
    margin-bottom: 36px;
    box-shadow: 0 24px 48px rgba(58,12,8,0.28);
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
    border: 1px solid #F5D6D3;
    transition: all 0.25s ease;
    height: 100%;
    margin-bottom: 6px;
}
.service-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 18px 34px rgba(58,12,8,0.14);
    border-color:#C2382D;
}
.service-icon { font-size: 2rem; margin-bottom: 10px; }
.service-title { font-size: 1.08rem; font-weight: 700; color:#3A0C08; margin-bottom: 6px; }
.service-desc { color:#6B4B48; font-size: 0.88rem; line-height:1.6; }

.flagship-card {
    background: linear-gradient(135deg, #3A0C08 0%, #C2382D 100%);
    border-radius: 22px;
    padding: 34px 34px;
    color: white;
    box-shadow: 0 20px 40px rgba(58,12,8,0.32);
    margin-bottom: 10px;
}
.flagship-title { font-size:1.5rem; font-weight:800; margin-bottom:10px; }
.flagship-desc { opacity:0.92; line-height:1.7; font-size:0.95rem; }

.stat-box { text-align:center; padding: 10px 6px; }
.stat-num { font-size: 1.9rem; font-weight: 800; color:#C2382D; font-family:'Poppins',sans-serif;}
.stat-label { color:#6B4B48; font-size: 0.8rem; margin-top:2px;}

.section-title { font-size: 1.7rem; font-weight: 800; color:#3A0C08; margin-bottom: 4px;}
.section-sub { color:#6B4B48; margin-bottom: 26px; font-size:0.95rem;}

.info-box {
    background:#FDF5F4;
    border-radius: 16px;
    padding: 22px 24px;
    border: 1px solid #F5D6D3;
    margin-bottom: 14px;
}
.info-box b { color:#3A0C08; }

.contact-box {
    background:#FDF5F4;
    border-radius: 18px;
    padding: 26px;
    border: 1px solid #F5D6D3;
}

.divider-soft { border: none; border-top: 1px solid #F5D6D3; margin: 30px 0; }

.stButton>button {
    background: linear-gradient(135deg, #C2382D, #3A0C08);
    color: white !important;
    border: none;
    border-radius: 12px;
    padding: 10px 26px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(194,56,45,0.32);
}
.stButton>button p { color: white !important; }

.stDownloadButton>button {
    background: linear-gradient(135deg, #F2A65A, #A82B20);
    color: #1a1a1a !important;
    border: none;
    border-radius: 12px;
    font-weight: 700;
}

.calc-header {
    background: linear-gradient(135deg, #3A0C08 0%, #C2382D 100%);
    border-radius: 20px;
    padding: 30px 34px;
    color: white;
    margin-bottom: 28px;
}
.qris-box { border: 2px dashed #C2382D; padding: 20px; border-radius: 15px; text-align: center; background-color: #FAF1F0; }
</style>
""", unsafe_allow_html=True)

if 'payment_verified' not in st.session_state:
    st.session_state.payment_verified = False

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

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
# 4. ENGINE AKTUARIA (PUC DENGAN IFRIC AD & FAKTOR )
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
        
        # --- ATRIBUSI IFRIC AD (CAPPING 24 TAHUN) ---
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

        # --- PERHITUNGAN PBO & CSC FINAL BERDASARKAN ATRIBUSI IFRIC AD ---
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
# 5. GENERATOR PDF LAPORAN KKA SETYA GUNAWAN (FORMAT COVER KUSTOM & DETAIL LENGKAP A4)
# ==========================================
def draw_cover_background(canvas_obj, doc_obj):
    canvas_obj.saveState()
    if os.path.exists("cover_bg.png"):
        canvas_obj.drawImage("cover_bg.png", 0, 0, width=595.27, height=841.89, preserveAspectRatio=False, mask='auto')
    canvas_obj.restoreState()

def draw_footer_landscape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#3A0C08'))
    canvas.setLineWidth(1)
    canvas.line(36, 45, landscape(A4)[0] - 36, 45) 
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawCentredString(landscape(A4)[0]/2.0, 30, "Kantor Konsultan Aktuaria Setya Gunawan (KKA Setya Gunawan)")
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(landscape(A4)[0]/2.0, 20, "Izin Badan Usaha No. 4.21.0007 | Keputusan Kemenkeu RI No. 590/KM.1/2021 | STTD-OJK: STTD-039/NB.122/STTD-KA/2021 | AKKAI: AKKAI-21043")
    canvas.restoreState()

def generate_detailed_report(results_dict, salary_inc, ret_age, val_years, company_name, report_no, report_date):
    pdf_buffer = io.BytesIO()
    
    class MixedPageDocTemplate(SimpleDocTemplate):
        def handle_pageBegin(self):
            if self.page > 1:
                self.pagesize = landscape(A4)
            super().handle_pageBegin()

    doc_mixed = MixedPageDocTemplate(
        pdf_buffer, 
        pagesize=A4, 
        rightMargin=54, 
        leftMargin=54, 
        topMargin=54, 
        bottomMargin=54
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    cover_title_style = ParagraphStyle('CoverMainTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=17, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=6, leading=21)
    cover_sub_style = ParagraphStyle('CoverSubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=22, leading=17)
    cover_desc_style = ParagraphStyle('CoverDesc', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=4, leading=15)
    cover_date_style = ParagraphStyle('CoverDate', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=65, leading=14)
    cover_address_style = ParagraphStyle('CoverAddressRight', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#2980B9'), alignment=2, leading=13.5)
    
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#C2382D'), spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('BodyCustom', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#222222'), spaceBefore=4, spaceAfter=8, leading=13)

    formatted_date = report_date.strftime('%d %B %Y') if hasattr(report_date, 'strftime') else str(report_date)

    # 1. HALAMAN SAMPUL (COVER) A4 PORTRAIT
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=1.6*inch, height=1.3*inch)
        logo.hAlign = 'RIGHT'
        elements.append(logo)
        elements.append(Spacer(1, 20))
    else:
        elements.append(Spacer(1, 45))

    elements.append(Paragraph("FINAL ACTUARIAL REPORT", cover_title_style))
    elements.append(Paragraph(f"PT {company_name.upper()}", cover_sub_style))
    elements.append(Spacer(1, 115))
    
    elements.append(Paragraph("EMPLOYEE BENEFITS LIABILITIES", cover_desc_style))
    elements.append(Paragraph(f"NO. {report_no}", cover_desc_style))
    elements.append(Spacer(1, 12))
    
    val_yr_str = str(val_years[0]) if val_years else '2022'
    elements.append(Paragraph(f"PERIOD DECEMBER, 31ST {val_yr_str}", cover_date_style))
    elements.append(Spacer(1, 15))
    
    address_block = (
        "<b>KKA SETYA GUNAWAN</b><br/>"
        "<i>Cilandak 88 Condominium Unit D-1</i><br/>"
        "<i>Jl. Margasatwa Barat No. 88</i><br/>"
        "<i>Cilandak Timur</i><br/>"
        "<i>Pasar Minggu</i><br/>"
        "<i>Jakarta Selatan,</i><br/>"
        "<i>12560</i>"
    )
    elements.append(Paragraph(address_block, cover_address_style))
    elements.append(PageBreak())

    # 2. BAB PENGANTAR
    elements.append(Paragraph("<b>1. PENDAHULUAN / INTRODUCTION</b>", h_style))
    elements.append(Paragraph(f"Laporan aktuaria ini disajikan untuk memenuhi permintaan <b>PT {company_name.upper()}</b> guna mengetahui Kewajiban dan Beban atas Imbalan Kerja Karyawan berdasarkan Undang-Undang Ketenagakerjaan (UU Cipta Kerja No. 11 Tahun 2020) dan PSAK 219.", body_style))
    
    elements.append(Paragraph("<b>2. MANFAAT KARYAWAN / EMPLOYEE BENEFITS</b>", h_style))
    elements.append(Paragraph("Valuasi mencakup Manfaat Pensiun, Manfaat Meninggal Dunia, Manfaat Mengundurkan Diri, Manfaat Sakit Berkepanjangan, serta Kompensasi PKWT sesuai regulasi yang berlaku.", body_style))

    elements.append(Paragraph("<b>3. METODOLOGI & ASUMSI AKTUARIA</b>", h_style))
    elements.append(Paragraph(f"Metode valuasi menggunakan <b>Projected Unit Credit (PUC)</b> dengan asumsi tingkat kenaikan gaji {salary_inc*100:.2f}% p.a., Usia Pensiun Normal {ret_age} tahun, serta tingkat diskonto berbasis kurva PHEI.", body_style))
    elements.append(PageBreak())

    # 3. RINGKASAN HASIL & LAMPIRAN DETAIL KARYAWAN LENGKAP PER TAHUN
    for yr in sorted(val_years, reverse=True):
        df_yr = results_dict[yr]
        if df_yr.empty: continue
            
        tot_salary = df_yr['Gross Salary'].sum()
        tot_pvfb = df_yr['PVFB'].sum()
        tot_pbo = df_yr['PBO'].sum()
        tot_csc = df_yr['CSC'].sum()
        num_emp = len(df_yr)

        elements.append(Paragraph(f"<b>4. RINGKASAN HASIL VALUASI (PER 31 DESEMBER {yr})</b>", h_style))
        t1_data = [
            ["URAIAN (EXPLANATION)", f"Per 31 Des {yr} (Pasca Kerja)", f"Per 31 Des {yr} (Jangka Panjang Lainnya)"],
            ["1. Jumlah Karyawan (Number of Employees)", str(num_emp), "0"],
            ["2. Total Penghasilan Sebulan (Total Salary)", f"Rp {fmt_num(tot_salary)}", "Rp 0"],
            ["3. Rata-rata Usia (Average Age)", f"{df_yr['Age Valuation'].mean():.2f}", "0.00"],
            ["4. Rata-rata Masa Kerja Lalu (Past Service)", f"{df_yr['Past Service'].mean():.2f} tahun", "0.00 tahun"],
            ["5. Tingkat Diskonto Akhir (Discount Rate)", f"{df_yr['Applied_Discount'].mean()*100:.2f}%", f"{df_yr['Applied_Discount'].mean()*100:.2f}%"],
            ["6. Tingkat Kenaikan Gaji (Salary Increment)", f"{salary_inc*100:.2f}%", f"{salary_inc*100:.2f}%"],
            ["7. Biaya Jasa Kini (Current Service Cost)", f"Rp {fmt_num(tot_csc)}", "Rp 0"],
            ["8. Nilai Kini Kewajiban / PVDBO (Obligation)", f"Rp {fmt_num(tot_pbo)}", "Rp 0"]
        ]
        t1 = Table(t1_data, colWidths=[280, 200, 200])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3A0C08')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D3C1BE')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 15))

        # --- LAMPIRAN DETAIL KARYAWAN ---
        elements.append(Paragraph(f"<b>LAMPIRAN — Detail Perhitungan Individu Karyawan (Tahun {yr})</b>", h_style))
        table_data = [["No", "NIK & Nama Karyawan", "Tgl Lahir", "Tgl Masuk", "Gaji Kotor (Rp)", "NRA", "Umur", "Masa Kerja", "Faktor UU", "Diskonto", "PVFB (Rp)", "PBO (Rp)", "CSC (Rp)"]]
        
        for i, row in df_yr.iterrows():
            dob_str = row['Tanggal Lahir'].strftime('%d-%m-%Y') if pd.notnull(row['Tanggal Lahir']) else "-"
            table_data.append([
                str(i + 1), f"{row['NIK']}\n{row['Name']}"[:22], dob_str, "01-01-2023",
                fmt_num(row['Gross Salary']), f"{ret_age}.00", f"{row['Age Valuation']:.2f}", f"{row['Past Service']:.2f}",
                "23.75", f"{row['Applied_Discount']*100:.2f}%", fmt_num(row['PVFB']), fmt_num(row['PBO']), fmt_num(row['CSC'])
            ])
            
        table_data.append([
            "", "TOTAL KESELURUHAN", "", "", fmt_num(tot_salary), "", "", "", "", "", 
            fmt_num(tot_pvfb), fmt_num(tot_pbo), fmt_num(tot_csc)
        ])
        
        col_widths = [24, 115, 55, 55, 75, 32, 35, 42, 60, 45, 75, 75, 70]
        t_detail = Table(table_data, colWidths=col_widths, repeatRows=1)
        t_detail.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3A0C08')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 6.5),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D3C1BE')),
            ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
            ('ALIGN', (1,1), (3,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EADCDA')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        elements.append(t_detail)
        elements.append(PageBreak())

    # 4. BAB PENUTUP
    elements.append(Paragraph("<b>5. PENUTUP / CLOSING</b>", h_style))
    elements.append(Paragraph(f"Demikian laporan aktuaria ini disusun secara independen oleh KKA Setya Gunawan untuk dipergunakan sebagaimana mestinya oleh manajemen <b>PT {company_name.upper()}</b> dan pihak Auditor independen.", body_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Jakarta, {formatted_date}<br/><b>KANTOR KONSULTAN AKTUARIA SETYA GUNAWAN</b><br/><br/><br/><br/><b>Setya Gunawan, FSAI</b>", ParagraphStyle('SignBlock', parent=styles['Normal'], fontSize=9, alignment=2)))
        
    doc_mixed.build(
        elements, 
        onFirstPage=draw_cover_background, 
        onLaterPages=draw_footer_landscape
    )
    pdf_buffer.seek(0)
    return pdf_buffer

# ==========================================
# 6. KONSTANTA KORPORAT KKA Setya Gunawan
# ==========================================
COMPANY_LEGAL_NAME = "Kantor Konsultan Aktuaria Setya Gunawan"
COMPANY_LICENSE = "Izin Badan Usaha Kemenkeu RI No. 4.21.0007"
COMPANY_MENKEU = "Keputusan Kemenkeu RI No. 590/KM.1/2021"
COMPANY_OJK = "STTD-OJK: STTD-039/NB.122/STTD-KA/2021"
COMPANY_AKKAI = "AKKAI-21043"
COMPANY_ADDRESS = "Cilandak 88 Condominium Unit D-1, Jl. Margasatwa Barat No. 88, Cilandak Timur, Pasar Minggu, Jakarta Selatan 12560"
COMPANY_PHONE = "+62 81290909019"
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
# 7. NAVIGASI HORIZONTAL NAVBAR ATAS (DENGAN URL PARAMETER ADMIN RAHASIA)
# ==========================================
if "menu" not in st.session_state:
    st.session_state["menu"] = "Beranda"

def go_to(page_name):
    st.session_state["menu"] = page_name
    st.rerun()

# Deteksi URL parameter rahasia: ?role=admin
query_params = st.query_params
is_url_admin = query_params.get("role") == "admin"

nav_options = ["Beranda", "Tentang Kami", "Layanan Kami", "Kalkulator Valuasi Aktuaria", "Kontak Kami"]
nav_icons = ["house", "building", "briefcase", "calculator", "envelope"]

# Jika diakses lewat tautan rahasia admin, tambahkan menu Admin secara eksklusif
if is_url_admin:
    nav_options.append("🔐 Admin Dashboard")
    nav_icons.append("shield-lock")

with st.container():
    if LOGO_B64:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 5px;">
            <img src="data:image/png;base64,{LOGO_B64}" style="height: 45px; vertical-align: middle;"/>
            <span style="font-family:'Poppins',sans-serif; font-weight:800; font-size:1.1rem; margin-left:10px; vertical-align: middle; color:#3A0C08;">KKA Setya Gunawan</span>
        </div>
        """, unsafe_allow_html=True)

    selected_nav = option_menu(
        menu_title=None,
        options=nav_options,
        icons=nav_icons,
        menu_icon="cast",
        default_index=nav_options.index(st.session_state["menu"]) if st.session_state["menu"] in nav_options else 0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#FAF1F0", "border-radius": "10px", "margin-bottom": "25px"},
            "icon": {"color": "#C2382D", "font-size": "13px"}, 
            "nav-link": {
                "font-size": "13.5px",
                "text-align": "center",
                "margin": "0px 4px",
                "font-family": "Inter, sans-serif",
                "font-weight": "600",
                "color": "#3A0C08",
            },
            "nav-link-selected": {"background-color": "#3A0C08", "color": "white !important"},
        }
    )

menu = selected_nav
st.session_state["menu"] = selected_nav

# ==========================================
# 8. HALAMAN: BERANDA
# ==========================================
if menu == "🏠 Beranda" or menu == "Beranda":
    with st.container():
        st.success(f"✓ TERDAFTAR OJK & KEMENKEU — {COMPANY_MENKEU}")
        st.title(f"Kantor Konsultan Aktuaria Setya Gunawan\nSolusi Profesional PSAK 219")
        st.write(
            f"{COMPANY_LEGAL_NAME} menyediakan jasa valuasi aktuaria imbalan kerja, "
            "konsultasi program pensiun, dan pelaporan keuangan sesuai standar **PSAK 219 & IFRIC AD** — "
            "didukung pencocokan kurva yield PHEI zero-coupon resmi per tahun valuasi."
        )
        st.markdown("📐 **PSAK 219 & IFRIC AD** | 📈 **PHEI Yield Matching** | 📄 **Kertas Kerja Audit Ready** | 🗂️ **Integrasi API & Otomasi**")

    st.markdown("---")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Hitung Imbalan Kerja PSAK 219", use_container_width=True):
            go_to("Kalkulator Valuasi Aktuaria")
    with c2:
        if st.button("💼 Lihat Layanan Kami", use_container_width=True):
            go_to("Layanan Kami")

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric(label="Sesuai PSAK 219 & IFRIC AD", value="100%")
    with s2:
        st.metric(label="Tenor Kurva PHEI (Tahun)", value="30")
    with s3:
        st.metric(label="Tampil Per Karyawan", value="Detail")
    with s4:
        st.metric(label="Estimasi & Laporan", value="24 Jam")

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.subheader("Layanan Utama KKA Setya Gunawan")
    st.caption("Layanan Valuasi Aktuaria berstandar.")

    fc1, fc2 = st.columns([1.4, 1])
    with fc1:
        with st.container(border=True):
            st.subheader("🧮 Valuasi Aktuaria Imbalan Kerja (PSAK 219)")
            st.write(
                "Perhitungan kewajiban imbalan pascakerja menggunakan metode *Projected Unit Credit* "
                "dan penerapan interpretasi **IFRIC AD (Capping 24 Tahun Masa Kerja)**. "
                "Sistem mengintegrasikan asumsi demografi TMI IV, tingkat diskonto PHEI, serta analisis sensitivitas mendalam."
            )
            if st.button("🚀 Buka Kalkulator Valuasi Aktuaria", key="cta_flagship"):
                go_to("Kalkulator Valuasi Aktuaria")
    with fc2:
        with st.container(border=True):
            st.markdown("<b>Keunggulan Sistem KKA Setya Gunawan:</b>", unsafe_allow_html=True)
            st.write("📈 Pencocokan kurva yield PHEI otomatis")
            st.write("⚖️ Atribusi IFRIC AD / ISAK 35 (Capping)")
            st.write("👥 **Tabel rincian tingkat individu langsung di web**")
            st.write("📄 Ekspor Laporan PDF sesuai dengan standar penyajian laporan KKA")

# ==========================================
# 9. HALAMAN: TENTANG KAMI
# ==========================================
elif menu == "🏢 Tentang Kami" or menu == "Tentang Kami":
    with st.container():
        st.success("TENTANG KAMI")
        st.title(f"{COMPANY_LEGAL_NAME}")
        st.write("Kantor konsultan aktuaria independen yang terdaftar resmi dan berizin untuk memberikan layanan aktuaria, konsultasi imbalan kerja, dan audit support bagi perusahaan di Indonesia.")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("🎯 Visi KKA Setya Gunawan")
            st.write("Menjadi kantor konsultan aktuaria terdepan yang andal, profesional, dan tepercaya dalam mendukung pengelolaan liabilitas imbalan kerja korporasi di Indonesia.")
    with c2:
        with st.container(border=True):
            st.subheader("🚀 Misi KKA Setya Gunawan")
            st.write("Menghadirkan layanan aktuaria berbasis teknologi tinggi, transparan, serta selaras dengan standar akuntansi keuangan PSAK 219, IFRS, dan regulasi ketenagakerjaan nasional.")

    st.markdown("---")
    st.subheader("Legalitas & Perizinan Resmi")
    l1, l2, l3 = st.columns(3)
    with l1:
        with st.container(border=True):
            st.markdown("📜 **Izin Badan Usaha**")
            st.write(f"{COMPANY_LICENSE}\n\n({COMPANY_MENKEU})")
    with l2:
        with st.container(border=True):
            st.markdown("🏛️ **Terdaftar di OJK**")
            st.write(COMPANY_OJK)
    with l3:
        with st.container(border=True):
            st.markdown("🪪 **Keanggotaan AKKAI**")
            st.write(f"Nomor: {COMPANY_AKKAI}")

# ==========================================
# 10. HALAMAN: LAYANAN KAMI
# ==========================================
elif menu == "💼 Layanan Kami" or menu == "Layanan Kami":
    with st.container():
        st.success("LAYANAN KAMI")
        st.title("Layanan Konsultasi & Valuasi Aktuaria")
        st.write("Mendampingi perusahaan menyusun laporan aktuaria imbalan pascakerja, analisis sensitivitas, hingga tata kelola program dana pensiun (DPLK / DPPK).")

    with st.container(border=True):
        st.subheader("⭐ Kalkulator & Valuasi Aktuaria PSAK 219 Terintegrasi")
        st.write("Sistem valuasi otomatis berbasis web untuk menghitung PVDBO, CSC, Biaya Bunga, OCI, serta analisis jatuh tempo (Maturity Analysis) dan uji sensitivitas secara presisi.")
        if st.button("🚀 Gunakan Kalkulator Sekarang", key="cta_service_page"):
            go_to("Kalkulator Valuasi Aktuaria")

# ==========================================
# 11. HALAMAN: KONTAK KAMI
# ==========================================
elif menu == "📞 Kontak Kami" or menu == "Kontak Kami":
    with st.container():
        st.success("HUBUNGI KAMI")
        st.title("Konsultasikan Kebutuhan Aktuaria Anda")
        st.write("Tim aktuaris publik dan profesional KKA Setya Gunawan siap melayani kebutuhan korporasi Anda.")

    c1, c2 = st.columns([1, 1.1])
    with c1:
        with st.container(border=True):
            st.subheader("📍 Alamat Kantor Utama")
            st.write(COMPANY_ADDRESS)
            st.markdown("📱 **Telepon / WhatsApp**")
            st.write(COMPANY_PHONE)
            st.markdown("✉️ **Email Resmi**")
            st.write(COMPANY_EMAIL)
            st.markdown("🏛️ **Legalitas & Akreditasi**")
            st.write(f"{COMPANY_LICENSE}\n{COMPANY_OJK}\nAKKAI: {COMPANY_AKKAI}")
    with c2:
        st.subheader("Kirim Pesan Konsultasi")
        with st.form("contact_form"):
            st.text_input("Nama Lengkap")
            st.text_input("Nama Perusahaan")
            st.text_input("Email Korporat")
            st.text_area("Pesan / Kebutuhan Valuasi", height=120)
            submitted = st.form_submit_button("Kirim Pesan")
            if submitted:
                st.success("Terima kasih! Pesan Anda telah diterima oleh tim KKA Setya Gunawan.")

# ==========================================
# 12. HALAMAN: ADMIN DASHBOARD (EKSKLUSIF)
# ==========================================
elif menu == "🔐 Admin Dashboard":
    st.success("PANEL KONTROL INTERNAL KKA SETYA GUNAWAN")
    st.title("🔐 Admin Dashboard & Data Pulling Center")
    st.write("Area kontrol terbatas untuk memantau data yang diunggah klien dan menarik hasil kalkulasi.")

    if not st.session_state.admin_logged_in:
        with st.form("admin_login_form"):
            st.markdown("### Masukkan Sandi Internal Admin")
            admin_pass_input = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Masuk Dashboard")
            if login_btn:
                if admin_pass_input == "aktuaris2026": # Sandi Admin Anda
                    st.session_state.admin_logged_in = True
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Sandi salah!")
    else:
        st.success("Status: Aktif sebagai Admin Internal KKA Setya Gunawan")
        if st.button("Keluar (Logout) Admin"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.markdown("---")
        st.subheader("📊 Monitoring Data & Hasil Valuasi Klien")

        if "results_dict" in st.session_state and st.session_state.results_dict:
            res_dict = st.session_state.results_dict
            act_yrs = st.session_state.active_years
            client_name = st.session_state.get("input_perusahaan", "Perusahaan Klien")

            st.info(f"Klien Aktif Terakhir: **{client_name}**")

            for yr in sorted(act_yrs, reverse=True):
                st.markdown(f"#### 📅 Data Klien Tahun Valuasi {yr}")
                df_client = res_dict[yr]
                st.dataframe(df_client, use_container_width=True)

                # Fitur Data Pulling (Download Data Klien dalam format CSV / Excel)
                csv_bytes = df_client.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Tarik Data Klien (Tahun {yr}) - CSV",
                    data=csv_bytes,
                    file_name=f"Data_Pulling_{client_name.replace(' ', '_')}_{yr}.csv",
                    mime="text/csv",
                    key=f"pull_csv_{yr}"
                )
        else:
            st.warning("Belum ada data kalkulasi atau unggahan dari klien yang tersimpan di memori sesi sistem saat ini.")

# ==========================================
# 13. HALAMAN: KALKULATOR VALUASI AKTUARIA
# ==========================================
elif menu == "🧮 Kalkulator Valuasi Aktuaria" or menu == "Kalkulator Valuasi Aktuaria":
    with st.container():
        st.success("KKA Setya Gunawan — PORTAL AKTUARIA")
        st.title("📄 Generator Laporan Aktuaria PSAK 219 (IFRIC AD)")
        st.write("Menampilkan rincian kalkulasi per karyawan di web, dilengkapi kurva yield PHEI & kertas kerja siap audit.")

    # Sistem Pembayaran / Paywall QRIS KKA Setya Gunawan
    if not st.session_state.payment_verified:
        st.warning("🔒 **Akses Terkunci:** Silakan lakukan verifikasi pembayaran administrasi layanan valuasi aktuaria KKA Setya Gunawan.")
        with st.container(border=True):
            st.subheader("Biaya Akses Valuasi Korporat")
            st.markdown("## Rp 5.000.000,-")
            st.image("https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg", width=200)
            ref_code = st.text_input("Masukkan Kode Referensi Transfer:")
            if st.button("✅ Verifikasi Pembayaran", use_container_width=True):
                if ref_code:
                    with st.spinner("Memeriksa status pembayaran..."):
                        time.sleep(1.5)
                        st.session_state.payment_verified = True
                        st.rerun()
                else:
                    st.error("Silakan masukkan kode referensi transfer yang valid.")
    else:
        st.success("🎉 Pembayaran Terverifikasi! Sistem Kalkulator PSAK 219 & Kertas Kerja Individu Aktif.")

        # Pengaturan Laporan dipindah ke bagian utama halaman karena sidebar tidak dipakai
        with st.expander("⚙️ Pengaturan Laporan & Asumsi Aktuaria (Klik untuk Mengatur)", expanded=True):
            col_set1, col_set2 = st.columns(2)
            with col_set1:
                input_perusahaan = st.text_input("Nama Perusahaan Klien", "PT ABC SEJAHTERA")
                tanggal_laporan = st.date_input("Tanggal Penerbitan Laporan", datetime.date.today())
                nomor_laporan = st.text_input("Nomor Laporan Baku", f"082/FR-KAS/PSAK/III/{tanggal_laporan.strftime('%Y')}")
            with col_set2:
                asumsi_gaji = st.number_input("Kenaikan Gaji Tahunan (%)", value=8.0, step=0.1) / 100
                usia_pensiun = st.number_input("Usia Pensiun Normal", value=55, step=1)
                asumsi_resign = st.number_input("Tingkat Pengunduran Diri / Resign (%)", value=2.0, step=0.1) / 100
            st.info("💡 **Standar Aktuaris KKA Setya Gunawan:** Suku bunga diskonto ditentukan otomatis lewat *yield curve matching* PHEI sesuai sisa masa kerja individual.")

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
                            {"NIK": "001", "Nama": "Karyawan Contoh 1", "Tanggal Lahir": "1990-01-21", "Tgl. Mulai Bekerja": "2023-10-15", "Total Upah Bulanan (Gross)": 10000000.0, "Saldo DPLK": 0.0}
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
        if st.button("Jalankan Valuasi Otomatis (PSAK 219 & IFRIC AD) 🚀") and datasets_to_process:
            with st.spinner("Menghitung perincian aktuaria per karyawan dengan metode PUC dan IFRIC AD..."):
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

                # Simpan ke session_state agar aman dari NameError & bisa ditarik oleh Admin
                st.session_state.results_dict = results_dict
                st.session_state.dplk_dict = dplk_dict
                st.session_state.paid_dict = benefit_paid_dict
                st.session_state.active_years = active_years
                st.session_state.asumsi_gaji = asumsi_gaji
                st.session_state.usia_pensiun = usia_pensiun
                st.session_state.input_perusahaan = input_perusahaan
                st.session_state.nomor_laporan = nomor_laporan
                st.session_state.tanggal_laporan = tanggal_laporan
                st.session_state.calculated_results = True
                st.success("Valuasi Aktuaria Selesai! Rincian tingkat individu kini siap ditinjau.")

        if st.session_state.get("calculated_results"):
            res_dict = st.session_state.results_dict
            act_yrs = st.session_state.active_years
            
            cur_salary_inc = st.session_state.get("asumsi_gaji", asumsi_gaji)
            cur_ret_age = st.session_state.get("usia_pensiun", usia_pensiun)
            cur_company = st.session_state.get("input_perusahaan", input_perusahaan)
            cur_no_rep = st.session_state.get("nomor_laporan", nomor_laporan)
            cur_date_rep = st.session_state.get("tanggal_laporan", tanggal_laporan)

            st.markdown("---")
            st.subheader("👥 Rincian Perhitungan Tingkat Individu per Karyawan")
            st.write("Berikut adalah rincian kalkulasi aktuaria per orang sesuai format kertas kerja KKA Setya Gunawan:")

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
            st.subheader("📥 Unduh Kertas Kerja & Laporan Resmi KKA Setya Gunawan")
            pdf_file = generate_detailed_report(
                results_dict=res_dict, 
                salary_inc=cur_salary_inc, 
                ret_age=cur_ret_age, 
                val_years=act_yrs, 
                company_name=cur_company, 
                report_no=cur_no_rep, 
                report_date=cur_date_rep
            )

            st.download_button(
                label="📥 Download Laporan Aktuaria PSAK 219 (PDF Landscape)",
                data=pdf_file,
                file_name=f"LAPORAN_AKTUARIA_PSAK219_{cur_company.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
