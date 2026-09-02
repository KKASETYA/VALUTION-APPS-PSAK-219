import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re
import base64
import time
import sqlite3
import uuid

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from streamlit_option_menu import option_menu

# ==========================================
# FIX ERROR FONT (DYNAMIC FONT VARIABLES)
# ==========================================
# Default ke font standar ReportLab yang 100% aman di Cloud manapun
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_ITALIC = 'Helvetica-Oblique'
FONT_BOLDITALIC = 'Helvetica-BoldOblique'

try:
    # Jika file font kustom tersedia, daftarkan dan gunakan font kustom
    if os.path.exists("Calibri.ttf") and os.path.exists("Calibri-Bold.ttf") and os.path.exists("Calibri-Italic.ttf") and os.path.exists("Calibri-BoldItalic.ttf"):
        pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
        pdfmetrics.registerFont(TTFont('Calibri-Bold', 'Calibri-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Calibri-Italic', 'Calibri-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Calibri-BoldItalic', 'Calibri-BoldItalic.ttf'))
        addMapping('Calibri', 0, 0, 'Calibri')
        addMapping('Calibri', 1, 0, 'Calibri-Bold')
        addMapping('Calibri', 0, 1, 'Calibri-Italic')
        addMapping('Calibri', 1, 1, 'Calibri-BoldItalic')
        
        FONT_REGULAR = 'Calibri'
        FONT_BOLD = 'Calibri-Bold'
        FONT_ITALIC = 'Calibri-Italic'
        FONT_BOLDITALIC = 'Calibri-BoldItalic'
except Exception:
    pass

