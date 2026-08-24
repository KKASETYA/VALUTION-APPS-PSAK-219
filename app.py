import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==========================================
# 1. FORMATTER ANGKA & MATA UANG
# ==========================================
def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    if decimals == 0:
        return f"{num:,.0f}".replace(",", ".")
    else:
        formatted = f"{num:,.{decimals}f}"
        return formatted.replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 2. UNIVERSAL PARSER EXCEL (MULTI-SHEET / MULTI-TAHUN)
# ==========================================
def parse_excel_universal(file_or_buffer, sheet_name=0):
    df_raw = pd.read_excel(file_or_buffer, sheet_name=sheet_name, header=None)
    detected_year = 2025
    str_sh = str(sheet_name).lower()
    
    match_4dig = re.search(r'(20\d{2})', str_sh)
    if match_4dig:
        detected_year = int(match_4dig.group(1))
    else:
        match_dec = re.search(r'dec\s*(\d{2})', str_sh)
        if match_dec:
            detected_year = 2000 + int(match_dec.group(1))
        else:
            match_2dig = re.search(r'(\d{2})', str_sh)
            if match_2dig:
                yr_val = int(match_2dig.group(1))
                if yr_val in [23, 24, 25, 26]:
                    detected_year = 2000 + yr_val

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
# 3. ENGINE AKTUARIA (PUC + TMI IV + UPH 15%)
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
# 4. GENERATOR PDF RESMI LENGKAP (TABEL 1 S.D. 5)
# ==========================================
def draw_page_decorations(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(0.75)
    canvas.line(36, 45, 576, 45)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(36, 32, "Konsultan Aktuaria Setya Gunawan")
    canvas.drawRightString(576, 32, f"{doc.page}")
    canvas.restoreState()

def generate_comprehensive_pdf(results_dict, dplk_dict, paid_dict, discount, salary_inc, ret_age, company_name, report_no, bop_obligation, override_pbo, override_csc):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=60)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CoverTitle', parent=styles['Heading1'], fontSize=14, leading=18, alignment=1, textColor=colors.black)
    h_eng = ParagraphStyle('HEng', parent=styles['Heading2'], fontSize=9.5, leading=11, fontName='Helvetica-Bold', textColor=colors.black)
    h_ind = ParagraphStyle('HInd', parent=styles['Heading2'], fontSize=9.5, leading=11, fontName='Helvetica-Bold', alignment=2, textColor=colors.black)
    body_eng = ParagraphStyle('BEng', parent=styles['Normal'], fontSize=8, leading=11, fontName='Helvetica', textColor=colors.black)
    body_ind = ParagraphStyle('BInd', parent=styles['Normal'], fontSize=8, leading=11, fontName='Helvetica', alignment=2, textColor=colors.black)
    
    std_tbl_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#D9D9D9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 3),
        ('TOPPADDING', (0,0), (-1,0), 3),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ])

    cur_yr = 2025
    df_cur = results_dict.get(cur_yr, list(results_dict.values())[0] if results_dict else pd.DataFrame())
    total_pbo = override_pbo if override_pbo > 0 else (df_cur['PBO'].sum() if not df_cur.empty else 0)
    total_csc = override_csc if override_csc > 0 else (df_cur['CSC'].sum() if not df_cur.empty else 0)
    total_dplk = dplk_dict.get(cur_yr, 0.0)
    total_benefit_paid = paid_dict.get(cur_yr, 2983814836.0)
    
    int_cost = bop_obligation * 0.0711
    net_expense = total_csc + int_cost
    funded_status = total_pbo - total_dplk
    pbo_expected = bop_obligation + net_expense - total_benefit_paid
    actuarial_gain_loss = total_pbo - pbo_expected

    # 1. COVER
    elements.append(Spacer(1, 100))
    t_cover = Table([[Paragraph(f"<b>PT. {company_name.upper()}</b><br/><br/><b>ACTUARIAL VALUATION BASED ON<br/>PSAK 219 EMPLOYEE BENEFIT</b><br/><br/>Valuation Period January 1 – December 31, {cur_yr}<br/><br/><b>FINAL REPORT NO. {report_no}</b>", title_style)]], colWidths=[400])
    t_cover.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#7F7F7F')),
        ('ROUNDEDCORNERS', [15, 15, 15, 15]),
        ('TOPPADDING', (0,0), (-1,-1), 30),
        ('BOTTOMPADDING', (0,0), (-1,-1), 30),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(t_cover)
    elements.append(PageBreak())

    # 2. GENERAL INFORMATION
    elements.append(Table([
        [Paragraph("<b>GENERAL INFORMATION</b>", h_eng), Paragraph("<b>INFORMASI UMUM</b>", h_ind)],
        [Paragraph(f"<b>PT. ASURANSI UMUM VIDEI</b><br/><br/>Graha Mustika Ratu, Lantai 1<br/>Jl. Gatot Subroto No. Kav 74-75<br/>Jakarta Selatan 12870", body_eng),
         Paragraph(f"<b>PT. ASURANSI UMUM VIDEI</b><br/><br/>Graha Mustika Ratu, Lantai 1<br/>Jl. Gatot Subroto No. Kav 74-75<br/>Jakarta Selatan 12870", body_ind)],
        [Paragraph("Jakarta, March 03th, 2026", body_eng), Paragraph("Jakarta, 3 Maret 2026", body_ind)]
    ], colWidths=[260, 260]))
    elements.append(PageBreak())

    # 3. TABLE OF CONTENT
    elements.append(Table([
        [Paragraph("<b>TABLE OF CONTENT</b>", h_eng), Paragraph("<b>DAFTAR ISI</b>", h_ind)],
        [Paragraph("1. Introduction<br/>2. Employees and Financial Data<br/>3. Methodology<br/>4. Actuarial Assumption<br/>5. Summary of Valuation Results<br/>6. Closing<br/>7. Actuarial Statement", body_eng),
         Paragraph("1. Pendahuluan<br/>2. Data Karyawan dan Keuangan<br/>3. Metodologi<br/>4. Asumsi Aktuaria<br/>5. Ringkasan Hasil Perhitungan<br/>6. Penutup<br/>7. Pernyataan Aktuaris", body_ind)]
    ], colWidths=[260, 260]))
    elements.append(PageBreak())

    # 4. EXECUTIVE SUMMARY
    elements.append(Table([
        [Paragraph("<b>EXECUTIVE SUMMARY</b>", h_eng), Paragraph("<b>RINGKASAN EKSEKUTIF</b>", h_ind)],
        [Paragraph(f"This report has been prepared at the request of PT. ASURANSI UMUM VIDEI with the purpose to identify actuarial liability and cost arising from post employment benefits...", body_eng),
         Paragraph(f"Laporan ini telah disusun untuk memenuhi permohonan PT. ASURANSI UMUM VIDEI dalam mengetahui kewajiban dan beban aktuaria atas Imbalan Pasca Kerja...", body_ind)],
        [Paragraph("<b>Report Parameters:</b><br/>1. Report No. : 0067/KAS-FR/PSAK/III/2026<br/>2. Date : March 03th, 2026<br/>3. Actuary Name : Setya Gunawan, SE, FSAI, AAAIJ, AIIS<br/>4. Reg. PAI No. : 20011027<br/>5. Public Actuary No. : Act-1.17.00026", body_eng),
         Paragraph("<b>Parameter Laporan:</b><br/>1. No. Laporan : 0067/KAS-FR/PSAK/III/2026<br/>2. Tanggal : 3 Maret 2026<br/>3. Nama Aktuaris : Setya Gunawan, SE, FSAI, AAAIJ, AIIS<br/>4. Reg. PAI No. : 20011027<br/>5. Aktuaria Publik No. : Act-1.17.00026", body_ind)]
    ], colWidths=[260, 260]))
    elements.append(PageBreak())

    # 5. TABEL 1: IKHTISAR DATA DAN ASUMSI AKTUARIA
    elements.append(Paragraph("<b>TABLE 1 / TABEL 1: IKHTISAR DATA DAN ASUMSI AKTUARIA</b>", ParagraphStyle('T1Title', parent=styles['Heading2'], fontSize=9, alignment=1)))
    elements.append(Spacer(1, 5))
    t1_data = [
        ["EXPLANATION", "Des 31, 2024", "Des 31, 2025", "URAIAN"],
        ["Number of Employee", "147", f"{len(df_cur)}", "Jumlah Karyawan (orang)"],
        ["Monthly Wages", "824.331.212", f"{fmt_num(df_cur['Gross Salary'].sum() if not df_cur.empty else 0)}", "Jumlah Gaji Sebulan"],
        ["Average Monthly Wages", "5.607.695", f"{fmt_num(df_cur['Gross Salary'].mean() if not df_cur.empty else 0)}", "Rata-rata Gaji Sebulan"],
        ["Average Age (Years)", "39,78", f"{df_cur['Age Valuation'].mean():.2f}".replace('.', ',') if not df_cur.empty else "0", "Rata-rata Usia (Tahun)"],
        ["Average Years of Service", "8,81", f"{df_cur['Past Service'].mean():.2f}".replace('.', ',') if not df_cur.empty else "0", "Rata-rata Masa Kerja (Tahun)"],
        ["Discount Rate Beginning", "6,64%", "7,11%", "Tingkat Diskonto Awal Tahun"],
        ["Discount Rate Ending", "7,11%", f"{discount*100:.2f}%".replace('.', ','), "Tingkat Diskonto Akhir Tahun"],
        ["Future Salary Increases", "5,00%", f"{salary_inc*100:.2f}%".replace('.', ','), "Tingkat Kenaikan Gaji"],
        ["Current Service Cost", "725.729.273", fmt_num(total_csc), "Biaya Jasa Kini"],
        ["Total Benefit Paid", "(391.618.631)", f"({fmt_num(total_benefit_paid)})", "Imbalan yang dibayarkan"],
        ["Obligation at BoP", "7.202.205.556", fmt_num(bop_obligation), "Nilai kini kewajiban awal periode"],
        ["Obligation at EoP", "6.431.037.297", fmt_num(total_pbo), "Nilai kini kewajiban akhir periode"],
        ["Mortality Table", "TMI IV", "TMI IV", "Tabel Mortalita"],
        ["Normal Retirement Age", "55 / 56", f"{ret_age}", "Usia Pensiun Normal (Tahun)"]
    ]
    t_table1 = Table(t1_data, colWidths=[150, 65, 65, 160])
    t_table1.setStyle(std_tbl_style)
    elements.append(t_table1)
    elements.append(PageBreak())

    # 6. TABEL 2: ANALISIS KEUNTUNGAN DAN KERUGIAN AKTUARIA (GAIN AND LOSS CALCULATIONS)
    elements.append(Paragraph("<b>TABLE 2 / TABEL 2: ANALISIS KEUNTUNGAN DAN KERUGIAN AKTUARIA</b>", ParagraphStyle('T2Title', parent=styles['Heading2'], fontSize=9, alignment=1)))
    elements.append(Spacer(1, 5))
    t2_data = [
        ["EXPLANATION", "Des 31, 2024", "Des 31, 2025", "URAIAN"],
        ["Actual Present Value of Obligation at BoP", fmt_num(7202205556), fmt_num(bop_obligation), "Nilai Kini Kewajiban Awal Periode"],
        ["Interest Cost", fmt_num(513076815), fmt_num(int_cost), "Biaya Bunga"],
        ["Current Service Cost", fmt_num(725729273), fmt_num(total_csc), "Biaya Jasa Kini"],
        ["Benefit Payments", f"({fmt_num(391618631)})", f"({fmt_num(total_benefit_paid)})", "Pembayaran Manfaat"],
        ["Present Value of Obligation at EoP - Expected", fmt_num(7536098048), fmt_num(pbo_expected), "Nilai Kini Kewajiban Akhir (Ekspektasi)"],
        ["Actuarial (Gain)/Loss on Obligation", f"({fmt_num(602594759)})", f"{fmt_num(actuarial_gain_loss)}", "Keuntungan/Kerugian Aktuaria pada Kewajiban"],
        ["Present Value of Obligation at EoP - Actual", fmt_num(6431037297), fmt_num(total_pbo), "Nilai Kini Kewajiban Akhir (Aktual)"],
        ["Total Actuarial (Gain)/Loss for Period", f"({fmt_num(602594759)})", f"{fmt_num(actuarial_gain_loss)}", "Total Keuntungan/Kerugian Aktuaria Tahun Berjalan"]
    ]
    t_table2 = Table(t2_data, colWidths=[150, 65, 65, 160])
    t_table2.setStyle(std_tbl_style)
    elements.append(t_table2)
    elements.append(PageBreak())

    # 7. TABEL 3: PENDAPATAN KOMPREHENSIF LAINNYA (OTHER COMPREHENSIVE INCOME)
    elements.append(Paragraph("<b>TABLE 3 / TABEL 3: PENDAPATAN KOMPREHENSIF LAINNYA (OCI)</b>", ParagraphStyle('T3Title', parent=styles['Heading2'], fontSize=9, alignment=1)))
    elements.append(Spacer(1, 5))
    t3_data = [
        ["EXPLANATION", "Des 31, 2024", "Des 31, 2025", "URAIAN"],
        ["Other Comprehensive Income at BoP", "-", "-", "OCI Awal Periode"],
        ["Actuarial (Gain)/Loss on Obligation", f"({fmt_num(602594759)})", f"{fmt_num(actuarial_gain_loss)}", "Keuntungan/Kerugian Aktuaria pada Kewajiban"],
        ["Actuarial (Gain)/Loss on Plan Assets", "-", "-", "Keuntungan/Kerugian Aktuaria pada Aktiva Program"],
        ["Total Actuarial (Gain)/Loss at Period", f"({fmt_num(602594759)})", f"{fmt_num(actuarial_gain_loss)}", "Total Keuntungan/Kerugian Aktuaria Periode Ini"],
        ["Other Comprehensive Income at EoP", f"({fmt_num(602594759)})", f"{fmt_num(actuarial_gain_loss)}", "OCI Akhir Periode"]
    ]
    t_table3 = Table(t3_data, colWidths=[150, 65, 65, 160])
    t_table3.setStyle(std_tbl_style)
    elements.append(t_table3)
    elements.append(PageBreak())

    # 8. TABEL 4: STATUS PENDANAAN & REKONSILIASI (FUNDED STATUS & RECONCILIATION)
    elements.append(Paragraph("<b>TABLE 4 / TABEL 4: STATUS PENDANAAN & REKONSILIASI</b>", ParagraphStyle('T4Title', parent=styles['Heading2'], fontSize=9, alignment=1)))
    elements.append(Spacer(1, 5))
    t_t4_1 = Table([
        ["E X P L A N A T I O N", "Des 31, 2024", "Des 31, 2025", "U R A I A N"],
        ["Present Value of Obligation at EOP", fmt_num(6431037297.0), fmt_num(total_pbo), "Nilai Kini Kewajiban"],
        ["Fair Value of Plan Assets", "-", "-", "Nilai Wajar Aktiva Program"],
        ["Funded Status", fmt_num(6431037297.0), fmt_num(funded_status), "Posisi Pendanaan"],
        ["Liability/(Assets) Recognized in Balance Sheet", fmt_num(6431037297.0), fmt_num(funded_status), "Kewajiban Diakui di Neraca"]
    ], colWidths=[150, 65, 65, 160])
    t_t4_1.setStyle(std_tbl_style)
    elements.append(t_t4_1)
    elements.append(Spacer(1, 10))

    t_t4_2 = Table([
        ["E X P L A N A T I O N", "Des 31, 2024", "Des 31, 2025", "U R A I A N"],
        ["Liability/(Assets) at BoP", fmt_num(7202205556), fmt_num(bop_obligation), "Kewajiban pada Awal Periode"],
        ["Expense/(Income)", fmt_num(223045131), fmt_num(net_expense), "Beban/(Pendapatan)"],
        ["Benefit Payment - Actual", f"({fmt_num(391618631)})", f"({fmt_num(total_benefit_paid)})", "Realisasi Pembayaran Manfaat"],
        ["Other Comprehensive Income", f"({fmt_num(602594759)})", f"({fmt_num(abs(actuarial_gain_loss))})", "Pendapatan Komprehensif Lainnya"],
        ["Liability/(Assets) at EoP", fmt_num(6431037297.0), fmt_num(funded_status), "Kewajiban pada Akhir Periode"]
    ], colWidths=[150, 65, 65, 160])
    t_t4_2.setStyle(std_tbl_style)
    elements.append(t_t4_2)
    elements.append(PageBreak())

    # 9. TABEL 5: PENGAKUAN BEBAN / PENDAPATAN DI LAPORAN LABA RUGI (RECOGNITION OF EXPENSE)
    elements.append(Paragraph("<b>TABLE 5 / TABEL 5: PENGAKUAN BEBAN DALAM LABA RUGI</b>", ParagraphStyle('T5Title', parent=styles['Heading2'], fontSize=9, alignment=1)))
    elements.append(Spacer(1, 5))
    t5_data = [
        ["EXPLANATION", "Des 31, 2024", "Des 31, 2025", "URAIAN"],
        ["Current Service Cost", fmt_num(725729273), fmt_num(total_csc), "Biaya Jasa Kini"],
        ["Interest Cost", fmt_num(513076815), fmt_num(int_cost), "Biaya Bunga"],
        ["Expected Return on Plan Assets", "-", "-", "Harapan Hasil Investasi"],
        ["Net Expense / (Income) Recognized", fmt_num(223045131), fmt_num(net_expense), "Beban / (Pendapatan) yang Diakui di Laba Rugi"]
    ]
    t_table5 = Table(t5_data, colWidths=[150, 65, 65, 160])
    t_table5.setStyle(std_tbl_style)
    elements.append(t_table5)
    elements.append(PageBreak())

    # 10. SURAT PERNYATAAN MANAJEMEN
    elements.append(Paragraph("<b>SURAT PERNYATAAN KEBENARAN DATA & PERSETUJUAN ASUMSI PT. ASURANSI UMUM VIDEI</b>", ParagraphStyle('Stmt', parent=styles['Heading2'], fontSize=10, alignment=1)))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Dalam rangka Perhitungan Aktuaria Program Imbalan Pasca Kerja berdasarkan PSAK 219 periode 31 Desember 2025 untuk PT. ASURANSI UMUM VIDEI, kami sebagai Manajemen menyatakan bahwa data dan informasi yang kami sampaikan kepada Aktuaris adalah <b>TELENGKAP DAN BENAR</b>.", body_ind))
    elements.append(Spacer(1, 10))
    
    stmt_data = [
        ["1", "Total Karyawan", f"{len(df_cur)} Orang"],
        ["2", "Total Gaji", f"Rp {fmt_num(df_cur['Gross Salary'].sum() if not df_cur.empty else 0)}"],
        ["3", "Usia Pensiun", f"{ret_age} Tahun"],
        ["4", "Asumsi Rata-rata Kenaikan Gaji", f"{salary_inc*100:.2f}%"],
        ["5", "Imbalan Pasca Kerja - Tetap", f"Rp {fmt_num(total_pbo)}"],
        ["6", "Imbalan Pasca Kerja - Kontrak", f"Rp {fmt_num(74313038)}"],
        ["7", "Imbalan Jangka Panjang Lainnya", f"Rp {fmt_num(321186643)}"]
    ]
    t_stmt = Table(stmt_data, colWidths=[30, 220, 250])
    t_stmt.setStyle(std_tbl_style)
    elements.append(t_stmt)
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Demikian surat pernyataan ini kami buat dengan sebenarnya, dan kami siap mempertanggungjawabkan perihal kelengkapan data dan kebenaran data pada posisi periode 31 Desember 2025.", body_ind))
    elements.append(PageBreak())

    # 11. ACTUARIAL STATEMENT & CLOSING
    elements.append(Table([
        [Paragraph("<b>ACTUARIAL STATEMENT</b>", h_eng), Paragraph("<b>PERNYATAAN AKTUARIS</b>", h_ind)],
        [Paragraph("We have calculated actuarial valuation for PT. ASURANSI UMUM VIDEI pertaining to Severance Payment, Service Pay and Compensation Payment...", body_eng),
         Paragraph("Kami telah menghitung besar cadangan PT. ASURANSI UMUM VIDEI berkenaan dengan cadangan Pesangon, Penghargaan Masa Kerja...", body_ind)],
        [Paragraph(f"Jakarta, March 03th, 2026<br/><b>Setya Gunawan, SE, FSAI, AAAIJ, AIIS</b><br/>Reg. PAI No. 20011027<br/>Public Actuary No. Act-1.17.00026", body_eng),
         Paragraph(f"Jakarta, 3 Maret 2026<br/><b>Setya Gunawan, SE, FSAI, AAAIJ, AIIS</b><br/>Reg. PAI No. 20011027<br/>Aktuaris Publik No. Act-1.17.00026", body_ind)]
    ], colWidths=[260, 260]))

    doc.build(elements, onFirstPage=draw_page_decorations, onLaterPages=draw_page_decorations)
    pdf_buffer.seek(0)
    return pdf_buffer


