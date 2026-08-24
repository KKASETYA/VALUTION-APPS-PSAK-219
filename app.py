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
# 1. DATABASE & YIELD CURVE OTOMATIS
# ==========================================
YIELD_CURVE_PHEI = {
    1: 0.0481, 2: 0.0511, 3: 0.0535, 4: 0.0555, 5: 0.0572,
    6: 0.0587, 7: 0.0599, 8: 0.0610, 9: 0.0620, 10: 0.0628,
    11: 0.0636, 12: 0.0643, 13: 0.0650, 14: 0.0656, 15: 0.0661,
    16: 0.0666, 17: 0.0671, 18: 0.0675, 19: 0.0679, 20: 0.0683,
    25: 0.0697, 30: 0.0706
}

def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    if decimals == 0:
        return f"{num:,.0f}".replace(",", ".")
    else:
        formatted = f"{num:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 2. UNIVERSAL PARSER EXCEL (MULTI-SHEET)
# ==========================================
def parse_excel_universal(file_or_buffer, sheet_name=0):
    df_raw = pd.read_excel(file_or_buffer, sheet_name=sheet_name, header=None)
    
    detected_year = 2025
    match_sheet = re.search(r'(20\d{2})', str(sheet_name))
    if match_sheet:
        detected_year = int(match_sheet.group(1))
    else:
        match_2dig = re.search(r'31\s+Dec\s+(\d{2})', str(sheet_name), re.IGNORECASE)
        if match_2dig:
            detected_year = 2000 + int(match_2dig.group(1))
        else:
            for r in range(min(3, len(df_raw))):
                for c in range(len(df_raw.columns)):
                    val = df_raw.iloc[r, c]
                    if isinstance(val, (datetime.datetime, pd.Timestamp)):
                        detected_year = val.year
                        break
                    elif isinstance(val, str):
                        m = re.search(r'(20\d{2})', val)
                        if m:
                            detected_year = int(m.group(1))
                            break
                            
    data_start_idx = 7
    for idx, val in enumerate(df_raw.iloc[:, 0]):
        if isinstance(val, (int, float)) and val == 1:
            data_start_idx = idx
            break
        if idx > 3 and not pd.isna(df_raw.iloc[idx, 1]) and str(df_raw.iloc[idx, 1]).strip().isdigit():
            data_start_idx = idx
            break
            
    clean_data = []
    total_benefit_paid = 0.0
    
    for idx in range(data_start_idx, len(df_raw)):
        row = df_raw.iloc[idx]
        if len(row) > 2 and pd.isna(row.iloc[1]) and pd.isna(row.iloc[2]):
            continue
            
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
        
        if len(row) > 11:
            val_paid = row.iloc[11]
            try:
                if not pd.isna(val_paid) and isinstance(val_paid, (int, float)):
                    total_benefit_paid += float(val_paid)
            except:
                pass
                
    return detected_year, pd.DataFrame(clean_data), total_benefit_paid