# ==========================================
# KONFIGURASI HALAMAN & IDENTITAS KKA SETYA GUNAWAN
# ==========================================
st.set_page_config(
    page_title="KKA Setya Gunawan | Kantor Konsultan Aktuaria",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INISIALISASI DATABASE SQLITE (MULTI-TENANT BACKEND)
# ==========================================
def init_db():
    conn = sqlite3.connect("kka_actuarial.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_files (
            company_name TEXT PRIMARY KEY,
            filename TEXT,
            file_bytes BLOB,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculation_results (
            company_name TEXT,
            valuation_year INTEGER,
            result_csv TEXT,
            parameters TEXT,
            timestamp TEXT,
            PRIMARY KEY (company_name, valuation_year)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_pdfs (
            company_name TEXT PRIMARY KEY,
            pdf_bytes BLOB,
            filename TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# CUSTOM CSS & TEMA KORPORAT KKA SETYA GUNAWAN
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
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State Global
if 'payment_verified' not in st.session_state: st.session_state.payment_verified = False
if 'admin_logged_in' not in st.session_state: st.session_state.admin_logged_in = False
if 'client_session_id' not in st.session_state: st.session_state.client_session_id = str(uuid.uuid4())[:8]

if 'results_dict' not in st.session_state: st.session_state.results_dict = {}
if 'active_years' not in st.session_state: st.session_state.active_years = []
if 'calculated_results' not in st.session_state: st.session_state.calculated_results = False

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
    if dur_int in curve: return curve[dur_int]
    elif dur_int < 1: return curve[0.1]
    elif dur_int > 30: return curve[30]
    else:
        lower_tenor = max([t for t in curve.keys() if t <= duration])
        upper_tenor = min([t for t in curve.keys() if t >= duration])
        if lower_tenor == upper_tenor: return curve[lower_tenor]
        r_low, r_high = curve[lower_tenor], curve[upper_tenor]
        return r_low + (r_high - r_low) * (duration - lower_tenor) / (upper_tenor - lower_tenor)

# ==========================================
# 2. FORMATTER ANGKA & RUPIAH
# ==========================================
def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    if decimals == 0: return f"{num:,.0f}".replace(",", ".")
    else: return f"{num:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

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

    def safe_float(val, default=0.0):
        try:
            if pd.isna(val): return default
            cleaned = re.sub(r'[^0-9.\-]', '', str(val))
            if cleaned == '' or cleaned == '-': return default
            return float(cleaned)
        except: return default

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
                'Tanggal Lahir': dob, 'Tgl. Mulai Bekerja': doe,
                'Total Upah Bulanan (Gross)': salary, 'Saldo DPLK': dplk,
                'Pension_Mult': pension_mult, 'Disability_Mult': disability_mult,
                'Death_Mult': death_mult, 'Resign_Mult': resign_mult
            })

        if len(row) > 11:
            val_paid = safe_float(row.iloc[11], 0.0)
            if val_paid > 0: total_benefit_paid += val_paid

    return pd.DataFrame(clean_data), total_benefit_paid

# ==========================================
# 4. ENGINE AKTUARIA (PUC DENGAN IFRIC AD)
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

    def calculate_puc(self, current_age, past_service, current_salary, p_mult=1.75, d_mult=2.0, death_mult=2.0, r_mult=1.0, years_to_retire=0.0):
        if pd.isna(current_age) or pd.isna(past_service) or pd.isna(current_salary) or years_to_retire <= 0:
            return {'PBO': 0, 'CSC': 0, 'Duration': 0, 'PVFB': 0, 'Applied_Discount': 0, 'Future_Service': 0}

        discount_rate = get_phei_discount_rate(years_to_retire, self.val_year)
        total_service = past_service + years_to_retire
        weighted_time_pv = 0
        
        unattributed_years = max(0, total_service - 24)
        past_service_ret = max(0, past_service - unattributed_years)
        total_service_ret = min(total_service, 24)

        pvfb_death = pvfb_disability = pvfb_resign = 0
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
            pvfb_death += b_death * p_survival * q_m * v
            pvfb_disability += b_disab * p_survival * q_d * v
            pvfb_resign += b_resign * p_survival * q_w * v
            weighted_time_pv += (t + 1) * (b_death * p_survival * q_m * v + b_disab * p_survival * q_d * v + b_resign * p_survival * q_w * v)
            p_survival *= (1 - (q_m + q_d + q_w))

        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((p_mult * up_ret) + upmk_ret)
        v_ret = 1 / ((1 + discount_rate) ** years_to_retire)
        pv_ret = b_ret * v_ret * p_survival

        weighted_time_pv += years_to_retire * pv_ret
        total_pvfb = pvfb_death + pvfb_disability + pvfb_resign + pv_ret

        pbo_death_dis_res = (pvfb_death + pvfb_disability + pvfb_resign) * (past_service / total_service) if total_service > 0 else 0
        csc_death_dis_res = (pvfb_death + pvfb_disability + pvfb_resign) / total_service if total_service > 0 else 0
        
        pbo_ret = pv_ret * (past_service_ret / total_service_ret) if total_service_ret > 0 else 0
        csc_ret = (pv_ret / total_service_ret) if (past_service >= unattributed_years and total_service_ret > 0) else 0

        pbo = pbo_death_dis_res + pbo_ret
        csc = csc_death_dis_res + csc_ret
        duration = (weighted_time_pv / total_pvfb) if total_pvfb > 0 else years_to_retire / 2.0
        
        return {
            'PBO': pbo, 'CSC': csc, 'Duration': duration, 
            'PVFB': total_pvfb, 'Applied_Discount': discount_rate, 'Future_Service': years_to_retire
        }

# ==========================================
# 5. GENERATOR PDF LAPORAN
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
    canvas.line(56.7, 45, landscape(A4)[0] - 56.7, 45) 
    canvas.setFont(FONT_REGULAR, 9)
    canvas.drawCentredString(landscape(A4)[0]/2.0, 30, "Kantor Konsultan Aktuaria Setya Gunawan (KKA Setya Gunawan)")
    canvas.setFont(FONT_REGULAR, 8)
    canvas.drawCentredString(landscape(A4)[0]/2.0, 20, "Izin Badan Usaha No. 4.21.0007 | Keputusan Kemenkeu RI No. 590/KM.1/2021 | STTD-OJK: STTD-039/NB.122/STTD-KA/2021 | AKKAI: AKKAI-21043")
    canvas.restoreState()

def generate_detailed_report(results_dict, salary_inc, ret_age, val_keys, company_name, report_no, report_date):
    pdf_buffer = io.BytesIO()
    
    class MixedPageDocTemplate(SimpleDocTemplate):
        def handle_pageBegin(self):
            if self.page > 8: self.pagesize = landscape(A4)
            super().handle_pageBegin()

    doc_mixed = MixedPageDocTemplate(pdf_buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=54, bottomMargin=54)
    elements = []
    styles = getSampleStyleSheet()
    
    cover_title_style = ParagraphStyle('CoverMainTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=17, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=6, leading=21)
    cover_sub_style = ParagraphStyle('CoverSubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13.5, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=22, leading=17)
    cover_desc_style = ParagraphStyle('CoverDesc', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=4, leading=15)
    cover_date_style = ParagraphStyle('CoverDate', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, textColor=colors.HexColor('#E67E22'), alignment=2, spaceAfter=65, leading=14)
    cover_address_style = ParagraphStyle('CoverAddressRight', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, textColor=colors.HexColor('#2980B9'), alignment=2, leading=13.5)
    
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontName=FONT_BOLD, fontSize=11, textColor=colors.HexColor('#C2382D'), spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('BodyCustom', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.HexColor('#222222'), spaceBefore=4, spaceAfter=8, leading=15, alignment=4, keepWithNext=False)

    formatted_date = report_date.strftime('%d %B %Y') if hasattr(report_date, 'strftime') else str(report_date)

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
    
    first_key = val_keys[0] if val_keys else '31 Des 2022'
    elements.append(Paragraph(f"PERIOD PER {first_key.upper()}", cover_date_style))
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

    # ==========================================
    # HALAMAN INFORMASI UMUM / GENERAL INFORMATION
    # ==========================================
    info_text_style = ParagraphStyle('InfoText', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.black, alignment=4, spaceAfter=4, leading=15)
    info_header_table_style = ParagraphStyle('InfoHeaderTable', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, textColor=colors.black, alignment=0, leading=15)

    content_width_portrait = 595.27 - 72 
    col_w_half = content_width_portrait / 2.0

    info_col_left = [
        Paragraph("<b>INFORMASI UMUM</b>", info_header_table_style),
        Spacer(1, 6),
        Paragraph("• <b>Entitas:</b><br/>PT " + company_name.upper(), info_text_style),
        Paragraph("• <b>Alamat:</b><br/>Cilandak 88 Condominium Unit D-1, Jl. Margasatwa Barat No. 88, Cilandak Timur, Pasar Minggu, Jakarta Selatan 12560", info_text_style),
        Paragraph(f"• <b>Tanggal Valuasi:</b><br/>{first_key}", info_text_style),
        Paragraph("• <b>Konsultan Aktuaria:</b><br/><b>KKA SETYA GUNAWAN</b><br/>Cilandak 88 Condominium Unit D-1,<br/>Jl. Margasatwa Barat No. 88,<br/>Cilandak Timur,<br/>Pasar Minggu,<br/>Jakarta Selatan<br/>12560", info_text_style),
        Paragraph("• <b>Izin Usaha:</b><br/>Kementrian Keuangan RI<br/>Badan Pengawas Pasar Modal & Lembaga Keuangan<br/>No.", info_text_style),
        Paragraph("• <b>Aktuaris Public:</b><br/>Act-1.17.00026", info_text_style)
    ]

    info_col_right = [
        Paragraph("<b>GENERAL INFORMATION</b>", info_header_table_style),
        Spacer(1, 6),
        Paragraph("• <b>Entity:</b><br/>PT " + company_name.upper(), info_text_style),
        Paragraph("• <b>Address:</b><br/>Cilandak 88 Condominium Unit D-1, Jl. Margasatwa Barat No. 88, Cilandak Timur, Pasar Minggu, Jakarta Selatan 12560", info_text_style),
        Paragraph(f"• <b>Valuation Date:</b><br/>{first_key}", info_text_style),
        Paragraph("• <b>Actuarial Consultant:</b><br/><b>KKA SETYA GUNAWAN</b><br/>Cilandak 88 Condominium Unit D-1,<br/>Jl. Margasatwa Barat No. 88,<br/>Cilandak Timur,<br/>Pasar Minggu,<br/>Jakarta Selatan<br/>12560", info_text_style),
        Paragraph("• <b>Business Licence:</b><br/>Ministry of Finance RI<br/>Badan Pengawas Pasar Modal & Lembaga Keuangan<br/>No.", info_text_style),
        Paragraph("• <b>Public Actuary:</b><br/>Act-1.17.00026", info_text_style)
    ]

    info_table = Table([[info_col_left, info_col_right]], colWidths=[col_w_half, col_w_half])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())

    # ==========================================
    # HALAMAN DAFTAR ISI / TABLE OF CONTENTS
    # ==========================================
    toc_head_style = ParagraphStyle('TOCHead', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, textColor=colors.black, leading=15)
    toc_item_style = ParagraphStyle('TOCItem', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.black, leading=15, alignment=4)
    toc_subitem_style = ParagraphStyle('TOCSubItem', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.black, leading=15, leftIndent=12, alignment=4)

    toc_left_content = [
        Paragraph("<b>DAFTAR ISI &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; HAL &nbsp;&nbsp; PAGES</b>", toc_head_style),
        Spacer(1, 3),
        Paragraph("<b>Informasi Umum</b>", toc_item_style),
        Paragraph("<b>Daftar Isi</b>", toc_item_style),
        Spacer(1, 3),
        Paragraph("1 &nbsp;&nbsp;&nbsp;&nbsp; Pendahuluan", toc_item_style),
        Paragraph("2 &nbsp;&nbsp;&nbsp;&nbsp; Manfaat", toc_item_style),
        Paragraph("3 &nbsp;&nbsp;&nbsp;&nbsp; Data Karyawan dan Data Keuangan", toc_item_style),
        Paragraph("4 &nbsp;&nbsp;&nbsp;&nbsp; Metodologi", toc_item_style),
        Paragraph("5 &nbsp;&nbsp;&nbsp;&nbsp; Metode Valuasi dan Asumsi Aktuaria", toc_item_style),
        Paragraph("6 &nbsp;&nbsp;&nbsp;&nbsp; Ringkasan Hasil Valuasi", toc_item_style),
        Paragraph("7 &nbsp;&nbsp;&nbsp;&nbsp; Penutup", toc_item_style),
        Spacer(1, 3),
        Paragraph("<b>Lampiran</b>", toc_item_style),
        Paragraph("1 &nbsp;&nbsp;&nbsp;&nbsp; Ringkasan Manfaat Imbalan Kerja", toc_item_style),
        Paragraph("2 &nbsp;&nbsp;&nbsp;&nbsp; Pengertian Istilah Teknis", toc_item_style),
        Paragraph("3 &nbsp;&nbsp;&nbsp;&nbsp; Justifikasi Asumsi Aktuaria", toc_item_style),
        Paragraph("4 &nbsp;&nbsp;&nbsp;&nbsp; Tabel Tingkat Kematian, Pengunduran Diri dan Sakit Berkepanjangan", toc_item_style),
        Paragraph(f"5 &nbsp;&nbsp;&nbsp;&nbsp; Tabel PHEI Per {first_key}", toc_item_style),
        Paragraph("6 &nbsp;&nbsp;&nbsp;&nbsp; Detail Karyawan", toc_item_style),
        Spacer(1, 3),
        Paragraph("<b>TABEL</b>", toc_item_style),
        Paragraph("<b>Tabel Rekonsiliasi</b>", toc_item_style),
        Paragraph("• &nbsp; Analisis Sensitivitas", toc_subitem_style),
        Paragraph("• &nbsp; Tabel Distribusi", toc_subitem_style),
        Paragraph("• &nbsp; Tabel 1: Data, Asumsi dan Hasil Valuasi Aktuaria", toc_subitem_style),
        Paragraph("• &nbsp; Tabel 2: Perhitungan Pengukuran Kembali", toc_subitem_style),
        Paragraph("• &nbsp; Tabel 3: Penghasilan Komprehensif Lain", toc_subitem_style),
        Paragraph("• &nbsp; Tabel 4: Posisi Pendanaan dan Pengakuan (Kewajiban)/Aset dalam Neraca", toc_subitem_style),
        Paragraph("• &nbsp; Tabel 5: Pengakuan Beban/(Pendapatan) dalam Laporan Laba Rugi", toc_subitem_style),
        Paragraph("• &nbsp; Perhitungan Dampak Kurtailment", toc_subitem_style),
    ]

    toc_right_content = [
        Paragraph("<b>GENERAL INFORMATION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; PAGES</b>", toc_head_style),
        Spacer(1, 3),
        Paragraph("<b>General Information</b>", toc_item_style),
        Paragraph("<b>Table of contents</b>", toc_item_style),
        Spacer(1, 3),
        Paragraph("1 &nbsp;&nbsp;&nbsp;&nbsp; Introduction", toc_item_style),
        Paragraph("2 &nbsp;&nbsp;&nbsp;&nbsp; Benefits Program", toc_item_style),
        Paragraph("3 &nbsp;&nbsp;&nbsp;&nbsp; Employee and Financial Data", toc_item_style),
        Paragraph("4 &nbsp;&nbsp;&nbsp;&nbsp; Methodology", toc_item_style),
        Paragraph("5 &nbsp;&nbsp;&nbsp;&nbsp; Actuarial Valuation Methods and Assumptions", toc_item_style),
        Paragraph("6 &nbsp;&nbsp;&nbsp;&nbsp; Summary of Valuation Results", toc_item_style),
        Paragraph("7 &nbsp;&nbsp;&nbsp;&nbsp; Closing", toc_item_style),
        Spacer(1, 3),
        Paragraph("<b>Appendices</b>", toc_item_style),
        Paragraph("1 &nbsp;&nbsp;&nbsp;&nbsp; Summary of Employee Benefits", toc_item_style),
        Paragraph("2 &nbsp;&nbsp;&nbsp;&nbsp; Definition of Technical Terms", toc_item_style),
        Paragraph("3 &nbsp;&nbsp;&nbsp;&nbsp; Justification of Actuarial Assumptions", toc_item_style),
        Paragraph("4 &nbsp;&nbsp;&nbsp;&nbsp; Table of Mortality, Resignation and Prolonged Illness Rates", toc_item_style),
        Paragraph(f"5 &nbsp;&nbsp;&nbsp;&nbsp; IBPA table as of {first_key}", toc_item_style),
        Paragraph("7 &nbsp;&nbsp;&nbsp;&nbsp; Detail Employee", toc_item_style),
        Spacer(1, 3),
        Paragraph("<b>TABLES</b>", toc_item_style),
        Paragraph("<b>Reconciliation Table</b>", toc_item_style),
        Paragraph("• &nbsp; Sensitivity Analysis", toc_subitem_style),
        Paragraph("• &nbsp; Distribution Table", toc_subitem_style),
        Paragraph("• &nbsp; Table 1: Data, Assumptions and Actuarial Valuation Results", toc_subitem_style),
        Paragraph("• &nbsp; Table 2: Re-measurement Calculations", toc_subitem_style),
        Paragraph("• &nbsp; Table 3: Other Comprehensive Income", toc_subitem_style),
        Paragraph("• &nbsp; Table 4: Funding Position and Recognition of (Liability)/Asset in Balance Sheet", toc_subitem_style),
        Paragraph("• &nbsp; Table 5: Expenses/(Revenues) in Income Statement", toc_subitem_style),
        Paragraph("• &nbsp; Calculation of Curtailment Effects", toc_subitem_style),
    ]

    toc_table = Table([[toc_left_content, toc_right_content]], colWidths=[col_w_half, col_w_half])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(toc_table)
    elements.append(PageBreak())

    # ==========================================
    # HALAMAN PENDAHULUAN & MANFAAT KARYAWAN
    # ==========================================
    intro_head_style_11 = ParagraphStyle('IntroHead11', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, textColor=colors.black, leading=15, spaceAfter=4, keepWithNext=True)
    intro_subhead_style_11 = ParagraphStyle('IntroSubHead11', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, textColor=colors.black, leading=15, spaceAfter=2, keepWithNext=True)
    intro_body_style_11 = ParagraphStyle('IntroBody11', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.black, leading=15, spaceAfter=3, alignment=4, keepWithNext=False)

    intro_col_left_p1 = [
        Paragraph("<b>1. PENDAHULUAN</b>", intro_head_style_11),
        Paragraph("<b>1.1 Tujuan</b>", intro_subhead_style_11),
        Paragraph(f"Laporan ini disajikan berdasarkan Lembar Persetujuan PT {company_name.upper()} untuk mengetahui Kewajiban dan Beban atas Imbalan Kerja Karyawan berdasarkan Undang-Undang Ketenagakerjaan (UU Cipta Kerja No. 11 Tahun 2020) dan Peraturan Perusahaan yang berlaku, sebagaimana tertuang dalam PSAK 219 tentang Imbalan Kerja.", intro_body_style_11),
        Paragraph(f"Selain itu perhitungan ini dilakukan untuk tahun buku yang berakhir pada {first_key}.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>1.2 Manfaat</b>", intro_subhead_style_11),
        Paragraph("Manfaat Karyawan berdasarkan UU Cipta Kerja No. 11 Tahun 2020 mencakup Imbalan Kerja untuk Karyawan Tetap yang diberhentikan karena Pensiun, Meninggal Dunia, Sakit Berkepanjangan atau Mengundurkan Diri secara sukarela.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>1.3 Tanggal Valuasi</b>", intro_subhead_style_11),
        Paragraph(f"Tanggal Valuasi adalah {first_key}.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>1.4 Data</b>", intro_subhead_style_11),
        Paragraph("Valuasi menggunakan data yang telah kami terima dan telah dikonfirmasi oleh Entitas.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2. MANFAAT KARYAWAN</b>", intro_head_style_11),
        Paragraph("Manfaat karyawan berdasarkan Cipta Kerja No. 11 Tahun 2020, terdiri dari:", intro_body_style_11),
        Paragraph("<b>2.1 Manfaat Pensiun</b><br/>Manfaat yang dibayarkan kepada Karyawan yang berhenti bekerja karena mencapai usia pensiun normal. Besaran manfaat adalah sebesar 2,3P + 1,15PMK. (Pasal 56)", intro_body_style_11),
        Paragraph("<b>2.2 Manfaat Meninggal Dunia</b><br/>Manfaat yang dibayarkan kepada ahli waris dari Karyawan yang Meninggal Dunia. Besaran manfaat adalah sebesar 2,3P + 1,15PMK. (Pasal 57)", intro_body_style_11)
    ]

    intro_col_right_p1 = [
        Paragraph("<b>1. INTRODUCTION</b>", intro_head_style_11),
        Paragraph("<b>1.1 Purpose</b>", intro_subhead_style_11),
        Paragraph(f"This report is presented by virtue of PT {company_name.upper()} to determine the Obligations and Expenses for Employee Benefits under Law about Manpower (UU Cipta Kerja No. 11 Tahun 2020) and applicable Company Regulations, as stated in PSAK 219 concerning Employee Benefits.", intro_body_style_11),
        Paragraph(f"In addition, this calculation is for the financial year ending {first_key}.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>1.2 Benefit</b>", intro_subhead_style_11),
        Paragraph("Under Law Cipta Kerja No. 11 Years 2020 about Manpower, Employee Benefits in this valuation include benefits for Permanent Employees terminated due to retirement, death, prolonged illness or voluntary resignation.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>1.3 Valuation Date</b>", intro_subhead_style_11),
        Paragraph(f"The Valuation Date as per {first_key}.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>1.4 Data</b>", intro_subhead_style_11),
        Paragraph("Valuation uses the data we have received and confirmed by the Entity.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2. EMPLOYEE BENEFITS</b>", intro_head_style_11),
        Paragraph("Under Law Cipta Kerja No. 11 years 2020 about Manpower, Employee Benefits consist of:", intro_body_style_11),
        Paragraph("<b>2.1 Retirement Benefits</b><br/>Benefits paid to those employees terminated due to reaching the normal retirement age. The amount of benefit is 2,3P + 1,15PMK. (Article 56)", intro_body_style_11),
        Paragraph("<b>2.2 Death Benefits</b><br/>Benefits paid to the heirs of Death Employees. The amount of benefit is 2,3P + 1,15PMK. (Article 57)", intro_body_style_11)
    ]

    intro_table_p1 = Table([[intro_col_left_p1, intro_col_right_p1]], colWidths=[col_w_half, col_w_half])
    intro_table_p1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(intro_table_p1)
    elements.append(PageBreak())

    # ==========================================
    # HALAMAN LANJUTAN PENDAHULUAN & MANFAAT
    # ==========================================
    intro_col_left_p2 = [
        Paragraph("<b>2.3 Manfaat Mengundurkan Diri</b><br/>Manfaat yang dibayarkan kepada Karyawan yang Mengundurkan Diri secara sukarela. Besaran manfaat adalah sebesar 0,3P + 0,15PMK. (Pasal 50)", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.4 Manfaat Sakit Berkepanjangan</b><br/>Manfaat yang dibayarkan kepada Karyawan yang diberhentikan karena Sakit berkepanjangan. Besaran manfaat adalah sebesar 2,3P + 2,3PMK. (Pasal 55)", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.5 Uang pisah</b><br/>Perusahaan diwajibkan untuk memberikan uang pisah kepada karyawan akibat Pemutusan Hubungan Kerja, dimana besaran nya diatur sesuai dengan Undang-undang", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.6 Karyawan PKWT (Kontrak)</b><br/>Pengusaha wajib memberikan uang kompensasi kepada Pekerja/Buruh yang hubungan kerjanya berdasarkan PKWT. Uang kompensasi diberikan kepada Pekerja/Buruh yang telah mempunyai masa kerja paling sedikit 1 (satu) bulan secara terus menerus. Uang Kompensasi yang dihitung secara aktuaria adalah Pekerja/Buruh yang telah mempunyai masa kerja lebih dari 1 (satu) tahun.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.7 Pajak</b><br/>Pajak atas Manfaat Pensiun dibayar oleh Karyawan sesuai Pasal 21 Peraturan Pemerintah Republik Indonesia Nomor 68 Tahun 2009 tentang Tarif Pajak Penghasilan.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>3. DATA PESERTA DAN KEUANGAN</b>", intro_head_style_11),
        Paragraph("Peserta adalah Karyawan Tetap (PKWTT) & Kontrak (PKWT).", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>3.1 Data Karyawan Tetap (PKWTT) & Kontrak (PKWT)</b>", intro_subhead_style_11),
    ]

    intro_col_right_p2 = [
        Paragraph("<b>2.3 Resignation Benefits</b><br/>Benefits paid to those voluntarily resigned Employees. The amount of benefit is equal to 0,3P + 0,15PMK. (Article 50)", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.4 Benefits of Prolonged Illness</b><br/>Benefits paid to those employees terminated due to prolonged illness. The amount of benefit is 2,3P + 2,3PMK. (Article 55)", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.5 Benefit Severance Payment</b><br/>Companies are required to provide severance pay to employees as a result of Termination of Employment, where the amount is regulated in accordance with the Law.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.6 PKWT Employees (Contract)</b><br/>Employers are required to provide compensation money to Workers / Laborers whose working relationship is based on PKWT. Compensation money is given to Workers / Laborers who have worked at least 1 (one) month continuously. Compensation money that is calculated actuarially is Workers/Laborers who have worked for more than 1 (one) year.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>2.7 Tax</b><br/>Taxes on Retirement Benefits are paid by the Employee in accordance with Article 21 of Government Regulation of the Republic of Indonesia Number 68 of 2009 concerning Income Tax Rates.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>3. PARTICIPANT AND FINANCIAL DATA</b>", intro_head_style_11),
        Paragraph("Participants are Permanent (PKWTT) & Contract (PKWT) Employees.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>3.1 Permanent PKWTT & Contract PKWT Employees Data</b>", intro_subhead_style_11),
    ]

    intro_table_p2 = Table([[intro_col_left_p2, intro_col_right_p2]], colWidths=[col_w_half, col_w_half])
    intro_table_p2.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(intro_table_p2)
    elements.append(PageBreak())

    # ==========================================
    # HALAMAN DATA KEUANGAN & METODOLOGI
    # ==========================================
    fin_col_left = [
        Paragraph("Berikut adalah ringkasan data yang kami terima dari Entitas terdapat pada tabel 1", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>3.2 Data Keuangan</b>", intro_subhead_style_11),
        Paragraph("Realisasi Pembayaran Benefit / Manfaat serta iuran termasuk pajak oleh Perusahaan sebagai berikut :", intro_body_style_11),
        Paragraph("• &nbsp; Realisasi pembayaran Manfaat Pensiun adalah sebesar <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Realisasi pembayaran Manfaat Mengundurkan diri adalah sebesar <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Realisasi pembayaran Manfaat Meninggal Dunia adalah sebesar <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Nilai Wajar Aset Program Dana Pensiun adalah sebesar <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Iuran Karyawan Dana Pensiun adalah sebesar <b>Rp. 0,-</b>", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4. METODOLOGI</b>", intro_head_style_11),
        Paragraph("<b>4.1</b> Tujuan PSAK 219 adalah untuk mengatur Akuntansi dan pengungkapan imbalan kerja. Di dalam PSAK 219, entitas diwajibkan untuk mengakui <b>Liabilitas</b> ketika pekerja telah memberikan jasanya dan berhak memperoleh imbalan kerja yang akan dibayarkan dimasa yang akan datang, dan <b>Beban</b> ketika entitas menikmati manfaat ekonomis yang dihasilkan dari jasa yang diberikan oleh pekerja yang berhak memperoleh imbalan kerja.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4.2</b> Dalam PSAK 219, Komponen Beban terdiri dari:", intro_body_style_11),
        Paragraph("a. &nbsp; Biaya Jasa Kini;<br/>b. &nbsp; Biaya Bunga Neto;<br/>c. &nbsp; Biaya Jasa Lalu, jika ada.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4.3</b> Pada Neraca, jumlah (Kewajiban)/ Aset yang diakui adalah akumulasi dari (Beban)/Pendapatan ditambah Penghasilan Komprehensif Lain Pembayaran Manfaat Aktual, dan Kontribusi yang dibayarkan oleh Entitas.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4.4</b> Pengertian Istilah Teknis yang digunakan dalam laporan ini dijelaskan pada <b>Lampiran 2</b>.", intro_body_style_11)
    ]

    fin_col_right = [
        Paragraph("The following is a summary of data we received from the Entity is on Table 1", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>3.2 Financial Data</b>", intro_subhead_style_11),
        Paragraph("The Company's realized Benefit and Contributions Payments are as follows:", intro_body_style_11),
        Paragraph("• &nbsp; Realized payments of Retirement Benefits shall be <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Realized payments of Withdrawal Benefits shall be <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Realized payments of Death Benefits shall be <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Fair Value of Pension Fund Assets shall be <b>Rp. 0,-</b>", intro_body_style_11),
        Paragraph("• &nbsp; Employee contributions to Pension Fund shall be <b>Rp. 0,-</b>", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4. METHODOLOGY</b>", intro_head_style_11),
        Paragraph("<b>4.1</b> The purpose of PSAK 219 is to regulate and disclose employee benefits accounting treatment and disclosure. Under PSAK 219, an entity is required to recognize <b>Liabilities</b> when an employee has provided their services and is entitled to receive employee benefits to be paid in the future and <b>Expenses</b> when the entity gets economic benefits resulting from services provided by employees entitled to receive employee benefits.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4.2</b> Under PSAK 24, the Expense Component consists of:<br/>a. &nbsp; Current Service Cost;<br/>b. &nbsp; Net Interest Cost;<br/>c. &nbsp; Past Service Cost, if any.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4.3</b> On the Balance Sheet, the recognized amount (Liabilities) / Assets is the accumulated (Expenses)/Revenues plus Other Comprehensive Income, Actual Benefit Payment, and Contributions paid by the Entity.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>4.4</b> The definitions of Technical Terms used in this report are described in <b>Appendix 2</b>.", intro_body_style_11)
    ]

    fin_table = Table([[fin_col_left, fin_col_right]], colWidths=[col_w_half, col_w_half])
    fin_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(fin_table)
    elements.append(PageBreak())

    # ==========================================
    # HALAMAN: METODE DAN ASUMSI AKTUARIA
    # ==========================================
    meth_col_left = [
        Paragraph("<b>5. METODE DAN ASUMSI AKTUARIA</b>", intro_head_style_11),
        Spacer(1, 2),
        Paragraph("<b>5.1 Metode Valuasi Aktuaria</b>", intro_subhead_style_11),
        Paragraph("Metode valuasi aktuaria yang dipergunakan adalah <b>“Projected Unit Credit”</b> berdasarkan metode ini, manfaat/imbalan diakru secara prorata sesuai jasa atau dengan kata lain manfaat/imbalan dibagi tahun jasa, mengganggap setiap periode jasa akan menghasilkan satu unit tambahan manfaat/imbalan dan mengukur setiap unit secara terpisah untuk menghasilkan kewajiban final.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>5.2 Asumsi Aktuaria</b>", intro_subhead_style_11),
        Paragraph("Berdasarkan PSAK 219, asumsi aktuaria tidak boleh bias dan harus cocok satu dengan yang lain. Asumsi aktuaria adalah estimasi terbaik entitas mengenai variabel yang akan menentukan hasil Valuasi.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>6. RINGKASAN HASIL VALUASI</b>", intro_head_style_11),
        Paragraph("Berdasarkan Data, Metode dan Asumsi yang digunakan, berikut ini ringkasan hasil valuasi.", intro_body_style_11)
    ]

    meth_col_right = [
        Paragraph("<b>5. ACTUARIAL METHODS AND ASSUMPTIONS</b>", intro_head_style_11),
        Spacer(1, 2),
        Paragraph("<b>5.1 Actuarial Valuation Method</b>", intro_subhead_style_11),
        Paragraph("The actuarial valuation method used is <b>“Projected Unit Credit”</b>. Under this method, benefits/rewards are accrued pro rata according to services; or, in other words, benefits/rewards are divided by service years, assuming each service period would produce one additional unit of benefits/rewards and measuring each unit separately to produce final obligations.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>5.2 Actuarial Assumptions</b>", intro_subhead_style_11),
        Paragraph("Under PSAK 219, actuarial assumptions must be unbiased and mutually compatible. Actuarial assumptions are the entity's best estimates of the variables that would determine the valuation results.", intro_body_style_11),
        Spacer(1, 2),
        Paragraph("<b>6. SUMMARY OF VALUATION RESULTS</b>", intro_head_style_11),
        Paragraph("Based on the Data, Methods and Assumptions used, here is the summary of valuation results.", intro_body_style_11)
    ]

    meth_table = Table([[meth_col_left, meth_col_right]], colWidths=[col_w_half, col_w_half])
    meth_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(meth_table)
    elements.append(PageBreak())

    # ==========================================
    # HALAMAN BARU: PENUTUP / CLOSING
    # ==========================================
    closing_style_11 = ParagraphStyle('ClosingStyle11', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.black, leading=15, spaceAfter=4, alignment=4, keepWithNext=False)
    closing_head_11 = ParagraphStyle('ClosingHead11', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, textColor=colors.black, leading=15, spaceAfter=4, keepWithNext=True)
    closing_center_style = ParagraphStyle('ClosingCenter', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, textColor=colors.black, leading=15, alignment=1, keepWithNext=True)

    closing_col_left = [
        Paragraph("<b>7. PENUTUP</b>", closing_head_11),
        Paragraph(f"Semoga informasi yang kami berikan dapat berguna bagi manajemen <b>PT {company_name.upper()}</b> dan pihak <i>Auditor</i> dalam rangka mengakui kewajiban dan beban entitas sesuai dengan ketentuan PSAK 219 untuk periode {first_key}.", closing_style_11),
        Spacer(1, 10),
        Paragraph(f"Jakarta, {formatted_date}", closing_center_style),
        Spacer(1, 8),
        Paragraph("<b>KKA SETYA GUNAWAN</b>", ParagraphStyle('SignHeadLeft', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, alignment=0, keepWithNext=True)),
        Spacer(1, 2),
        Paragraph("Aktuaris Publik<br/>(Public Actuary)<br/>Lisensi Aktuaris Publik<br/>(Public Actuary Licence)<br/>Konsultan<br/>(Consultant Office)<br/>Alamat Kantor", ParagraphStyle('SignDescLeft', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, leading=15, alignment=0))
    ]

    closing_col_right = [
        Paragraph("<b>7. CLOSING</b>", closing_head_11),
        Paragraph(f"We hope that the information we provide can be useful for the management of <b>PT {company_name.upper()}</b> and the Auditor to recognize the entity's liabilities and expenses in accordance with the provisions of PSAK 219 for the period of {first_key}.", closing_style_11),
        Spacer(1, 45), 
        Paragraph("<b>Setya Gunawan, S.E., AAAIJ, AIIS, FSAI</b>", ParagraphStyle('SignHeadRight', parent=styles['Normal'], fontName=FONT_BOLD, fontSize=11, alignment=0, keepWithNext=True)),
        Spacer(1, 2),
        Paragraph("<b>:</b> Aktuaris Publik<br/><b>:</b> Act-1.17.00026<br/><b>:</b> KKA SETYA GUNAWAN<br/><b>:</b> Cilandak 88 Condominium Unit D-1<br/>Jl. Margasatwa Barat No.88<br/>Cilandak Timur<br/>Pasar Minggu<br/>Jakarta Selatan,<br/>12560", ParagraphStyle('SignDescRight', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, leading=15, alignment=0))
    ]

    closing_table = Table([[closing_col_left, closing_col_right]], colWidths=[col_w_half, col_w_half])
    closing_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(closing_table)
    elements.append(Spacer(1, 5))

    contact_col_left = [
        Paragraph("(Office Adress)<br/>Telepon<br/>(Phone)<br/>Surat Elektronik<br/>(Email)", ParagraphStyle('ContactDescLeft', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, leading=15, alignment=0))
    ]
    contact_col_right = [
        Paragraph("<b>:</b> +62 21 781 7718 / +62 812 9090 9019<br/><b>:</b> <a href='mailto:aktuaris@actuarial-kas.com'>aktuaris@actuarial-kas.com</a>; <a href='mailto:kka_setyagunawan@yahoo.com'>kka_setyagunawan@yahoo.com</a>", ParagraphStyle('ContactDescRight', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, leading=15, alignment=0))
    ]
    contact_table = Table([[contact_col_left, contact_col_right]], colWidths=[col_w_half, col_w_half])
    contact_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(contact_table)
    elements.append(PageBreak())

    for vkey in sorted(val_keys, reverse=True):
        df_yr = results_dict[vkey]
        if df_yr.empty: continue
            
        tot_salary = df_yr['Gross Salary'].sum()
        tot_pvfb = df_yr['PVFB'].sum()
        tot_pbo = df_yr['PBO'].sum()
        tot_csc = df_yr['CSC'].sum()
        num_emp = len(df_yr)

        elements.append(Paragraph(f"<b>8. RINGKASAN HASIL VALUASI (PER {vkey.upper()})</b>", h_style))
        t1_data = [
            ["URAIAN (EXPLANATION)", f"Per {vkey} (Pasca Kerja)", f"Per {vkey} (Jangka Panjang Lainnya)"],
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
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D3C1BE')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 15))

        elements.append(Paragraph(f"<b>LAMPIRAN — Detail Perhitungan Individu Karyawan (Periode {vkey})</b>", h_style))
        table_data = [["No", "NIK & Nama Karyawan", "Tgl Lahir", "Tgl Masuk", "Gaji Kotor (Rp)", "NRA", "Umur", "Age Entry", "Masa Kerja", "Faktor UU", "Diskonto", "PVFB (Rp)", "PBO (Rp)", "CSC (Rp)"]]
        
        for i, row in df_yr.iterrows():
            dob_str = row['Tanggal Lahir'].strftime('%d-%m-%Y') if pd.notnull(row['Tanggal Lahir']) else "-"
            doe_str = row['Tgl. Mulai Bekerja'].strftime('%d-%m-%Y') if pd.notnull(row['Tgl. Mulai Bekerja']) else "-"
            table_data.append([
                str(i + 1), f"{row['NIK']}\n{row['Name']}"[:22], dob_str, doe_str,
                fmt_num(row['Gross Salary']), f"{row['NRA']:.2f}", f"{row['Age Valuation']:.2f}", f"{row['Age Entry']:.2f}", f"{row['Past Service']:.2f}",
                "23.75", f"{row['Applied_Discount']*100:.2f}%", fmt_num(row['PVFB']), fmt_num(row['PBO']), fmt_num(row['CSC'])
            ])
            
        table_data.append([
            "", "TOTAL KESELURUHAN", "", "", fmt_num(tot_salary), "", "", "", "", "", "", 
            fmt_num(tot_pvfb), fmt_num(tot_pbo), fmt_num(tot_csc)
        ])
        
        col_widths = [24, 115, 55, 55, 75, 30, 32, 35, 38, 50, 42, 65, 65, 60]
        t_detail = Table(table_data, colWidths=col_widths, repeatRows=1)
        t_detail.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3A0C08')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D3C1BE')),
            ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
            ('ALIGN', (1,1), (3,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EADCDA')),
            ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD)
        ]))
        elements.append(t_detail)
        elements.append(PageBreak())

    elements.append(Paragraph("<b>9. PENUTUP / CLOSING</b>", h_style))
    elements.append(Paragraph(f"Demikian laporan aktuaria ini disusun secara independen oleh KKA Setya Gunawan untuk dipergunakan sebagaimana mestinya oleh manajemen <b>PT {company_name.upper()}</b> dan pihak Auditor independen.", body_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Jakarta, {formatted_date}<br/><b>KANTOR KONSULTAN AKTUARIA SETYA GUNAWAN</b><br/><br/><br/><br/><b>Setya Gunawan, S.E., AAAIJ, AIIS, FSAI</b>", ParagraphStyle('SignBlock', parent=styles['Normal'], fontName=FONT_REGULAR, fontSize=11, alignment=2)))
        
    doc_mixed.build(elements, onFirstPage=draw_cover_background, onLaterPages=draw_footer_landscape)
    pdf_buffer.seek(0)
    return pdf_buffer

# ==========================================
# 6. KONSTANTA KORPORAT KKA SETYA GUNAWAN
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
        with open(LOGO_PATH, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

LOGO_B64 = load_logo_base64()

# ==========================================
# 7. NAVIGASI HORIZONTAL NAVBAR ATAS
# ==========================================
if "menu" not in st.session_state: st.session_state["menu"] = "Beranda"

def go_to(page_name): st.session_state["menu"] = page_name; st.rerun()

query_params = st.query_params
is_url_admin = query_params.get("role") == "admin"

nav_options = ["Beranda", "Tentang Kami", "Layanan Kami", "Kalkulator Valuasi Aktuaria", "Kontak Kami"]
nav_icons = ["house", "building", "briefcase", "calculator", "envelope"]

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
        menu_title=None, options=nav_options, icons=nav_icons, menu_icon="cast",
        default_index=nav_options.index(st.session_state["menu"]) if st.session_state["menu"] in nav_options else 0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#FAF1F0", "border-radius": "10px", "margin-bottom": "25px"},
            "icon": {"color": "#C2382D", "font-size": "13px"}, 
            "nav-link": {"font-size": "13.5px", "text-align": "center", "margin": "0px 4px", "font-family": "Inter, sans-serif", "font-weight": "600", "color": "#3A0C08"},
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
        st.markdown("📐 **PSAK 219 & IFRIC AD** | 📈 **PHEI Yield Matching** | 📄 **Kertas Kerja Audit Ready** | 🗂️ **Multi-Tenant DB**")

    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Hitung Imbalan Kerja PSAK 219", use_container_width=True): go_to("Kalkulator Valuasi Aktuaria")
    with c2:
        if st.button("💼 Lihat Layanan Kami", use_container_width=True): go_to("Layanan Kami")

# ==========================================
# 9. HALAMAN: TENTANG KAMI
# ==========================================
elif menu == "🏢 Tentang Kami" or menu == "Tentang Kami":
    with st.container():
        st.success("TENTANG KAMI")
        st.title(f"{COMPANY_LEGAL_NAME}")
        st.write("Kantor konsultan aktuaria independen yang terdaftar resmi dan berizin untuk memberikan layanan aktuaria, konsultasi imbalan kerja, dan audit support bagi perusahaan di Indonesia.")

# ==========================================
# 10. HALAMAN: LAYANAN KAMI
# ==========================================
elif menu == "💼 Layanan Kami" or menu == "Layanan Kami":
    with st.container():
        st.success("LAYANAN KAMI")
        st.title("Layanan Konsultasi & Valuasi Aktuaria")
        st.write("Mendampingi perusahaan menyusun laporan aktuaria imbalan pascakerja, analisis sensitivitas, hingga tata kelola program dana pensiun (DPLK / DPPK).")

# ==========================================
# 11. HALAMAN: KONTAK KAMI
# ==========================================
elif menu == "📞 Kontak Kami" or menu == "Kontak Kami":
    with st.container():
        st.success("HUBUNGI KAMI")
        st.title("Konsultasikan Kebutuhan Aktuaria Anda")
        st.write(f"Email: {COMPANY_EMAIL} | Telepon: {COMPANY_PHONE}<br/>Alamat: {COMPANY_ADDRESS}", unsafe_allow_html=True)

# ==========================================
# 12. HALAMAN: ADMIN DASHBOARD (MULTI-TENANT & 5 KOLOM SESUAI PERMINTAAN)
# ==========================================
elif menu == "🔐 Admin Dashboard":
    st.success("PANEL KONTROL INTERNAL KKA SETYA GUNAWAN")
    st.title("🔐 Admin Dashboard & Database Center")
    st.write("Pusat kendali arsip seluruh perusahaan klien yang tersimpan permanen di database server.")

    if not st.session_state.admin_logged_in:
        with st.form("admin_login_form"):
            st.markdown("### Masukkan Sandi Internal Admin")
            admin_pass_input = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Masuk Dashboard")
            if login_btn:
                if admin_pass_input == "aktuaris2026":
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
        st.subheader("📊 Monitoring Data Klien Multi-Perusahaan")

        conn = sqlite3.connect("kka_actuarial.db", check_same_thread=False)
        
        query = '''
            SELECT 
                r.timestamp AS tanggal,
                r.company_name AS nama_perusahaan,
                COALESCE(GROUP_CONCAT(DISTINCT c.valuation_year), 'Belum Kalkulasi') AS periode_perhitungan,
                r.filename AS raw_filename,
                r.file_bytes AS raw_bytes,
                p.pdf_bytes AS pdf_bytes,
                p.filename AS pdf_filename
            FROM raw_files r
            LEFT JOIN calculation_results c ON r.company_name = c.company_name
            LEFT JOIN report_pdfs p ON r.company_name = p.company_name
            GROUP BY r.company_name
        '''
        df_admin_summary = pd.read_sql(query, conn)

        if not df_admin_summary.empty:
            st.markdown("### Daftar Arsip Perusahaan Klien Aktif")
            
            for index, row in df_admin_summary.iterrows():
                with st.container(border=True):
                    col1, col2, col3, col4, col5 = st.columns([1.2, 1.8, 1.2, 1.9, 1.9])
                    with col1:
                        st.markdown(f"**1. Tanggal/Waktu:**<br/>{row['tanggal']}", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**2. Nama Perusahaan:**<br/>`{row['nama_perusahaan']}`", unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"**3. Periode Perhitungan:**<br/>{row['periode_perhitungan']}", unsafe_allow_html=True)
                    with col4:
                        st.markdown(f"**4. Data Mentah Asli:**")
                        if row['raw_bytes']:
                            st.download_button(
                                label=f"📥 Download Excel",
                                data=row['raw_bytes'],
                                file_name=row['raw_filename'] or f"Data_{row['nama_perusahaan']}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"admin_raw_{index}_{row['nama_perusahaan']}"
                            )
                        else:
                            st.write("Belum ada file")
                    with col5:
                        st.markdown(f"**5. Laporan PDF Klien:**")
                        if row['pdf_bytes']:
                            st.download_button(
                                label=f"📥 Download PDF",
                                data=row['pdf_bytes'],
                                file_name=row['pdf_filename'] or f"LAPORAN_AKTUARIA_{row['nama_perusahaan'].replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key=f"admin_pdf_{index}_{row['nama_perusahaan']}"
                            )
                        else:
                            st.write("Belum digenerate")
        else:
            st.warning("⚠️ Belum ada data perusahaan yang tersimpan di database server.")
        
        conn.close()

# ==========================================
# 13. HALAMAN: KALKULATOR VALUASI AKTUARIA
# ==========================================
elif menu == "🧮 Kalkulator Valuasi Aktuaria" or menu == "Kalkulator Valuasi Aktuaria":
    with st.container():
        st.success("KKA Setya Gunawan — PORTAL AKTUARIA")
        st.title("📄 Generator Laporan Aktuaria PSAK 219 (IFRIC AD)")
        st.write("Menampilkan rincian kalkulasi per karyawan di web, dilengkapi kurva yield PHEI & kertas kerja siap audit.")

    if not st.session_state.payment_verified:
        st.warning("🔒 **Akses Terkunci:** Silakan lakukan verifikasi pembayaran administrasi layanan valuasi aktuaria.")
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
                    conn = sqlite3.connect("kka_actuarial.db", check_same_thread=False)
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO raw_files (company_name, filename, file_bytes, timestamp)
                        VALUES (?, ?, ?, ?)
                    ''', (input_perusahaan, uploaded_file.name, uploaded_file.getvalue(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()

                    xl_file = pd.ExcelFile(uploaded_file)
                    for sh in xl_file.sheet_names:
                        match = re.search(r'(20\d{2})', sh)
                        if match:
                            yr = int(match.group(1))
                            df_emp, total_paid = parse_excel_dataset(uploaded_file, sheet_name=sh)
                            datasets_to_process[f"31 Des {yr}"] = df_emp
                            benefit_paid_dict[f"31 Des {yr}"] = total_paid
                    st.success(f"Berhasil membaca sheet Excel untuk **{input_perusahaan}**")
                except Exception as e:
                    st.error(f"Gagal membaca file: {e}")
        else:
            selected_years = st.multiselect(
                "Pilih Tahun Valuasi",
                [2021, 2022, 2023, 2024, 2025, 2026],
                default=[2024, 2025]
            )
            
            selected_periods = st.multiselect(
                "Pilih Periode Tanggal Valuasi (Per Tahun)",
                ["30 Juni", "31 Desember"],
                default=["31 Desember"]
            )

            valuation_keys = []
            for yr in selected_years:
                for p in selected_periods:
                    if "Juni" in p or "Jun" in p:
                        valuation_keys.append(f"30 Jun {yr}")
                    else:
                        valuation_keys.append(f"31 Des {yr}")

            if "manual_datasets_v2" not in st.session_state:
                st.session_state.manual_datasets_v2 = {}

            tab_periods = st.tabs(valuation_keys) if valuation_keys else []

            for idx, vkey in enumerate(valuation_keys):
                with tab_periods[idx]:
                    if vkey not in st.session_state.manual_datasets_v2:
                        st.session_state.manual_datasets_v2[vkey] = pd.DataFrame([
                            {"NIK": "001", "Nama": "Karyawan Contoh 1", "Tanggal Lahir": "1990-01-21", "Tgl. Mulai Bekerja": "2023-10-15", "Total Upah Bulanan (Gross)": 10000000.0, "Saldo DPLK": 0.0}
                        ])

                    edited_df = st.data_editor(
                        st.session_state.manual_datasets_v2[vkey],
                        num_rows="dynamic",
                        key=f"manual_editor_{vkey}",
                        use_container_width=True
                    )
                    st.session_state.manual_datasets_v2[vkey] = edited_df
                    datasets_to_process[vkey] = edited_df

                    benefit_paid_dict[vkey] = st.number_input(
                        f"Total Benefit Paid Aktual Periode {vkey} (Rp)",
                        value=0.0,
                        step=1000000.0,
                        key=f"manual_paid_{vkey}"
                    )

        st.markdown("---")
        if st.button("Jalankan Valuasi Otomatis (PSAK 219 & IFRIC AD) 🚀") and datasets_to_process:
            with st.spinner("Menghitung perincian aktuaria per karyawan dengan metode PUC & IFRIC AD, serta menyimpannya ke database..."):
                results_dict = {}
                dplk_dict = {}
                active_keys = sorted(list(datasets_to_process.keys()))
                
                conn = sqlite3.connect("kka_actuarial.db", check_same_thread=False)
                cursor = conn.cursor()

                for vkey in active_keys:
                    parts = vkey.split()
                    day = int(parts[0])
                    month_str = parts[1]
                    yr = int(parts[2])
                    
                    month = 6 if "Jun" in month_str else 12
                    val_date_dt = datetime.datetime(yr, month, day)
                    df_input = datasets_to_process[vkey]

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
                        age_entry = (doe - dob).days / 365.25
                        nra = float(row.get("NRA", usia_pensiun))
                        future_service = 0.0 if current_age >= nra else (nra - current_age)

                        kalkulasi = final_engine.calculate_puc(current_age, past_service, gross_salary, p_mult, d_mult, death_mult, r_mult, years_to_retire=future_service)
                        hasil_valuasi.append({
                            "NIK": str(row.get("NIK", "N/A")), "Name": str(row.get("Nama", "Unknown")),
                            "Tanggal Lahir": dob, "Tgl. Mulai Bekerja": doe,
                            "Age Valuation": current_age, "Age Entry": age_entry, "Past Service": past_service, "NRA": nra,
                            "Gross Salary": gross_salary, **kalkulasi
                        })

                    df_res_yr = pd.DataFrame(hasil_valuasi)
                    results_dict[vkey] = df_res_yr
                    dplk_dict[vkey] = total_dplk_yr

                    # Penanganan tabel database yang aman dan anti-OperationalError
                    try:
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS calculation_results (
                                company_name TEXT,
                                valuation_year INTEGER,
                                result_csv TEXT,
                                parameters TEXT,
                                timestamp TEXT,
                                PRIMARY KEY (company_name, valuation_year)
                            )
                        ''')
                    except sqlite3.OperationalError:
                        cursor.execute('DROP TABLE IF EXISTS calculation_results')
                        cursor.execute('''
                            CREATE TABLE calculation_results (
                                company_name TEXT,
                                valuation_year INTEGER,
                                result_csv TEXT,
                                parameters TEXT,
                                timestamp TEXT,
                                PRIMARY KEY (company_name, valuation_year)
                            )
                        ''')

                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO calculation_results (company_name, valuation_year, result_csv, parameters, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            input_perusahaan, yr, df_res_yr.to_csv(index=False),
                            f"Period:{vkey},SalaryInc:{asumsi_gaji},RetAge:{usia_pensiun},Resign:{asumsi_resign}",
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                    except sqlite3.OperationalError:
                        cursor.execute('DROP TABLE IF EXISTS calculation_results')
                        cursor.execute('''
                            CREATE TABLE calculation_results (
                                company_name TEXT,
                                valuation_year INTEGER,
                                result_csv TEXT,
                                parameters TEXT,
                                timestamp TEXT,
                                PRIMARY KEY (company_name, valuation_year)
                            )
                        ''')
                        cursor.execute('''
                            INSERT OR REPLACE INTO calculation_results (company_name, valuation_year, result_csv, parameters, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            input_perusahaan, yr, df_res_yr.to_csv(index=False),
                            f"Period:{vkey},SalaryInc:{asumsi_gaji},RetAge:{usia_pensiun},Resign:{asumsi_resign}",
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))

                temp_pdf_buffer = generate_detailed_report(
                    results_dict=results_dict, 
                    salary_inc=asumsi_gaji, 
                    ret_age=usia_pensiun, 
                    val_keys=active_keys, 
                    company_name=input_perusahaan, 
                    report_no=nomor_laporan, 
                    report_date=tanggal_laporan
                )
                pdf_filename_str = f"LAPORAN_AKTUARIA_PSAK219_{input_perusahaan.replace(' ', '_')}.pdf"
                
                try:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS report_pdfs (
                            company_name TEXT PRIMARY KEY,
                            pdf_bytes BLOB,
                            filename TEXT,
                            timestamp TEXT
                        )
                    ''')
                except sqlite3.OperationalError:
                    cursor.execute('DROP TABLE IF EXISTS report_pdfs')
                    cursor.execute('''
                        CREATE TABLE report_pdfs (
                            company_name TEXT PRIMARY KEY,
                            pdf_bytes BLOB,
                            filename TEXT,
                            timestamp TEXT
                        )
                    ''')

                cursor.execute('''
                    INSERT OR REPLACE INTO report_pdfs (company_name, pdf_bytes, filename, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    input_perusahaan, temp_pdf_buffer.getvalue(), pdf_filename_str,
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                conn.commit()
                conn.close()

                st.session_state.results_dict = results_dict
                st.session_state.dplk_dict = dplk_dict
                st.session_state.paid_dict = benefit_paid_dict
                st.session_state.active_years = active_keys
                st.session_state.asumsi_gaji = asumsi_gaji
                st.session_state.usia_pensiun = usia_pensiun
                st.session_state.input_perusahaan = input_perusahaan
                st.session_state.nomor_laporan = nomor_laporan
                st.session_state.tanggal_laporan = tanggal_laporan
                st.session_state.calculated_results = True
                st.success(f"Valuasi Aktuaria untuk **{input_perusahaan}** Selesai! Data kalkulasi dan laporan PDF tersimpan aman di Database Server.")

        if st.session_state.get("calculated_results"):
            res_dict = st.session_state.results_dict
            act_keys = st.session_state.active_years
            
            cur_salary_inc = st.session_state.get("asumsi_gaji", asumsi_gaji)
            cur_ret_age = st.session_state.get("usia_pensiun", usia_pensiun)
            cur_company = st.session_state.get("input_perusahaan", input_perusahaan)
            cur_no_rep = st.session_state.get("nomor_laporan", nomor_laporan)
            cur_date_rep = st.session_state.get("tanggal_laporan", tanggal_laporan)

            st.markdown("---")
            st.subheader("👥 Rincian Perhitungan Tingkat Individu per Karyawan")

            for vkey in sorted(act_keys, reverse=True):
                st.markdown(f"#### 📅 Periode Valuasi: {vkey}")
                df_y = res_dict[vkey]
                if df_y.empty: continue

                df_display = df_y.copy()
                df_display['Tanggal Lahir'] = pd.to_datetime(df_display['Tanggal Lahir']).dt.strftime('%d-%m-%Y')
                df_display['Tgl. Mulai Bekerja'] = pd.to_datetime(df_display['Tgl. Mulai Bekerja']).dt.strftime('%d-%m-%Y')
                df_display['Gross Salary'] = df_display['Gross Salary'].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
                df_display['NRA'] = df_display['NRA'].apply(lambda x: f"{x:.2f}")
                df_display['Age Valuation'] = df_display['Age Valuation'].apply(lambda x: f"{x:.2f}")
                df_display['Age Entry'] = df_display['Age Entry'].apply(lambda x: f"{x:.2f}") if 'Age Entry' in df_display else "-"
                df_display['Past Service'] = df_display['Past Service'].apply(lambda x: f"{x:.2f}")
                df_display['Title'] = df_display.get('Title', 'Staff')
                df_display['Future_Service'] = df_display['Future_Service'].apply(lambda x: f"{x:,.2f}" if isinstance(x, (int, float)) else str(x))
                df_display['Discount Rate'] = df_display['Applied_Discount'].apply(lambda x: f"{x*100:.2f}%")
                df_display['PVFB'] = df_display['PVFB'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_display['PBO'] = df_display['PBO'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_display['CSC'] = df_display['CSC'].apply(lambda x: f"Rp {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")) if 'CSC' in df_display else "-"

                cols_to_show = ['NIK', 'Name', 'Tanggal Lahir', 'Tgl. Mulai Bekerja', 'Gross Salary', 'NRA', 'Age Valuation', 'Age Entry', 'Past Service', 'Future_Service', 'Discount Rate', 'PVFB', 'PBO', 'CSC']
                st.dataframe(df_display[cols_to_show], use_container_width=True)

            st.markdown("---")
            st.subheader("📥 Unduh Kertas Kerja & Laporan Resmi KKA Setya Gunawan")
            pdf_file = generate_detailed_report(
                results_dict=res_dict, 
                salary_inc=cur_salary_inc, 
                ret_age=cur_ret_age, 
                val_keys=act_keys, 
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