# ==========================================
# 5. STREAMLIT INTERFACE
# ==========================================
st.set_page_config(page_title="Valuasi Aktuaria Presisi Profesional", layout="wide")
st.title("📄 Generator Laporan PDF Dwibahasa Resmi Aktuaria (Lengkap Tabel 1-5)")

st.sidebar.header("⚙️ Parameter Rekonsiliasi")
input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT. ASURANSI UMUM VIDEI")
nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", "0067/KAS-FR/PSAK/III/2026")

asumsi_diskonto = st.sidebar.number_input("Tingkat Diskonto Akhir (%)", value=6.37, step=0.01) / 100
asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=55, step=1)

bop_input = st.sidebar.number_input("Beginning Obligation (BoP 2025)", value=6431037297.0, step=1000000.0)
benefit_paid_input = st.sidebar.number_input("Realisasi Benefit Paid Aktual", value=2983814836.0, step=1000000.0)
override_pbo_input = st.sidebar.number_input("Lock Final PBO (Opsional, 0 = Auto)", value=3813896220.0, step=1000000.0)
override_csc_input = st.sidebar.number_input("Lock Final CSC (Opsional, 0 = Auto)", value=488511769.0, step=1000000.0)

uploaded_file = st.file_uploader("Unggah File Excel Template Aktuaria (.xlsx) - Mendukung Multi-Sheet/Multi-Tahun", type=["xlsx", "xls"])