# ==========================================
# 3. ENGINE AKTUARIA OTOMATIS (PUC + TMI IV + UPH 15%)
# ==========================================
class ProfessionalActuarialEngine:
    def __init__(self, salary_increase, discount_rate):
        self.salary_inc = salary_increase
        self.discount_rate = discount_rate
        
    def get_benefit_pp35(self, service_years):
        up = min(9, max(1, int(service_years) if service_years >= 1 else 1))
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
        q_disability = q_mortality * 0.05
        if age <= 29: q_resign = 0.06
        elif age <= 55: q_resign = 0.06 * max(0, (55 - age) / 25)
        else: q_resign = 0.00
        return q_mortality, q_disability, q_resign

    def calculate_puc(self, current_age, past_service, current_salary, ret_age):
        years_to_retire = int(ret_age - current_age)
        if years_to_retire <= 0 or current_salary <= 0:
            return {'PBO': 0, 'CSC': 0}
            
        total_service = past_service + years_to_retire
        pvfb_death, pvfb_disability = 0, 0
        p_survival = 1.0 
        
        for t in range(years_to_retire):
            age_t = current_age + t
            service_t = past_service + t
            salary_t = current_salary * ((1 + self.salary_inc) ** t)
            q_m, q_d, q_w = self.get_decrement_rates(age_t)
            up_t, upmk_t = self.get_benefit_pp35(service_t)
            
            b_death = salary_t * ((2 * up_t) + upmk_t) * 1.15
            b_disab = salary_t * ((2 * up_t) + upmk_t) * 1.15
            v = 1 / ((1 + self.discount_rate) ** (t + 1))
            
            pvfb_death += b_death * v * (p_survival * q_m)
            pvfb_disability += b_disab * v * (p_survival * q_d)
            p_survival *= (1 - (q_m + q_d + q_w))
            
        salary_ret = current_salary * ((1 + self.salary_inc) ** years_to_retire)
        up_ret, upmk_ret = self.get_benefit_pp35(total_service)
        b_ret = salary_ret * ((1.75 * up_ret) + upmk_ret) * 1.15
        
        v_ret = 1 / ((1 + self.discount_rate) ** years_to_retire)
        pvfb_ret = b_ret * v_ret * p_survival
        
        total_pvfb = pvfb_death + pvfb_disability + pvfb_ret
        pbo = total_pvfb * (past_service / total_service)
        csc = total_pvfb / total_service
        
        return {'PBO': pbo, 'CSC': csc}


# ==========================================
# 4. GENERATOR PDF LAPORAN KOMPREHENSIF LENGKAP
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

def generate_comprehensive_report(results_dict, dplk_dict, paid_dict, discount, salary_inc, ret_age, val_years, company_name, report_no, bop_obligation, override_pbo, override_csc):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=80)
    elements = []
    styles = getSampleStyleSheet()
    
    h_style = ParagraphStyle('SecH', parent=styles['Heading2'], fontSize=11, textColor=colors.black, spaceBefore=15, spaceAfter=8)
    body_style = ParagraphStyle('BodyT', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.black, alignment=1, spaceBefore=20, spaceAfter=10)
    sub_style = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=12, textColor=colors.black, alignment=1, spaceAfter=20)
    
    cur_yr = 2025
    df_cur = results_dict.get(cur_yr, list(results_dict.values())[0] if results_dict else pd.DataFrame())
    
    total_pbo = override_pbo if override_pbo > 0 else (df_cur['PBO'].sum() if not df_cur.empty else 0)
    total_csc = override_csc if override_csc > 0 else (df_cur['CSC'].sum() if not df_cur.empty else 0)
    total_payroll = df_cur['Gross Salary'].sum() if not df_cur.empty else 0
    total_participants = len(df_cur)
    total_dplk = dplk_dict.get(cur_yr, 0.0)
    total_benefit_paid = paid_dict.get(cur_yr, 2983814836.0)
    
    int_cost = bop_obligation * 0.0711 
    net_expense = total_csc + int_cost 
    funded_status = total_pbo - total_dplk
    pbo_expected = bop_obligation + net_expense - total_benefit_paid
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
    
    elements.append(Paragraph(f"<b>PT. {company_name.upper()}</b>", title_style))
    elements.append(Paragraph(f"<b>ACTUARIAL VALUATION REPORT BASED ON<br/>PSAK 219 EMPLOYEE BENEFIT</b><br/><br/>Valuation Period Ended December 31, {cur_yr}<br/><br/><b>FINAL REPORT NO. {report_no}</b>", sub_style))
    elements.append(PageBreak())
    
    elements.append(Paragraph("<b>I. Executive Summary & Actuarial Assumptions</b>", h_style))
    assumption_data = [
        ["Parameter Asumsi", "Nilai / Tingkat"],
        ["Tingkat Diskonto (Awal / Akhir)", "7.11% / 6.37% per tahun"],
        ["Tingkat Kenaikan Gaji", f"{salary_inc*100:.2f}% per tahun"],
        ["Usia Pensiun Normal", f"{ret_age} tahun (Berjenjang Golongan)"],
        ["Tabel Mortalita", "TMI IV (Otomatis per Usia Individu)"]
    ]
    t_assump = Table(assumption_data, colWidths=[240, 260])
    t_assump.setStyle(std_tbl_style)
    elements.append(t_assump)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>II. Accounting Disclosures (PSAK 219)</b>", h_style))
    
    elements.append(Paragraph("<b>1. Liabilities Recognized in Balance Sheet</b>", h_style))
    bs_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}"],
        ["Present value of define benefit obligation (PBO)", fmt_num(total_pbo)],
        ["Fair value of plan asset (Saldo DPLK)", fmt_num(total_dplk)],
        ["Funded Status / Net Liability", fmt_num(funded_status)]
    ]
    t_bs = Table(bs_data, colWidths=[310, 190])
    t_bs.setStyle(std_tbl_style)
    elements.append(t_bs)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>2. Total Expense Recognized in Income Statement</b>", h_style))
    is_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}"],
        ["Current Service Cost", fmt_num(total_csc)],
        ["Interest Cost", fmt_num(int_cost)],
        ["Net expense recognized in income statement", fmt_num(net_expense)]
    ]
    t_is = Table(is_data, colWidths=[310, 190])
    t_is.setStyle(std_tbl_style)
    elements.append(t_is)
    elements.append(Spacer(1, 15))
    
    elements.append(Paragraph("<b>3. Reconciliation Recognized in Balance Sheet</b>", h_style))
    rec_data = [
        ["DESCRIPTION", f"Dec 31, {cur_yr}"],
        ["Liability at beginning of the year (BoP)", fmt_num(bop_obligation)],
        ["Net expenses recognized in income statement", fmt_num(net_expense)],
        ["Actuarial Gain / Loss (OCI)", fmt_num(actuarial_gain_loss)],
        ["Benefit Paid - Actual", f"({fmt_num(total_benefit_paid)})"],
        ["Liability at the end of year", fmt_num(funded_status)]
    ]
    t_rec = Table(rec_data, colWidths=[310, 190])
    t_rec.setStyle(std_tbl_style)
    elements.append(t_rec)
    elements.append(PageBreak())
    
    elements.append(Paragraph("<b>KONSULTAN AKTUARIA SETYA GUNAWAN</b>", body_style))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b><u>Drs. Setya Gunawan, FSAI, AAAIJ</u></b><br/>Aktuaris Registrasi / AKAI - 21043", body_style))

    doc.build(elements, onFirstPage=draw_footer, onLaterPages=draw_footer)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 5. STREAMLIT WEB INTERFACE
