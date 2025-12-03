import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- 1. SETUP HALAMAN (WIDE MODE) ---
# Kita pakai mode 'wide' agar latar belakang berwarna bisa memenuhi layar
st.set_page_config(
    page_title="Math Relax AI",
    page_icon="🧘",
    layout="wide", # Layar lebar
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (TAMPILAN BARU) ---
st.markdown("""
<style>
    /* A. LATAR BELAKANG KUNING GADING (SELURUH APLIKASI) */
    .stApp {
        background-color: #FDFD96; /* Warna Kuning Gading Cerah */
    }

    /* B. MENGATUR KOTAK CHAT UTAMA */
    /* Di Laptop: Kotak ada di tengah dengan lebar terbatas */
    .block-container {
        max-width: 900px; /* Lebar maksimal kotak chat di laptop */
        padding-top: 2rem;
        padding-bottom: 5rem;
        margin: auto; /* Posisi tengah */
    }

    /* C. TAMPILAN KHUSUS HP (MOBILE RESPONSIVE) */
    @media (max-width: 768px) {
        /* Di HP: Kotak chat memenuhi layar (Full Width) */
        .block-container {
            max-width: 100%;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 1rem;
        }
        /* Font di HP sedikit lebih besar biar enak dibaca */
        .stMarkdown, .stChatMessageContent {
             font-size: 1.05rem !important;
        }
    }

    /* D. MEMPERCANTIK ELEMEN CHAT */
    /* Judul Aplikasi */
    h1 {
        color: #4A4A4A;
        text-align: center;
        font-weight: 700;
    }
    /* Keterangan di bawah judul */
    .stCaption {
        text-align: center;
        color: #666;
        font-size: 1rem;
    }
    
    /* Warna Balon Chat (Biar kontras dengan background kuning) */
    /* Siswa (Hijau Lembut) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #E8F5E9;
        border: 1px solid #C8E6C9;
        border-radius: 15px;
    }
    /* AI (Putih Bersih) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 15px;
    }

    /* Sembunyikan elemen pengganggu */
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KONEKSI KE GOOGLE (MODEL 2.5 SESUAI DIAGNOSA) ---
@st.cache_resource # Cache biar gak connect ulang terus
def init_connections():
    # Cek Kunci
    if "GEMINI_API_KEY" not in st.secrets:
        return None, None, "Kunci API belum dipasang."

    # 1. Setup AI
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # MENGGUNAKAN MODEL 2.5 YANG TERSEDIA DI AKUN BAPAK
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        return None, None, f"Error AI: {e}"

    # 2. Setup Excel
    sheet = None
    err_msg = None
    try:
        if "gcp_service_account" in st.secrets:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
            client = gspread.authorize(creds)
            sheet = client.open("Database_Math_Relax").sheet1
        else:
            err_msg = "Kunci Excel (Service Account) belum dipasang."
    except Exception as e:
        err_msg = f"Gagal konek Excel: {e}"

    return model, sheet, err_msg

model, sheet, excel_err = init_connections()

# Tampilkan error Excel jika ada (tapi aplikasi tetap jalan)
if excel_err and "messages" not in st.session_state:
     st.toast(f"⚠️ Info Database: {excel_err}", icon="Info Database")

# --- 4. FUNGSI SIMPAN DATA ---
def simpan_log(nama, role, pesan):
    if sheet:
        try:
            tz = pytz.timezone('Asia/Jakarta')
            waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([waktu, nama, role, pesan])
        except:
            pass # Diam saja kalau gagal

# --- 5. LOGIKA LOGIN (TAMPILAN AWAL) ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if not st.session_state.user_name:
    # Gunakan container untuk membuat kotak login di tengah
    with st.container(border=True):
        st.markdown("<h2 style='text-align: center;'>👋 Selamat Datang</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Masukkan nama panggilanmu untuk mulai belajar.</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2: # Input di kolom tengah
            nama_input = st.text_input("Nama Kamu:", placeholder="Contoh: Budi", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True) # Spasi
            if st.button("Mulai Belajar 🚀", use_container_width=True, type="primary"):
                if nama_input.strip():
                    st.session_state.user_name = nama_input.strip()
                    st.rerun()
    st.stop()

# --- 6. TAMPILAN CHAT UTAMA (SETELAH LOGIN) ---

# KITA BUNGKUS SEMUA ISI CHAT DALAM SATU KOTAK PUTIH (CONTAINER)
with st.container(border=True):
    # Header Chat
    st.title("🧘 Math Relax AI")
    st.caption(f"Siswa: {st.session_state.user_name} | Materi: Pecahan SD Fase C")
    st.divider() # Garis pemisah

    # Sapaan Awal
    if "messages" not in st.session_state:
        st.session_state.messages = []
        sapaan = f"Halo **{st.session_state.user_name}**! 👋\n\nAku teman belajarmu. Jangan takut salah ya, di sini kita belajar Pecahan dengan santai. Kamu lagi bingung soal apa nih?"
        st.session_state.messages.append({"role": "model", "content": sapaan})

    # Tampilkan History Chat
    # Kita buat wadah scroll agar chat panjang tetap rapi di dalam kotak
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            ikon = "🧑‍🎓" if msg["role"] == "user" else "🧘"
            with st.chat_message(msg["role"], avatar=ikon):
                st.markdown(msg["content"])
        st.markdown("<div id='link_scroll'></div>", unsafe_allow_html=True) # Marker untuk auto-scroll

    # --- 7. INPUT PESAN (DI BAGIAN BAWAH KOTAK) ---
    st.markdown("<br>", unsafe_allow_html=True) # Beri jarak sedikit
    if prompt := st.chat_input("Ketik soal atau curhatmu di sini..."):
        # Tampilkan Pesan Siswa
        with chat_container:
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        simpan_log(st.session_state.user_name, "Siswa", prompt)

        # Proses Jawaban AI
        with chat_container:
            with st.chat_message("model", avatar="🧘"):
                if model:
                    placeholder = st.empty()
                    try:
                        # Instruksi Guru
                        chat_session = model.start_chat(history=[
                            {"role": "user", "parts": [f"Berperanlah sebagai Guru SD ramah. Nama siswa: {st.session_state.user_name}. Materi: PECAHAN. Metode: Scaffolding (bertahap). Jangan langsung beri jawaban akhir. Panggil siswa dengan namanya."]},
                            {"role": "model", "parts": ["Siap, saya mengerti."]}
                        ])
                        
                        # Masukkan history chat sebelumnya
                        for m in st.session_state.messages:
                            if m["role"] != "system":
                                role_google = "user" if m["role"] == "user" else "model"
                                try:
                                    chat_session.history.append({"role": role_google, "parts": [m["content"]]})
                                except:
                                    pass

                        # Kirim Pesan
                        response = chat_session.send_message(prompt)
                        jawaban_ai = response.text
                        
                        placeholder.markdown(jawaban_ai)
                        st.session_state.messages.append({"role": "model", "content": jawaban_ai})
                        simpan_log(st.session_state.user_name, "AI", jawaban_ai)
                        
                    except Exception as e:
                        st.error(f"Maaf, koneksi terputus. Coba lagi ya. ({e})")
                else:
                    st.error("Sistem AI belum siap. Cek konfigurasi.")