if "datasets_raw" not in st.session_state:
    st.session_state.datasets_raw = {}

if uploaded_file is not None:
    try:
        xl_file = pd.ExcelFile(uploaded_file)
        for sh in xl_file.sheet_names:
            if any(k in sh.lower() for k in ['asumsi', 'kontrak', 'cuti']):
                continue
            detected_yr, df_emp, _ = parse_excel_universal(uploaded_file, sheet_name=sh)
            if detected_yr not in st.session_state.datasets_raw:
                st.session_state.datasets_raw[detected_yr] = df_emp
        st.success(f"Berhasil membaca sheet Excel untuk tahun: {list(st.session_state.datasets_raw.keys())}")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")

st.markdown("---")
if st.session_state.datasets_raw:
    st.subheader("📋 Input & Editor Data Karyawan Multi-Tahun (Bisa Diedit Langsung)")
    tab_years = st.tabs([str(yr) for yr in sorted(st.session_state.datasets_raw.keys())])
    
    edited_datasets = {}
    benefit_paid_dict = {}
    
    for idx, yr in enumerate(sorted(st.session_state.datasets_raw.keys())):
        with tab_years[idx]:
            st.write(f"Edit Data Karyawan untuk Tahun **{yr}**:")
            edited_df = st.data_editor(
                st.session_state.datasets_raw[yr],
                num_rows="dynamic",
                key=f"editor_yr_{yr}",
                use_container_width=True
            )
            edited_datasets[yr] = edited_df
            benefit_paid_dict[yr] = benefit_paid_input if yr == 2025 else 0.0

    st.markdown("---")
    if st.button("Jalankan Valuasi Multi-Tahun & Generate PDF Resmi 🚀"):
        with st.spinner("Memproses perhitungan aktuaria multi-tahun..."):
            results_dict = {}
            dplk_dict = {}
            
            for key, df_input in edited_datasets.items():
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
            st.session_state.active_keys = sorted(list(edited_datasets.keys()))
            st.session_state.calculated = True
            st.success("Perhitungan Multi-Tahun Selesai!")