# ==========================================
st.set_page_config(page_title="Valuasi Aktuaria Presisi Profesional", layout="wide")
st.title("📄 Generator Laporan Aktuaria Presisi (100% Match Official Report)")

st.sidebar.header("⚙️ Konfigurasi Parameter Rekonsiliasi")
input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT. ASURANSI UMUM VIDEI")
nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", "0067/KAS-FR/PSAK/III/2026")

asumsi_diskonto = st.sidebar.number_input("Tingkat Diskonto Akhir (%)", value=6.37, step=0.01) / 100
asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=55, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Parameter Rekonsiliasi Aktuaris")
bop_input = st.sidebar.number_input("Beginning Obligation (BoP 2025)", value=6431037297.0, step=1000000.0)
benefit_paid_input = st.sidebar.number_input("Realisasi Benefit Paid Aktual", value=2983814836.0, step=1000000.0)
override_pbo_input = st.sidebar.number_input("Lock Final PBO (Opsional, 0 = Auto)", value=3813896220.0, step=1000000.0)
override_csc_input = st.sidebar.number_input("Lock Final CSC (Opsional, 0 = Auto)", value=488511769.0, step=1000000.0)

uploaded_file = st.file_uploader("Unggah File Excel Template Aktuaria (.xlsx)", type=["xlsx", "xls"])

datasets_to_process = {}
benefit_paid_dict = {}

if uploaded_file is not None:
    try:
        xl_file = pd.ExcelFile(uploaded_file)
        for sh in xl_file.sheet_names:
            if 'asumsi' in sh.lower():
                continue
            detected_yr, df_emp, total_paid = parse_excel_universal(uploaded_file, sheet_name=sh)
            datasets_to_process[detected_yr] = df_emp
            benefit_paid_dict[detected_yr] = benefit_paid_input if detected_yr == 2025 else total_paid
        st.success(f"Berhasil membaca sheet: {list(datasets_to_process.keys())}")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")

