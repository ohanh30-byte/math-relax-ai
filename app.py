import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- 1. KONFIGURASI TAMPILAN (UI) ---
st.set_page_config(
    page_title="Math Relax AI",
    page_icon="🧘",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS agar tampilan lebih bersih untuk anak SD
st.markdown("""
    <style>
    .stChatMessage {border-radius: 15px; padding: 10px;}
    .stTextInput > div > div > input {border-radius: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNGSI KONEKSI DATABASE & AI ---
def init_connections():
    # Cek Secrets
    if "gcp_service_account" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Konfigurasi Secrets belum lengkap. Mohon cek dashboard Streamlit.")
        st.stop()
    
    # Setup Gemini
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Setup Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    client = gspread.authorize(creds)
    
    # Buka Sheet (Nama File harus: Database_Math_Relax)
    try:
        return client.open("Database_Math_Relax").sheet1
    except:
        st.warning("⚠️ Belum terhubung ke Google Sheet. Chat bot tetap jalan, tapi data tidak tersimpan otomatis.")
        return None

sheet = init_connections()

# --- 3. FUNGSI SIMPAN DATA (LOGGING) ---
def save_log(nama, pesan_siswa, respon_ai):
    if sheet:
        try:
            tz = pytz.timezone('Asia/Jakarta')
            waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([waktu, nama, pesan_siswa, respon_ai])
        except Exception as e:
            print(f"Gagal simpan log: {e}")

# --- 4. TAMPILAN UTAMA (FRONTEND) ---

# Sidebar (Menu Samping)
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/meditation-guru.png", width=80)
    st.title("Panduan Siswa")
    st.info("""
    1. **Tulis Namamu** di kolom yang tersedia.
    2. **Ceritakan** kesulitanmu atau **ketik soal** pecahanmu.
    3. **Math Relax AI** akan membantumu pelan-pelan.
    4. Jangan takut salah ya! 😊
    """)
    if st.button("🔄 Mulai Percakapan Baru"):
        st.session_state.messages = []
        st.rerun()

st.title("🧘 Math Relax AI")
st.caption("Teman Belajar Matematika yang Menenangkan Hati")

# --- 5. LOGIC APLIKASI ---

# A. Input Nama Siswa
if "user_name" not in st.session_state or st.session_state.user_name == "":
    st.markdown("### 👋 Halo! Kenalan dulu yuk.")
    nama_input = st.text_input("Tulis nama panggilanmu di sini:", placeholder="Contoh: Budi")
    if st.button("Masuk Kelas"):
        if nama_input.strip():
            st.session_state.user_name = nama_input.strip()
            st.rerun()
    st.stop() # Berhenti di sini sampai nama diisi

# B. Sapaan Personal
st.success(f"Selamat datang, **{st.session_state.user_name}**! Silakan tanya apa saja tentang Pecahan.")

# C. Otak AI (System Prompt - Kunci Tesis)
system_instruction = f"""
Kamu adalah 'Math Relax AI', asisten belajar matematika yang sabar dan empatik untuk siswa SD Fase C.
Nama siswa saat ini adalah: {st.session_state.user_name}.

Tugas Utamamu:
1. Mereduksi kecemasan (Math Anxiety) dengan kalimat menenangkan.
2. Mengajarkan materi PECAHAN (tambah, kurang, kali, bagi).

Aturan Menjawab:
- Panggil siswa dengan namanya ({st.session_state.user_name}) sesekali agar akrab.
- Jika siswa bertanya soal (misal: 1/2 + 1/4), JANGAN langsung beri jawaban akhir.
- Tuntun langkah demi langkah (Scaffolding). Tanya dulu: "Kira-kira penyebutnya sudah sama belum?"
- Gunakan format LaTeX untuk pecahan ($ \\frac{{a}}{{b}} $).
- Berikan pujian jika siswa berhasil atau berusaha.
"""

model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)

# D. Menampilkan Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Sapaan awal otomatis dari AI
    welcome_msg = f"Halo {st.session_state.user_name}! Apa yang bikin kamu bingung soal pecahan hari ini? Cerita aja ya..."
    st.session_state.messages.append({"role": "model", "content": welcome_msg})

for message in st.session_state.messages:
    role = "user" if message["role"] == "user" else "assistant"
    avatar = "🧑‍🎓" if role == "user" else "🤖"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# E. Input & Respon
if prompt := st.chat_input("Ketik di sini..."):
    # 1. Tampilkan pesan siswa
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Proses AI
    with st.chat_message("assistant", avatar="🤖"):
        msg_placeholder = st.empty()
        full_response = ""
        
        try:
            # Kirim history agar nyambung
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"
            ])
            response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    msg_placeholder.markdown(full_response + "▌")
            msg_placeholder.markdown(full_response)
            
            # 3. Simpan ke Log Google Sheets (Background Process)
            save_log(st.session_state.user_name, prompt, full_response)
            
        except Exception as e:
            st.error(f"TERJADI ERROR: {e}") # Ini akan memberitahu kita masalahnya
            full_response = "Maaf, error koneksi."

    # 4. Simpan ke Session State
    st.session_state.messages.append({"role": "model", "content": full_response})