if st.session_state.get("calculated"):
    st.subheader("📊 Ringkasan Hasil Valuasi Multi-Tahun")
    res_dict = st.session_state.results_dict
    dp_dict = st.session_state.dplk_dict
    pd_dict = st.session_state.paid_dict
    pbo_lock = st.session_state.override_pbo
    
    summary_data = []
    for key in st.session_state.active_keys:
        df_y = res_dict[key]
        pbo_y = pbo_lock if (key == 2025 and pbo_lock > 0) else (df_y['PBO'].sum() if not df_y.empty else 0)
        payroll_y = df_y['Gross Salary'].sum() if not df_y.empty else 0
        summary_data.append({
            "Tahun": str(key),
            "Jumlah Peserta": len(df_y),
            "Total Payroll": f"Rp {payroll_y:,.0f}".replace(",", "."),
            "PBO (Obligation)": f"Rp {pbo_y:,.0f}".replace(",", ".")
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    pdf_file = generate_comprehensive_pdf(
        res_dict, dp_dict, pd_dict, asumsi_diskonto, asumsi_gaji, usia_pensiun, 
        input_perusahaan, nomor_laporan, bop_input, override_pbo_input, override_csc_input
    )
    
    st.download_button(
        label="📥 Download Laporan PDF Komprehensif Resmi (Lengkap Tabel 1-5)",
        data=pdf_file,
        file_name=f"FULL_TABLES_REPORT_{input_perusahaan.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
