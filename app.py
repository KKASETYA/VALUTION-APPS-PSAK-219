# ==========================================
# 6. KONFIGURASI HALAMAN & TEMA VISUAL
# ==========================================
st.set_page_config(
    page_title="KAS | Konsultan Aktuaria Setya Gunawan",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

COMPANY_LEGAL_NAME = "Kantor Konsultan Aktuaria Setya Gunawan"
COMPANY_SHORT = "KAS"
COMPANY_TAGLINE = "Serve u Great"
COMPANY_LICENSE = "Izin Usaha No. 4.21.007"
COMPANY_MENKEU = "Keputusan Menteri Keuangan RI No. 590/KM.1/2021"
COMPANY_MENKEU_DATE = "ditetapkan 7 Juni 2021"
COMPANY_OJK = "Terdaftar OJK — STTD Konsultan Aktuaria IKNB No. 039/NB.122/STTD-KA/2021 (15 November 2021)"
COMPANY_AKAI = "AKKAI - 21043 (berlaku s.d. 23 September 2027)"
COMPANY_ADDRESS = "Cilandak 88 Condominium Unit D-1, Jl. Margasatwa Barat No.88, Cilandak Timur, Pasar Minggu, Jakarta Selatan 12560"
COMPANY_PHONE = "+62 812 9090 9019"
COMPANY_PHONE_OFFICE = "+62 (21) 78 17118"
COMPANY_EMAIL = "kka_setyagunawan@yahoo.com"
COMPANY_EMAIL2 = "goen_bisnis@yahoo.com"
COMPANY_WEBSITE = "www.actuarial-kas.com"

LEADER_NAME = "Setya Gunawan, SE, FSAI, AAAI-J, AIIS"
LEADER_LICENSE = "Izin Aktuaris Publik No. Act-1.17.00026 (Kepmenkeu RI No. 50/KM.1/2017, 19 Januari 2017)"
LEADER_PAI = "Anggota Persatuan Aktuaris Indonesia (PAI) No. 20011027 — Fellow Society of Actuaries of Indonesia (FSAI)"

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

def dot_grid(color="#ffffff", opacity=0.55, n=30):
    dots = "".join([
        f'<span style="width:5px;height:5px;background:{color};opacity:{opacity};border-radius:50%;display:inline-block;margin:3px;"></span>'
        for _ in range(n)
    ])
    return f'<div style="display:flex;flex-wrap:wrap;width:86px;justify-content:flex-end;align-content:flex-start;">{dots}</div>'

DOT_GRID_HTML = dot_grid()

def section_bar(title, subtitle=None):
    """Header bar orange solid ala Company Profile KAS, dengan aksen dot-grid di kanan."""
    sub_html = f'<div style="color:#2a1c10;opacity:0.82;font-size:0.85rem;margin-top:4px;font-weight:500;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div style="background:linear-gradient(135deg,#F0672A,#D6540F);border-radius:14px;
                padding:18px 26px;margin:10px 0 22px 0;display:flex;align-items:center;
                justify-content:space-between;box-shadow:0 10px 22px rgba(214,84,15,0.28);">
        <div>
            <div style="color:#171310;font-weight:800;font-size:1.3rem;font-family:'Poppins',sans-serif;letter-spacing:0.6px;">{title}</div>
            {sub_html}
        </div>
        {DOT_GRID_HTML}
    </div>
    """

def profile_footer_bar():
    """Aksen footer bergaya teal + garis, meniru footer halaman Company Profile KAS."""
    return """
    <div style="display:flex;align-items:center;gap:14px;margin:36px 0 8px 0;">
        <div style="width:14px;height:46px;background:linear-gradient(180deg,#4F8C7D,#2E5F53);border-radius:3px;"></div>
        <div style="flex:1;border-top:1px solid #E3D3C2;"></div>
    </div>
    """

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
    background: linear-gradient(180deg, #241A12 0%, #6E3210 60%, #D6540F 100%);
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

/* ---------- Sidebar brand ---------- */
.sidebar-brand {
    text-align:center;
    padding: 6px 0 18px 0;
    border-bottom: 1px solid rgba(255,255,255,0.18);
    margin-bottom: 14px;
}
.sidebar-brand-title { font-family:'Poppins',sans-serif; font-weight:800; font-size:1.05rem; line-height:1.3; }
.sidebar-brand-tagline { font-style:italic; font-size:0.72rem; opacity:0.85; margin-top:2px; }
.sidebar-brand-sub { font-size:0.72rem; opacity:0.75; letter-spacing:0.5px; text-transform:uppercase; }
.sidebar-contact-box {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: 12px;
    padding: 12px 14px;
    font-size: 0.78rem;
    line-height: 1.6;
    margin-top: 18px;
}

/* ---------- Hero ---------- */
.hero-section {
    background: linear-gradient(135deg, #241A12 0%, #7A3410 45%, #E85D25 100%);
    padding: 56px 44px;
    border-radius: 26px;
    color: #ffffff;
    margin-bottom: 36px;
    box-shadow: 0 24px 48px rgba(36,26,18,0.30);
    position: relative;
    overflow: hidden;
}
.hero-title { font-size: 2.5rem; font-weight: 800; margin-bottom: 14px; line-height:1.2; }
.hero-sub { font-size: 1.08rem; font-weight: 400; opacity: 0.92; max-width: 700px; line-height:1.7; margin-bottom: 6px;}
.hero-tagline { font-style:italic; font-weight:600; opacity:0.85; font-size:1rem; margin-bottom:10px; }
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
    box-shadow: 0 6px 20px rgba(36,26,18,0.06);
    border: 1px solid #F3E4D8;
    transition: all 0.25s ease;
    height: 100%;
    margin-bottom: 6px;
}
.service-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 18px 34px rgba(214,84,15,0.16);
    border-color:#E85D25;
}
.service-icon { font-size: 2rem; margin-bottom: 10px; }
.service-title { font-size: 1.05rem; font-weight: 700; color:#241A12; margin-bottom: 6px; }
.service-desc { color:#7A6A5D; font-size: 0.87rem; line-height:1.6; }

.flagship-card {
    background: linear-gradient(135deg, #241A12 0%, #E85D25 100%);
    border-radius: 22px;
    padding: 34px 34px;
    color: white;
    box-shadow: 0 20px 40px rgba(36,26,18,0.32);
    margin-bottom: 10px;
}
.flagship-title { font-size:1.5rem; font-weight:800; margin-bottom:10px; }
.flagship-desc { opacity:0.92; line-height:1.7; font-size:0.95rem; }
.flagship-point { font-size:0.86rem; opacity:0.95; margin-bottom:6px; }

.stat-box { text-align:center; padding: 10px 6px; }
.stat-num { font-size: 1.7rem; font-weight: 800; color:#E85D25; font-family:'Poppins',sans-serif;}
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

.team-card {
    background:#ffffff;
    border-radius:18px;
    padding:22px;
    border:1px solid #F3E4D8;
    box-shadow: 0 6px 18px rgba(36,26,18,0.05);
    height:100%;
}
.team-avatar {
    width:56px; height:56px; border-radius:50%;
    background: linear-gradient(135deg,#E85D25,#7A3410);
    color:#fff; display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:1.3rem; margin-bottom:12px;
}
.team-name { font-weight:700; color:#241A12; font-size:1rem; margin-bottom:2px;}
.team-role { color:#E85D25; font-weight:600; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:8px;}
.team-desc { color:#7A6A5D; font-size:0.85rem; line-height:1.6; }

.org-box {
    background: linear-gradient(135deg,#8a3010,#4F1D0A);
    color:#fff;
    padding:14px 20px;
    border-radius:10px;
    font-weight:700;
    display:inline-block;
    margin:6px;
    box-shadow:0 8px 16px rgba(74,29,10,0.25);
    font-size:0.92rem;
    text-align:center;
}
.org-box.top { background: linear-gradient(135deg,#B8410D,#7A3410); font-size:1rem; padding:16px 26px;}

.legal-chip {
    display:flex; gap:10px; align-items:flex-start;
    background:#FFF6F1; border:1px solid #F3E4D8; border-radius:14px;
    padding:14px 16px; margin-bottom:10px;
}
.legal-chip .num {
    background:#E85D25; color:#fff; font-weight:800; font-size:0.78rem;
    width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
}
.legal-chip .txt b { color:#241A12; }
.legal-chip .txt { font-size:0.85rem; color:#5c4c40; line-height:1.5;}

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
    box-shadow: 0 10px 20px rgba(214,84,15,0.32);
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
    "🤝 Klien & Pengalaman",
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
        <div class="sidebar-brand-tagline">"{COMPANY_TAGLINE}"</div>
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
        <div class="badge-gold">✓ TERDAFTAR RESMI — OJK & KEMENTERIAN KEUANGAN RI</div>
        <div class="hero-tagline">"{COMPANY_TAGLINE}"</div>
        <div class="hero-title">Kepastian Aktuaria untuk<br/>Keputusan Bisnis yang Lebih Tepat</div>
        <div class="hero-sub">
            {COMPANY_LEGAL_NAME} (KAS) adalah Konsultan Aktuaria berbadan usaha perorangan yang dipimpin
            oleh seorang Aktuaris Publik bersertifikat, melayani perhitungan cadangan teknis, valuasi
            imbalan kerja (PSAK 24/219), budgeting, hingga pendampingan aktuaria bagi perusahaan asuransi,
            dana pensiun, perbankan, dan lembaga pemerintahan di seluruh Indonesia.
        </div>
        <div>
            <span class="badge-soft">📐 PSAK 24 & 219 Compliant</span>
            <span class="badge-soft">📈 PHEI IGSYC Yield Matching</span>
            <span class="badge-soft">🏛️ Terdaftar OJK sejak 2021</span>
            <span class="badge-soft">🧑‍💼 30+ Tahun Pengalaman Pimpinan</span>
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
        st.markdown('<div class="stat-box"><div class="stat-num">30+</div><div class="stat-label">Tahun Pengalaman Pimpinan</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown('<div class="stat-box"><div class="stat-num">60+</div><div class="stat-label">Klien Perusahaan & Lembaga</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown('<div class="stat-box"><div class="stat-num">2021</div><div class="stat-label">Terdaftar Resmi OJK & Kemenkeu</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown('<div class="stat-box"><div class="stat-num">1996</div><div class="stat-label">Awal Rekam Jejak Proyek</div></div>', unsafe_allow_html=True)

    st.markdown("<hr class='divider-soft'/>", unsafe_allow_html=True)
    st.markdown(section_bar("LAYANAN UNGGULAN KAMI", "Solusi aktuaria menyeluruh, dari perhitungan hingga laporan siap audit."), unsafe_allow_html=True)

    fc1, fc2 = st.columns([1.4, 1])
    with fc1:
        st.markdown("""
        <div class="flagship-card">
            <div class="flagship-title">🧮 Cadangan Pesangon & Imbalan Kerja — PSAK 24 / PSAK 219</div>
            <div class="flagship-desc">
                Layanan unggulan kami. Kalkulator online otomatis menghitung <b>PBO</b>, <b>Current Service Cost</b>,
                dan durasi liabilitas dengan metode <i>Projected Unit Credit (PUC)</i> sesuai UUK No.13/2003,
                UU Cipta Kerja, dan PSAK No.24 (Revisi 2013), lalu mencocokkan suku bunga diskonto secara
                otomatis dengan kurva <b>yield PHEI IGSYC</b> resmi — hasilnya langsung tersedia dalam laporan
                PDF formal dwibahasa, lengkap dengan neraca, OCI, dan rekonsiliasi.
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
            <div class="service-title">Valuasi Cadangan Teknis Asuransi</div>
            <div class="service-desc">Perhitungan & review cadangan teknis asuransi jiwa, umum, sosial, dan penjaminan.</div>
        </div>
        """, unsafe_allow_html=True)
    with g2:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">🧑‍💼</div>
            <div class="service-title">Pendampingan Aktuaris</div>
            <div class="service-desc">Second opinion, mitra aktuaris internal, hingga layanan aktuaris outsourcing penuh.</div>
        </div>
        """, unsafe_allow_html=True)
    with g3:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">🎓</div>
            <div class="service-title">Workshop & Pelatihan Aktuaria</div>
            <div class="service-desc">Pelatihan cadangan pesangon PSAK 24, asuransi kesehatan, hingga mahasiswa & karyawan.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(profile_footer_bar(), unsafe_allow_html=True)