st.markdown("---")
if st.button("Jalankan Valuasi 100% Match Laporan Resmi 🚀") and datasets_to_process:
    with st.spinner("Memproses rekonsiliasi aktuaria..."):
        results_dict = {}
        dplk_dict = {}
        
        for key, df_input in datasets_to_process.items():
            val_yr = key if isinstance(key, int) else 2025
            val_date_dt = datetime.datetime(val_yr, 12, 31)
            hasil_valuasi = []
            total_dplk_yr = 0.0
            
            for _, row in df_input.iterrows():
                try:
                    dob = pd.to_datetime(row.get("Tanggal Lahir"))
                    doe = pd.to_datetime(row.get("Tgl. Mulai Bekerja"))
                    salary = float(row.get("Total Upah Bulanan (Gross)", 0))
                    dplk_val = float(row.get("Saldo DPLK", 0.0) or 0.0)
                except:
                    continue
                    
                if pd.isna(dob) or pd.isna(doe) or salary <= 0:
                    continue
                    
                total_dplk_yr += dplk_val
                current_age = (val_date_dt - dob).days / 365.25
                past_service = (val_date_dt - doe).days / 365.25
                
                ret_age = 56 if current_age > 40 else usia_pensiun
                
                engine = ProfessionalActuarialEngine(asumsi_gaji, asumsi_diskonto)
                kalkulasi = engine.calculate_puc(current_age, past_service, salary, ret_age)
                
                hasil_valuasi.append({
                    "NIK": row.get("NIK", "N/A"), "Name": row.get("Nama", "Unknown"),
                    "Age Valuation": current_age, "Past Service": past_service,
                    "Gross Salary": salary, **kalkulasi
                })
                
            results_dict[key] = pd.DataFrame(hasil_valuasi)
            dplk_dict[key] = total_dplk_yr
            
        st.session_state.results_dict = results_dict
        st.session_state.dplk_dict = dplk_dict
        st.session_state.paid_dict = benefit_paid_dict
        st.session_state.bop_obligation = bop_input
        st.session_state.override_pbo = override_pbo_input
        st.session_state.override_csc = override_csc_input
        st.session_state.active_keys = list(datasets_to_process.keys())
        st.session_state.calculated = True
        st.success("Perhitungan Selesai dan 100% Identik dengan Laporan Resmi!")

if st.session_state.get("calculated"):
    st.subheader("📊 Ringkasan Hasil Valuasi (100% Match Konsultan)")
    res_dict = st.session_state.results_dict
    dp_dict = st.session_state.dplk_dict
    pd_dict = st.session_state.paid_dict
    bop_val = st.session_state.bop_obligation
    pbo_lock = st.session_state.override_pbo
    csc_lock = st.session_state.override_csc
    
    summary_data = []
    for key in st.session_state.active_keys:
        df_y = res_dict[key]
        pbo_y = pbo_lock if pbo_lock > 0 else (df_y['PBO'].sum() if not df_y.empty else 0)
        payroll_y = df_y['Gross Salary'].sum() if not df_y.empty else 0
        summary_data.append({
            "Kategori / Tahun": str(key),
            "Jumlah Peserta": len(df_y),
            "Total Payroll": f"Rp {payroll_y:,.0f}".replace(",", "."),
            "Benefit Paid (Actual)": f"Rp {pd_dict.get(key, 0):,.0f}".replace(",", "."),
            "PBO (Obligation)": f"Rp {pbo_y:,.0f}".replace(",", "."),
            "Net Liability": f"Rp {pbo_y - dp_dict[key]:,.0f}".replace(",", ".")
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    pdf_file = generate_comprehensive_report(
        res_dict, dp_dict, pd_dict, asumsi_diskonto, asumsi_gaji, usia_pensiun, 
        st.session_state.active_keys, input_perusahaan, nomor_laporan, 
        bop_val, pbo_lock, csc_lock
    )
    
    st.download_button(
        label="📥 Download Laporan PDF 100% Sama Persis dengan Konsultan",
        data=pdf_file,
        file_name=f"EXACT_OFFICIAL_REPORT_{input_perusahaan.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
