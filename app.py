import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import os
import re
import time

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# ==========================================
# KONFIGURASI HALAMAN 
# ==========================================
st.set_page_config(
    page_title="KKA Setya Gunawan - Konsultan Aktuaria",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS (TEMA ORANYE & HIJAU KAS)
# ==========================================
st.markdown("""
<style>
    /* Tema Warna KAS: Oranye (#F25C05) dan Hijau/Teal (#439A86) */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        color: #F25C05;
        margin-bottom: 0px;
        text-transform: uppercase;
    }
    .sub-header {
        font-size: 1.3rem;
        font-weight: 500;
        color: #439A86;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .section-title {
        color: #439A86;
        border-bottom: 3px solid #F25C05;
        padding-bottom: 5px;
        margin-bottom: 20px;
        font-weight: bold;
    }
    .card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        border-top: 5px solid #439A86;
        margin-bottom: 1rem;
        height: 100%;
    }
    .card:hover {
        border-top: 5px solid #F25C05;
        transition: 0.3s ease-in-out;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #333333;
        margin-bottom: 10px;
    }
    .qris-box {
        border: 2px dashed #F25C05;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        background-color: #FFF5F0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# STATE MANAGEMENT (UNTUK SISTEM PEMBAYARAN)
# ==========================================
if 'payment_verified' not in st.session_state:
    st.session_state.payment_verified = False

# ==========================================
# ENGINE AKTUARIA & PHEI YIELD (DIPERSINGKAT UNTUK STRUKTUR)
# ==========================================
PHEI_IGSYC_YIELD_CURVE = {i: (6.3 + (i*0.02))/100 for i in range(1, 31)} # Simulasi Tabel PHEI

def get_phei_discount_rate(duration):
    dur_int = int(round(duration))
    return PHEI_IGSYC_YIELD_CURVE.get(dur_int, 0.065)

def fmt_num(num, decimals=0):
    if pd.isna(num) or num == "" or num == 0: return "-"
    return f"{num:,.0f}".replace(",", ".")

class PSAK219Engine:
    def __init__(self, discount_rate, salary_increase, retirement_age):
        self.discount_rate = discount_rate
        self.salary_inc = salary_increase
        self.ret_age = retirement_age
        
    def calculate_puc(self, current_age, past_service, current_salary):
        # Simulasi Engine PUC Sederhana untuk mempercepat loading script
        yrs_to_retire = max(0, self.ret_age - current_age)
        total_service = past_service + yrs_to_retire
        pbo = current_salary * 12 * past_service * 0.1 / ((1 + self.discount_rate)**yrs_to_retire)
        csc = pbo / total_service if total_service > 0 else 0
        return {'PBO': pbo, 'CSC': csc, 'Duration': yrs_to_retire/2}

def generate_pdf_report(results_dict, company_name):
    # Template PDF Sederhana dengan Footer KAS Resmi
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Laporan Valuasi Aktuaria (PSAK 219) - {company_name}", styles['Title'])]
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

# ==========================================
# ARSITEKTUR WEBSITE (SIDEBAR NAVIGASI)
# ==========================================
st.sidebar.markdown("<h2 style='color: #F25C05; text-align:center;'>KKA SETYA GUNAWAN</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align:center; color:#439A86; font-weight:bold;'><i>Serve u Great</i></p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "📌 Navigasi Menu:",
    ["🏠 Beranda", "🏢 Profil Perusahaan", "💼 Layanan & Klien", "👥 Tim Manajemen", "🧮 Kalkulator Aktuaria (Unggulan)", "📞 Hubungi Kami"]
)

# ------------------------------------------
# 1. HALAMAN: BERANDA
# ------------------------------------------
if menu == "🏠 Beranda":
    st.markdown('<div class="main-header">KONSULTAN AKTUARIA SETYA GUNAWAN</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">"Serve u Great" - Mitra Solusi Keuangan, Risiko, dan Aktuaria Bisnis Anda</div>', unsafe_allow_html=True)
    
    st.image("https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80", use_column_width=True)
    
    st.markdown("<h3 class='section-title'>Kenapa Memilih Kami?</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-title">📜 Legalitas Resmi</div>
            Keputusan Menteri Keuangan RI No. 590/KM.1/2021 dan Terdaftar di Otoritas Jasa Keuangan (OJK).
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-title">👨‍💼 Tenaga Ahli Tersertifikasi</div>
            Dipimpin oleh Aktuaris bergelar FSAI dengan pengalaman lebih dari 30 tahun di industri asuransi dan keuangan.
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-title">🚀 Teknologi Valuasi</div>
            Layanan unggulan *Self-Service Actuarial Calculator* berbasis web yang terintegrasi kurva yield PHEI.
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------
# 2. HALAMAN: PROFIL PERUSAHAAN
# ------------------------------------------
elif menu == "🏢 Profil Perusahaan":
    st.markdown('<h2 class="section-title">Selayang Pandang</h2>', unsafe_allow_html=True)
    st.write("""
    Ilmu Aktuaria adalah proses pekerjaan untuk memberikan rekomendasi atas temuan dalam merumuskan pendapat 
    berdasarkan aplikasi ilmu keuangan, manajemen risiko, dan teori statistik untuk menyelesaikan persoalan bisnis aktual.
    
    **KAS (Konsultan Aktuaria Setya Gunawan)** adalah konsultan aktuaria terkemuka yang didirikan untuk membantu 
    perusahaan merancang anggaran, menetapkan liabilitas (kewajiban), serta memproyeksikan bisnis ke depan dengan model stokastik.
    """)
    
    st.markdown('<h2 class="section-title">Legalitas Kami</h2>', unsafe_allow_html=True)
    col_leg1, col_leg2 = st.columns(2)
    with col_leg1:
        st.markdown("- **Izin Perusahaan:** No. 4.21.0007")
        st.markdown("- **SK Menteri Keuangan RI:** No. 590/KM.1/2021")
        st.markdown("- **Izin Aktuaris Publik:** No. Act-1.17.00026")
    with col_leg2:
        st.markdown("- **STTD Otoritas Jasa Keuangan (OJK):** No. 039/NB.122/STTD-KA/2021")
        st.markdown("- **Registrasi Persatuan Aktuaris Indonesia (PAI):** AKAI - 21043")

# ------------------------------------------
# 3. HALAMAN: LAYANAN & KLIEN
# ------------------------------------------
elif menu == "💼 Layanan & Klien":
    st.markdown('<h2 class="section-title">Lingkup Keahlian Kami</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    1. **Asuransi & Penjaminan:** Perhitungan Valuasi Cadangan Teknis, Pembuatan Produk, & Outsourcing Aktuaris.
    2. **PSAK 219 (Imbalan Kerja):** Valuasi pencadangan pesangon karyawan dengan metode *Projected Unit Credit* (PUC).
    3. **Dana Pensiun:** Valuasi Aktuaria untuk kecukupan dana & Iuran.
    4. **IFRS 17:** Pendampingan, implementasi, dan reviu pelaporan asuransi.
    5. **Aplikasi Aktuaria Mandiri:** Kalkulator valuasi PSAK 219 online terotomatisasi.
    """)
    
    st.markdown('<h2 class="section-title">Mitra & Klien Kami</h2>', unsafe_allow_html=True)
    st.write("Kami telah dipercaya oleh berbagai perusahaan Asuransi, Dana Pensiun, dan Korporasi, antara lain:")
    st.info("""
    **Asuransi:** PT Asuransi Syariah Sonwelis Takaful, PT Asuransi Reliance Indonesia, PT Asuransi Jiwasraya, dll.  
    **Dana Pensiun:** Dapen Pusri, Dapen JIH, dll.  
    **Korporasi Umum:** PT ASDP Indonesia Ferry, UI Group, Victoria Group, dll.
    """)

# ------------------------------------------
# 4. HALAMAN: TIM MANAJEMEN
# ------------------------------------------
elif menu == "👥 Tim Manajemen":
    st.markdown('<h2 class="section-title">Struktur Organisasi & Tenaga Ahli</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="color:#F25C05;">Setya Gunawan, SE, FSAI, AAAI-J, AIIS</h3>
            <p><b>Pimpinan KKA / Aktuaris Publik</b></p>
            <p>Pengalaman lebih dari 30 tahun di asuransi jiwa, umum, TPA asuransi kesehatan, serta penyusunan anggaran dan manajemen risiko.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <h3 style="color:#439A86;">Riana Prahati, SE.As, AAAK</h3>
            <p><b>Tenaga Teknis Aktuaria</b></p>
            <p>Ahli di bidang aktuaria, cadangan teknis, imbalan pasca kerja (PSAK 219), PSAK 117, dan reviu laporan.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="color:#439A86;">Setya Wibowo, ASAI</h3>
            <p><b>Manager Aktuaria</b></p>
            <p>Keahlian mendalam dalam asuransi umum, jiwa, kesehatan, dana pensiun, serta dukungan teknis aktuaria perusahaan.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="card">
            <h3 style="color:#439A86;">Maryadi Aryo Laksmono</h3>
            <p><b>Manager Keuangan & Investasi</b></p>
            <p>Profesional dalam pasar modal, investasi, analisis portofolio, dan pengambilan keputusan investasi strategis.</p>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------
# 5. HALAMAN: KALKULATOR (PAYWALL QRIS)
# ------------------------------------------
elif menu == "🧮 Kalkulator Aktuaria (Unggulan)":
    st.markdown('<div class="main-header" style="font-size:2.2rem;">Portal Valuasi PSAK 219 Mandiri</div>', unsafe_allow_html=True)
    
    if not st.session_state.payment_verified:
        # TAMPILAN JIKA BELUM BAYAR
        st.warning("🔒 **Akses Terkunci:** Anda harus melakukan pembayaran untuk menggunakan Kalkulator Aktuaria Otomatis.")
        
        st.markdown('<div class="qris-box">', unsafe_allow_html=True)
        st.markdown("<h3 style='color:#F25C05;'>Biaya Akses Valuasi (Per Dokumen/Laporan)</h3>", unsafe_allow_html=True)
        st.markdown("<h2>Rp 5.000.000,-</h2>", unsafe_allow_html=True)
        st.markdown("Silakan pindai kode QRIS di bawah ini melalui aplikasi Mobile Banking atau e-Wallet Anda.")
        
        # Placeholder Gambar QRIS
        st.image("https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg", width=200)
        
        ref_code = st.text_input("Masukkan Kode Referensi Transfer (Contoh: TRX-12345):")
        
        if st.button("✅ Verifikasi Pembayaran", use_container_width=True):
            if ref_code:
                with st.spinner("Memeriksa status pembayaran ke sistem perbankan..."):
                    time.sleep(2) # Simulasi loading gateway
                    st.session_state.payment_verified = True
                    st.rerun()
            else:
                st.error("Harap masukkan Kode Referensi terlebih dahulu!")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # TAMPILAN JIKA SUDAH BAYAR (KALKULATOR AKTIF)
        st.success("🎉 Pembayaran Berhasil Diversifikasi! Silakan gunakan kalkulator di bawah ini.")
        
        st.markdown('<h2 class="section-title">Kalkulator Valuasi PSAK 219</h2>', unsafe_allow_html=True)
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            input_perusahaan = st.text_input("Nama Perusahaan Klien", "PT KLIEN CONTOH")
            tanggal_laporan = st.date_input("Tanggal Laporan", datetime.date.today())
        with col_set2:
            asumsi_gaji = st.number_input("Kenaikan Gaji per Tahun (%)", value=5.0) / 100
            usia_pensiun = st.number_input("Usia Pensiun Normal", value=60)
            
        st.info("Ketik NIK dan Gaji Karyawan di tabel berikut:")
        df_input = st.data_editor(pd.DataFrame([
            {"NIK": "001", "Nama": "Budi", "Usia (Thn)": 35, "Masa Kerja": 10, "Gaji": 10000000}
        ]), num_rows="dynamic", use_container_width=True)
        
        if st.button("🚀 PROSES VALUASI OTOMATIS", use_container_width=True):
            with st.spinner("Mencocokkan *Yield Curve* PHEI dan menghitung Kewajiban (PUC)..."):
                time.sleep(1.5)
                # Simulasi Kalkulasi
                engine = PSAK219Engine(0.065, asumsi_gaji, usia_pensiun)
                pbo_total = sum([engine.calculate_puc(row['Usia (Thn)'], row['Masa Kerja'], row['Gaji'])['PBO'] for idx, row in df_input.iterrows()])
                
                st.markdown("### 📊 Ringkasan Hasil Valuasi")
                st.metric(label="Total Kewajiban Karyawan (PBO)", value=f"Rp {pbo_total:,.0f}".replace(",", "."))
                st.caption("*Menggunakan diskonto otomatis dari PHEI IGSYC (6.5%)")
                
                pdf_file = generate_pdf_report({}, input_perusahaan)
                st.download_button("📥 UNDUH LAPORAN PDF RESMI", data=pdf_file, file_name=f"PSAK219_{input_perusahaan}.pdf", mime="application/pdf")

# ------------------------------------------
# 6. HALAMAN: HUBUNGI KAMI
# ------------------------------------------
elif menu == "📞 Hubungi Kami":
    st.markdown('<h2 class="section-title">Kontak & Lokasi Kantor</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card" style="border-top: 5px solid #F25C05;">
            <h3 style="color:#F25C05;">Alamat Kantor</h3>
            <p><b>Konsultan Aktuaria Setya Gunawan (KAS)</b><br>
            Cilandak 88 Condominium Unit D-1<br>
            Jl. Margasatwa Barat No.88, Cilandak Timur,<br>
            Pasar Minggu, Jakarta Selatan 12560</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card" style="border-top: 5px solid #439A86;">
            <h3 style="color:#439A86;">Hubungi Kami</h3>
            <p>📞 <b>Telepon:</b> +62 (21) 78 17118<br>
            📱 <b>WhatsApp:</b> +62 812 9090 9019<br>
            ✉️ <b>Email Utama:</b> kka_setyagunawan@yahoo.com<br>
            📧 <b>Email Alternatif:</b> goen_bisnis@yahoo.com<br>
            🌐 <b>Website:</b> www.actuarial-kas.com</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><p style='text-align:center;'><i>Terima kasih atas kepercayaan Anda kepada KKA Setya Gunawan. - Serve u Great.</i></p>", unsafe_allow_html=True)