# ==========================================
# 9. HALAMAN: TENTANG KAMI
# ==========================================
elif menu == "🏢 Tentang Kami":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">TENTANG KAMI</div>
        <div class="hero-title" style="font-size:2.1rem;">{COMPANY_LEGAL_NAME}</div>
        <div class="hero-sub">Kantor konsultan aktuaria berbadan usaha perorangan yang berfokus pada ketepatan
        perhitungan, kepatuhan standar akuntansi, dan kejelasan pelaporan bagi klien korporasi, dana pensiun,
        perbankan, dan lembaga pemerintahan di Indonesia.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_bar("SELAYANG PANDANG"), unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    Ilmu Aktuaria baru populer 2 (dua) tahun belakangan ini, banyak masyarakat yang belum memahami mengenai
    aktuaria sehingga banyak yang bimbang pada saat ilmu aktuaria akan diterapkan pada perusahaan yang
    memiliki tujuan profit maupun non profit serta lembaga pemerintahan — apakah sesuai, cocok, dan akurat.
    <br/><br/>
    Ilmu aktuaria adalah ilmu terapan berdasarkan konsep dan pengamatan yang diambil dari pengalaman praktisi
    dan ilmu pengetahuan lainnya, seperti matematika, statistik, ekonomi, keuangan, dan manajemen risiko.
    <br/><br/>
    Aktuaria adalah proses pekerjaan untuk memberikan rekomendasi atas temuan atau pekerjaan dalam rangka
    merumuskan suatu pendapat berdasarkan aplikasi ilmu keuangan, manajemen risiko, dan teori statistik untuk
    menyelesaikan persoalan-persoalan bisnis aktual. Aktuaris melakukan perhitungan dan analisa biaya,
    keuntungan bisnis, investasi, serta kemungkinan terjadinya peristiwa yang tidak pasti — sekaligus merancang,
    mengelola produk dan sistem pengelolaannya, serta terlibat dalam pembuatan laporan keuangan perusahaan.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_bar("LATAR BELAKANG"), unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    Banyak perusahaan berorientasi profit yang belum memiliki perencanaan matang, baik dari sisi penetapan
    produk, anggaran/budgeting, maupun penetapan liability/kewajiban — sehingga dalam perjalanannya (biasanya
    minimal 1 tahun) timbul kendala yang berakibat kurang baik. Kondisi ini berlaku luas: asuransi jiwa, asuransi
    umum, asuransi sosial, dana pensiun, perbankan, industri, pertanian, perdagangan, perikanan, komoditi,
    koperasi, hingga lembaga pemerintahan pusat/daerah dan partai politik.
    <br/><br/>
    Kami sebagai Konsultan Aktuaria yang dipimpin oleh seorang Aktuaris memiliki kemampuan terpadu di bidang
    Ilmu Keuangan, Ekonomi, Komputer, Statistik, Matematika, dan Manajemen Risiko — mampu menyusun anggaran/budgeting
    dan liability, serta memproyeksikan bisnis lebih dari 1 tahun ke depan menggunakan <i>Model Stokastik</i> untuk
    memperkirakan distribusi frekuensi dan severitas, termasuk memperhitungkan perkiraan suku bunga dan pergerakan
    valuta terhadap biaya-biaya di masa depan.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_bar("PROFIL LEGAL KAS"), unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(f"""
        <div class="info-box">
            <b>Badan Usaha</b><br/>
            KAS merupakan Konsultan Aktuaria berbentuk Badan Usaha Perorangan, didirikan berdasarkan
            {COMPANY_MENKEU} tentang Izin Usaha Kantor Konsultan Aktuaria Setya Gunawan, dengan
            {COMPANY_LICENSE} ({COMPANY_MENKEU_DATE}).<br/><br/>
            {COMPANY_OJK}
        </div>
        """, unsafe_allow_html=True)
    with p2:
        st.markdown(f"""
        <div class="info-box">
            <b>Pimpinan KAS</b><br/>
            {LEADER_NAME} — seorang Aktuaris yang telah mendapatkan izin sertifikasinya sebagai
            <b>Aktuaris Publik</b> berdasarkan {LEADER_LICENSE}.<br/><br/>
            {LEADER_PAI}
        </div>
        """, unsafe_allow_html=True)

    st.markdown(section_bar("STRUKTUR ORGANISASI"), unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; padding:20px 0;">
        <div class="org-box top">👑 Pimpinan KKA</div><br/>
        <div class="org-box">📊 Manager Aktuaria</div>
        <div class="org-box">💰 Manager Keuangan dan Investasi</div><br/>
        <div class="org-box">🧮 Tenaga Teknis Aktuaria</div>
        <div class="org-box">🗂️ Tenaga Administrasi dan Keuangan</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_bar("TIM KAMI"), unsafe_allow_html=True)
    t1, t2 = st.columns(2)
    with t1:
        st.markdown("""
        <div class="team-card">
            <div class="team-avatar">SG</div>
            <div class="team-name">Setya Gunawan, SE, FSAI, AAAI-J, AIIS</div>
            <div class="team-role">Pimpinan KKA / Aktuaris Publik</div>
            <div class="team-desc">
                Anggota Persatuan Aktuaris Indonesia (PAI) No. 20011027 dengan gelar FSAI. Berpengalaman lebih
                dari 30 tahun di bidang Ilmu Aktuaria dan Manajemen Risiko — perusahaan asuransi jiwa, asuransi
                umum, TPA Asuransi Kesehatan, staf pengajar, dan konsultan aktuaria. Keahlian khusus: penyusunan
                anggaran/budgeting perusahaan dan pengelolaan program asuransi kesehatan (Indemnity, Managed Care,
                ASO/TPA) dari awal pembentukan hingga pelaksanaan dan evaluasi periodik.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with t2:
        st.markdown("""
        <div class="team-card">
            <div class="team-avatar">SW</div>
            <div class="team-name">Setya Wibowo, ASAI</div>
            <div class="team-role">Manager Aktuaria</div>
            <div class="team-desc">
                Profesional di bidang aktuaria dan industri perasuransian dengan keahlian dalam aktuaria,
                asuransi umum, asuransi kesehatan, asuransi jiwa, dana pensiun, cadangan teknis, serta dukungan
                teknis laporan aktuaria. Berpengalaman di berbagai perusahaan asuransi, konsultan aktuaria, dan
                perusahaan umum dengan berbagai peran strategis.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    t3, t4 = st.columns(2)
    with t3:
        st.markdown("""
        <div class="team-card">
            <div class="team-avatar">RP</div>
            <div class="team-name">Riana Prahati, SE.As, AAAK</div>
            <div class="team-role">Tenaga Teknis Aktuaria</div>
            <div class="team-desc">
                Tenaga ahli di bidang aktuaria dengan keahlian dalam aktuaria, cadangan teknis, dana pensiun,
                imbalan pasca kerja, PSAK 24/PSAK 219, PSAK 117, serta penyusunan dan reviu laporan aktuaria.
                Berpengalaman dalam analisis aktuaria, evaluasi kewajiban perusahaan, dan dukungan teknis
                penyusunan laporan sesuai standar profesional.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with t4:
        st.markdown("""
        <div class="team-card">
            <div class="team-avatar">MA</div>
            <div class="team-name">Maryadi Aryo Laksmono</div>
            <div class="team-role">Manager Keuangan dan Investasi</div>
            <div class="team-desc">
                Tenaga profesional di bidang keuangan dan investasi dengan keahlian dalam pasar modal, investasi,
                analisis portofolio, serta dukungan kajian investasi. Berperan dalam analisis keuangan, evaluasi
                instrumen investasi, pengelolaan portofolio, dan dukungan pengambilan keputusan investasi.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(section_bar("LEGALITAS & SERTIFIKASI"), unsafe_allow_html=True)
    legal_items = [
        ("1", "Izin Usaha Konsultan Aktuaria", COMPANY_MENKEU + f" — {COMPANY_LICENSE}"),
        ("2", "Sertifikasi Asosiasi AKKAI", "Anggota Asosiasi Kantor Konsultan Aktuaria Indonesia, " + COMPANY_AKAI),
        ("3", "Sertifikasi Aktuaris (FSAI)", LEADER_PAI),
        ("4", "Sertifikasi Aktuaris Publik", LEADER_LICENSE),
        ("5", "Sertifikasi AAMAI (AAAI-J)", "Ajun Ahli Asuransi Indonesia sektor Jiwa — Asosiasi Ahli Manajemen Asuransi Indonesia."),
        ("6", "Sertifikasi IIS (Syariah)", "Associate of the Islamic Insurance Society (AIIS) — Islamic Insurance Society."),
        ("7", "Pengusaha Kena Pajak", "Terdaftar sebagai Pengusaha Kena Pajak sejak 22 Oktober 2021."),
        ("8", "Surat Tanda Terdaftar OJK", COMPANY_OJK),
    ]
    lc1, lc2 = st.columns(2)
    for i, (num, title, desc) in enumerate(legal_items):
        target = lc1 if i % 2 == 0 else lc2
        with target:
            st.markdown(f"""
            <div class="legal-chip">
                <div class="num">{num}</div>
                <div class="txt"><b>{title}</b><br/>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(profile_footer_bar(), unsafe_allow_html=True)

# ==========================================
# 10. HALAMAN: LAYANAN KAMI
# ==========================================
elif menu == "💼 Layanan Kami":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">LAYANAN KAMI</div>
        <div class="hero-title" style="font-size:2.1rem;">Keahlian & Solusi Aktuaria Menyeluruh</div>
        <div class="hero-sub">Dari perhitungan cadangan teknis, imbalan kerja, budgeting, hingga pendampingan
        aktuaria dan pelaporan resmi — kami mendampingi perusahaan Anda memenuhi kepatuhan standar akuntansi.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="flagship-card">
        <div class="flagship-title">⭐ Layanan Unggulan: Cadangan Pesangon Sesuai PSAK 24 / Imbalan Kerja PSAK 219</div>
        <div class="flagship-desc">
            Setiap perusahaan yang memiliki karyawan wajib memperhitungkan besarnya imbalan kerja sesuai
            ketentuan UUK No.13 Tahun 2003 / UU Cipta Kerja atau Peraturan Perusahaan dan PSAK No.24 (Revisi
            2013) / PSAK 219. Kalkulator online kami menghitung Imbalan Kerja menggunakan metode
            <b>Projected Unit Credit (PUC)</b>, mencocokkan diskonto otomatis dengan kurva yield PHEI IGSYC,
            dan menghasilkan laporan PDF siap direview oleh pihak internal, Kantor Akuntan Publik (KAP), maupun
            pihak berkepentingan lainnya.
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

    st.markdown(section_bar("ASURANSI JIWA, UMUM, SOSIAL & PENJAMINAN"), unsafe_allow_html=True)
    a1, a2 = st.columns(2)
    with a1:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">🧮</div>
            <div class="service-title">Perhitungan & Review Valuasi Cadangan Teknis</div>
            <div class="service-desc">Cadangan teknis adalah bagian penting kestabilan keuangan jangka panjang perusahaan asuransi. Kami juga dapat mereview perhitungan yang sudah dilakukan Aktuaris Internal perusahaan.</div>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown("""
        <div class="service-card">
            <div class="service-icon">📦</div>
            <div class="service-title">Pembuatan Produk Asuransi (Baru & Modifikasi)</div>
            <div class="service-desc">Asuransi Jiwa/Umum/Kesehatan/Penjaminan — mulai dari tool kits marketing, syarat polis, underwriting guideline, deskripsi produk, hingga profit testing dan evaluasi periodik.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(section_bar("PENDAMPINGAN & DUKUNGAN PROFESIONAL"), unsafe_allow_html=True)
    b_items = [
        ("🤝", "Pendampingan Aktuaris", "Second opinion & mitra bagi Aktuaris Internal, atau layanan Aktuaris Outsourcing penuh bagi perusahaan yang belum memiliki aktuaris internal."),
        ("💻", "Pendampingan Aplikasi IT Aktuaria", "Pendampingan aktuaria dalam pembuatan program IT — sistem Marketing, Operasional, dan Teknik."),
        ("🔍", "Pendampingan Kantor Akuntan Publik", "Mendampingi KAP/Eksternal Auditor saat audit perusahaan asuransi, perbankan, penjaminan, dan dana pensiun."),
        ("🏥", "Outsourcing Perhitungan Asuransi Kesehatan", "Perhitungan aktuaria asuransi kesehatan kumpulan, penetapan Term & Condition, dan jaringan provider yang sesuai profil klien."),
        ("🎓", "Workshop, Pelatihan & Seminar", "Cadangan pesangon PSAK 24, program asuransi kesehatan model Indemnity/Managed Care, hingga pelatihan mahasiswa & karyawan."),
        ("📘", "Penerapan & Review IFRS 17", "Penerapan, pendampingan, dan review IFRS 17 pada laporan keuangan perusahaan asuransi dan reasuransi."),
    ]
    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(b_items):
        with cols[i % 3]:
            st.markdown(f'<div class="service-card"><div class="service-icon">{icon}</div><div class="service-title">{title}</div><div class="service-desc">{desc}</div></div>', unsafe_allow_html=True)
            st.write("")

    st.markdown(section_bar("BUDGETING, ANALISA & PENDANAAN"), unsafe_allow_html=True)
    c_items = [
        ("🏦", "Budgeting Perusahaan Perbankan/Non-Perbankan", "Proyeksi target marketing, pendapatan, klaim, biaya, dan liability, serta evaluasi budgeting periodik."),
        ("📊", "Review Produk & Tarif Premi", "Evaluasi underwriting, proses klaim, handling problem, aplikasi, perhitungan aktuaria, manajemen risiko, dan SOP bagi produk yang merugi."),
        ("💵", "Analisa Biaya", "Analisa biaya secara detail — termasuk pemisahan biaya direct selling — agar alokasi premi/tarif tepat guna."),
        ("🏛️", "Valuasi Aktuaria untuk Pendanaan Dana Pensiun", "Perhitungan tingkat kecukupan dana dan tingkat iuran yang memadai untuk menutupi kewajiban Dana Pensiun."),
        ("🩺", "Valuasi Biaya Program Kesehatan", "Perhitungan biaya program kesehatan bagi peserta aktif maupun pensiunan dengan model perhitungan kami."),
        ("🏛️", "Budgeting Lembaga Pemerintahan", "SOP dan anggaran bagi Pemerintah Pusat/Daerah dan Perbankan, lengkap dengan evaluasi periodik atas program yang dijalankan."),
    ]
    cols2 = st.columns(3)
    for i, (icon, title, desc) in enumerate(c_items):
        with cols2[i % 3]:
            st.markdown(f'<div class="service-card"><div class="service-icon">{icon}</div><div class="service-title">{title}</div><div class="service-desc">{desc}</div></div>', unsafe_allow_html=True)
            st.write("")

    st.markdown(profile_footer_bar(), unsafe_allow_html=True)

# ==========================================
# 11. HALAMAN: KLIEN & PENGALAMAN
# ==========================================
elif menu == "🤝 Klien & Pengalaman":
    st.markdown(f"""
    <div class="hero-section" style="padding:44px 44px;">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">KLIEN & PENGALAMAN</div>
        <div class="hero-title" style="font-size:2.1rem;">Dipercaya Puluhan Perusahaan & Lembaga</div>
        <div class="hero-sub">Rekam jejak proyek sejak 1996 hingga saat ini, bersama mitra profesional yang
        turut mendukung kualitas layanan kami.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(section_bar("DAFTAR KLIEN KAS", "Sebagian perusahaan yang sudah menggunakan jasa KAS."), unsafe_allow_html=True)

    with st.expander("🏢 Perusahaan Asuransi — Product Development, Cadangan Teknis & Laporan Aktuaris (24 Perusahaan)"):
        st.markdown("""
        PT Asuransi Syariah Sonwelis Takaful · PT Asuransi Sahabat Artha Proteksi · PT Asuransi Binagriya Upakara ·
        PT Asuransi Jiwa Syariah Al Amin · PT Asuransi Jiwa Syariah Jasa Mitra Abadi · PT Asuransi Cakrawala Proteksi ·
        PT Asuransi Candi Utama · PT Asuransi Reliance Indonesia · PT Asuransi Videi · PT Asuransi Artha Graha ·
        PT Asuransi ABDA, Tbk · PT Asuransi Umum Victoria · PT Asuransi Jiwa Victoria · PT Asuransi Bhakti Bhayangkara ·
        PT Asuransi Bosowa · PT Asuransi Perisai Listrik Negara · PT Asuransi Umum MNC · PT Asuransi Seainsure ·
        PT Asuransi Jiwa Seainsure · PT Asuransi Etiqa Internasional · PT Asuransi Malaca Trust · PT Asuransi Jiwa IFG ·
        PT Asuransi Digital Bersama · PT Asuransi Jiwasraya
        """)

    with st.expander("📘 Perusahaan Asuransi — Penerapan & Review Saldo Awal PSAK 117 (15 Perusahaan)"):
        st.markdown("""
        PT Asuransi FPG Indonesia · PT Pacific Life Indonesia · PT Bhinneka Life Indonesia · PT Asuransi Umum Mega ·
        PT Arthagraha General Insurance · PT Asuransi Umum Bina Griya Upakara · PT Victoria Insurance ·
        PT Victoria Alife Indonesia · PT Asuransi Jiwa Nasional (Pelatihan & Pendampingan PSAK 117) ·
        PT Hanwa Life Insurance · PT Asuransi Jiwa Central Asia Raya (CAR) · PT Central Asia Finance ·
        PT Asuransi Jiwa Heksa · PT Asuransi Pan Pacific · PT Heksa Insurance
        """)

    with st.expander("🏛️ Perusahaan Dana Pensiun (5 Lembaga)"):
        st.markdown("""
        Dana Pensiun Jakarta Internasional Hotel · Dana Pensiun Pertani · Dana Pensiun Pusri ·
        Dana Pensiun BPD Kalsel · Dana Pensiun Baptis
        """)

    with st.expander("🏢 Perusahaan Non-Asuransi (20 Perusahaan)"):
        st.markdown("""
        Unit Usaha UI Group · PT NTL Nagai Trans Line Indonesia · PT Global Insurance Broker ·
        PT Mitra Harmoni Insurance Broker · PT Heesung Indonesia Electronics · PT Asics Indonesia Trading ·
        PT Media Prima HR Solution · PT Reliance Manajer Investasi · PT Zhalka Prima Global ·
        PT Petrolindo Energi Perkasa · Sinar Alam Group · PT Heesung Electronics Jakarta · Kopkar Hutama Karya ·
        SES Group (Business Plan) · Equity Building Management · ASDP Ferry (Analisa JHT) · PUSRI (Analisa JHT) ·
        MPA Group · PT Putra Elang · PPPRSKH Equity
        """)

    with st.expander("🧾 Valuasi Imbalan Kerja Sesuai PSAK No. 219 (17 Klien)"):
        st.markdown("""
        Dapen Pusri · PT Top Pasific Mineral · PT Intra Niaga Mulya · PT Krakatau Tirta Operasi ·
        PT Jamkrida Kalsel · PT Srijasa Brika Perkasa · Pusilkom UI · CEP CCTI FTUI · Victoria Group ·
        PT Aleyah Sintasint Farma · Sinar Alam Group · PT Heesung Electronics Jakarta · PT Jamkrida NTB Syariah ·
        SES Group (Business Plan) · PT ASDP Indonesia Ferry · MPA Group · MCI Group
        """)

    with st.expander("🤝 Mitra Kantor Akuntan Publik (KAP)"):
        st.markdown("""
        KAP Doli Bambang Sulistyanto dan Ali · KAP Gideon Adi & Rekan · KAP Heliantono · KAP Mirawati ·
        KAP Kreston Global · KAP KKSP & Rekan · KAP Clara Sunarsi · KAP DSI
        """)

    st.markdown(section_bar("MITRA STRATEGIS KAS"), unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("""
        <div class="info-box">
            <b>🧾 KAP Dian Utami & KAP Kuncara Budi Santosa</b><br/>
            Mitra profesional yang memiliki pengalaman dan keahlian dalam bidang Audit Keuangan dan Laporan
            Keuangan yang dapat bersinergi dengan kami.
        </div>
        <div class="info-box">
            <b>⚖️ Endra Wirawan & Rekan (Advocate and Legal Consulting)</b><br/>
            Mitra dari sisi hukum — mendampingi review perjanjian, investigasi klaim yang dianggap fraud,
            serta membantu klien jika terdapat permasalahan hukum.
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="info-box">
            <b>💼 Konsultan Pajak</b><br/>
            Mitra dari sisi perpajakan yang membantu klien kami dalam permasalahan perpajakan serta
            administrasinya agar bisnis klien dapat berjalan dengan baik.
        </div>
        <div class="info-box">
            <b>🌏 Euler Consulting (Malaysia)</b><br/>
            Mitra spesialis IFRS 17 sejak 2017, berpengalaman dalam pendampingan dan implementasi IFRS 17
            di Perusahaan Asuransi Zurich Asia Pasific.
        </div>
        """, unsafe_allow_html=True)

    st.markdown(section_bar("REKAM JEJAK PROYEK"), unsafe_allow_html=True)
    with st.expander("📜 Proyek Selesai (1996 – 2021)"):
        st.markdown("""
        - **1996–1999** — Menghitung Anggaran Kesehatan, membuat Produk Asuransi Jiwa & Kesehatan serta Cadangan Teknis Perusahaan pada Asuransi Jiwa Bakrie
        - **2004–2005** — Project Information Group Life for Allianz Life Indonesia
        - **2007** — Pembicara pada Workshop "Actuarial Health Care", organized by PT.Vico, Jakarta
        - **2007–2008** — Analisa & Menghitung Anggaran Kesehatan bagi Karyawan Aktif dan Pensiun, PT (Persero) Garam Surabaya
        - **2008** — Analisa Program Employee Benefit, Menghitung Anggaran Kesehatan & Penyeleksian Asuransi, Garuda Indonesia
        - **2008** — Analisa & Membuat Anggaran Kesehatan bagi Karyawan Aktif, PTPN XI Surabaya
        - **2008–2011** — Membangun TPA khusus Pelayanan Kesehatan pada PT.Kaissar HealthCare, sebagai Technical Advisor
        - **2008–2010** — Menghitung Anggaran Kesehatan & Cadangan Teknis, Asuransi Jiwa WanaArtha
        - **2009–2010** — Project System Information Pension Fund, Dana Pensiun Pupuk Kaltim
        - **2009** — Developed Priority Banking Unit, Bank BTN
        - **2010** — Membangun TPA Internal Program Kesehatan & Produk Standar Indemnity/Managed Care, PT (Persero) Asuransi Jasindo
        - **2010–2017** — Membangun TPA khusus Pelayanan Kesehatan, PT.Media Health Care, sebagai Technical Advisor
        - **2010** — Financial Advisor for Tune Money (Air Asia Group)
        - **2010–2016** — Menghitung Anggaran Kesehatan & Cadangan Teknis, Asuransi Jiwa Recapital
        - **2011** — Developed Priority Banking Unit, Bank Woori Saudara & Bank QNB Kesawan
        - **2011** — Project Originator for CDH Investment Hedge Fund
        - **2012** — Developed Priority Banking Unit, Bank DKI
        - **2012–2013** — Project Development Electronic Data Capture (EDC), Media Healthcare Indonesia
        - **2016–2017** — Menghitung Anggaran Kesehatan & Cadangan Teknis, Asuransi Bintang
        - **2016** — Developed Product & SOP, Bank Sumsel
        - **2017** — Leadership Development Program, Pemprov Sumatera Selatan
        - **2018–2020** — Technical Advisor Broker Asuransi untuk perencanaan produk, operasional & perjanjian Kerjasama Produk Asuransi Kredit, BPD Sumsel Babel
        - **2019** — Client Relationship for Sphere Capital Singapore
        - **2019** — Financial Advisor & Fund Raiser for Anterin.id
        - **2019** — Client Relationship for Yuanta Asset Management
        - **2021** — Financial Advisor to President Director, Bank Banten
        """)

    with st.expander("🚀 Proyek Berjalan / Existing Projects (2014 – 2025)"):
        st.markdown("""
        - **2014–2025** — Develop People Development Program, Bank Permata
        - **2017–2021** — Menghitung & Analisa Cadangan Teknis, Asuransi Jiwa Kresna
        - **2020–2024** — Technical Advisor Asuransi Jiwa Syariah — Pendampingan Aktuaris, Produk Baru (Asuransi Kesehatan Indemnity & Managed Care, Anuitas), Pelatihan & Analisa Cadangan Teknis
        - **2023–2024** — Technical Advisor Perusahaan Asuransi Umum Bosowa
        - **2024–2025** — Technical Advisor Perusahaan Asuransi Umum Reliance — evaluasi Produk Asuransi Kesehatan yang sedang berjalan
        """)

    st.markdown(profile_footer_bar(), unsafe_allow_html=True)

# ==========================================
# 12. HALAMAN: KONTAK KAMI
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
            {COMPANY_PHONE}<br/>
            {COMPANY_PHONE_OFFICE} (Kantor)<br/><br/>
            <b>✉️ Email</b><br/>
            {COMPANY_EMAIL}<br/>
            {COMPANY_EMAIL2}<br/><br/>
            <b>🌐 Website</b><br/>
            {COMPANY_WEBSITE}<br/><br/>
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

    st.markdown(profile_footer_bar(), unsafe_allow_html=True)

# ==========================================
# 13. HALAMAN: KALKULATOR VALUASI AKTUARIA
# ==========================================
elif menu == "🧮 Kalkulator Valuasi Aktuaria":
    st.markdown(f"""
    <div class="calc-header">
        {LOGO_CHIP_HTML}
        <div class="badge-gold">LAYANAN UNGGULAN</div>
        <div class="hero-title" style="font-size:1.9rem; margin-bottom:8px;">📄 Generator Laporan Aktuaria PSAK 219</div>
        <div class="hero-sub" style="font-size:0.98rem;">Pencocokan otomatis kurva yield PHEI IGSYC — hitung liabilitas dan unduh laporan resmi dalam hitungan menit.</div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pengaturan Dokumen & Klien")
    input_perusahaan = st.sidebar.text_input("Nama Perusahaan Klien", "PT GATRA MAPAN INDONESIA")
    tanggal_laporan = st.sidebar.date_input("Tanggal Laporan Diterbitkan", datetime.date(2026, 3, 27))
    nomor_laporan = st.sidebar.text_input("Nomor Laporan Baku", f"082/KAS-FR/PSAK/III/{tanggal_laporan.strftime('%Y')}")

    asumsi_gaji = st.sidebar.number_input("Kenaikan Gaji (%)", value=5.0, step=0.1) / 100
    usia_pensiun = st.sidebar.number_input("Usia Pensiun Normal", value=60, step=1)

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
    if st.button("Jalankan Valuasi Otomatis (PHEI IGSYC Yield Matching) 🚀") and datasets_to_process:
        with st.spinner("Menghitung durasi liabilitas dan mencocokkan kurva yield PHEI IGSYC..."):
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

                final_engine = PSAK219Engine(matched_phei_rate, asumsi_gaji, usia_pensiun)
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
            st.success(f"Valuasi Selesai! Suku Bunga PHEI IGSYC Tercocokkan Otomatis (Durasi Rata-rata ~{avg_duration:.2f} Tahun).")

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
            file_name=f"FINAL_REPORT_PHEI_IGSYC_{input_perusahaan.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
