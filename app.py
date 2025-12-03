import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- 1. SETUP HALAMAN ---
st.set_page_config(page_title="Math Relax AI", page_icon="🧘", layout="centered")

# --- CUSTOM CSS (TAMPILAN ALA WHATSAPP) ---
st.markdown("""
<style>
    /* Latar Belakang Aplikasi ala WA (Krem) */
    .stApp {
        background-color: #E5DDD5;
    }
    
    /* Warna Gelembung Chat */
    /* User (Siswa) - Hijau Muda */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #DCF8C6;
        border-radius: 10px;
        border: 1px solid #dcdcdc;
    }
    /* AI (Guru) - Putih */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF;
        border-radius: 10px;
        border: 1px solid #dcdcdc;
    }
    
    /* Tulisan Judul & Caption */
    h1, p {
        color: #075E54; /* Hijau Tua WA */
    }
</style>
""", unsafe_allow_html=True)

# --- 2. KONEKSI KE GOOGLE ---
def init_app():
    # Cek Kunci
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Kunci belum dipasang. Cek Secrets.")
        return None, None
    
    # Setup AI (VERSI 2.5 SESUAI AKUN BAPAK)
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash') 
    except Exception as e:
        st.error(f"Error Koneksi AI: {e}")
        return None, None

    # Setup Excel
    sheet = None
    try:
        if "gcp_service_account" in st.secrets:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
            client = gspread.authorize(creds)
            sheet = client.open("Database_Math_Relax").sheet1
    except:
        pass 

    return model, sheet

model, sheet = init_app()

# --- 3. FUNGSI SIMPAN DATA (DENGAN NAMA SISWA) ---
def simpan_log(nama_siswa, role, pesan):
    if sheet:
        try:
            tz = pytz.timezone('Asia/Jakarta')
            waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            # Format Excel: [Waktu, Nama Siswa, Siapa yg bicara, Isi Pesan]
            sheet.append_row([waktu, nama_siswa, role, pesan])
        except:
            pass

# --- 4. LOGIKA LOGIN NAMA (PENTING UNTUK TESIS) ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# Jika nama belum diisi, tampilkan halaman Login
if not st.session_state.user_name:
    st.title("🧘 Math Relax AI")
    st.markdown("### 👋 Halo! Kenalan dulu yuk.")
    st.info("Aplikasi ini didesain seperti WhatsApp agar kamu nyaman curhat matematika.")
    
    nama_input = st.text_input("Tulis nama panggilanmu di sini:", placeholder="Contoh: Budi Kelas 5A")
    
    if st.button("Masuk ke Chatroom 🚀"):
        if nama_input.strip():
            st.session_state.user_name = nama_input.strip()
            st.rerun() # Refresh halaman untuk masuk ke chat
    
    st.stop() # Berhenti di sini, jangan muat chat dulu

# --- 5. TAMPILAN CHAT UTAMA (SETELAH LOGIN) ---
st.title(f"🧘 Chatroom: {st.session_state.user_name}")
st.caption("Guru Privat Matematika Kamu (Pecahan)")

# Sapaan Awal
if "messages" not in st.session_state:
    st.session_state.messages = []
    sapaan = f"Halo {st.session_state.user_name}! 👋 Aku siap bantu kamu belajar Pecahan. Jangan ragu buat cerita ya, anggap aja lagi WA-an sama teman."
    st.session_state.messages.append({"role": "model", "content": sapaan})

# Tampilkan Chat History
for msg in st.session_state.messages:
    # Ikon: Siswa pakai orang, AI pakai robot yoga
    ikon = "🧑‍🎓" if msg["role"] == "user" else "🧘" 
    with st.chat_message(msg["role"], avatar=ikon):
        st.markdown(msg["content"])

# --- 6. PROSES CHAT ---
if prompt := st.chat_input("Ketik pesanmu di sini..."):
    # Tampilkan Pesan Siswa
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # SIMPAN KE EXCEL (Dengan Nama Siswa)
    simpan_log(st.session_state.user_name, "Siswa", prompt)

    # Proses Jawaban AI
    with st.chat_message("model", avatar="🧘"):
        if model:
            placeholder = st.empty()
            try:
                # Instruksi Guru
                chat_session = model.start_chat(history=[
                    {
                        "role": "user",
                        "parts": [f"Kamu adalah Guru SD ramah. Nama siswa: {st.session_state.user_name}. Materi: PECAHAN. Gaya bicara: Santai seperti chatting di WhatsApp, gunakan emoji. Metode: Scaffolding (bertahap)."]
                    },
                    {
                        "role": "model",
                        "parts": ["Siap! Saya mengerti."]
                    },
                ])
                
                # Masukkan history
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
                
                # SIMPAN KE EXCEL (Jawaban AI)
                simpan_log(st.session_state.user_name, "AI", jawaban_ai)
                
            except Exception as e:
                st.error("Koneksi agak lambat nih. Coba kirim lagi ya.")
