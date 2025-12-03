import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- 1. SETUP HALAMAN ---
st.set_page_config(
    page_title="Math Relax AI", 
    page_icon="🧘", 
    layout="centered",
    initial_sidebar_state="collapsed" # Sembunyikan sidebar agar layar penuh
)

# --- CUSTOM CSS (TAMPILAN ALA WHATSAPP MOBILE) ---
st.markdown("""
<style>
    /* 1. MENGATUR UKURAN LAYAR UTAMA AGAR SEPERTI HP */
    .block-container {
        padding-top: 1rem;   /* Buang ruang kosong atas */
        padding-bottom: 5rem; /* Beri ruang untuk kotak ketik bawah */
        max-width: 700px;    /* Batasi lebar maksimal biar fokus */
    }

    /* 2. LATAR BELAKANG KREM ALA WA */
    .stApp {
        background-color: #E5DDD5;
        background-image: url("https://i.pinimg.com/originals/8f/5d/46/8f5d46059d084c7f0f6396f9c9417859.png"); /* Opsional: Pattern WA */
        background-size: cover;
    }
    
    /* 3. GELEMBUNG CHAT YANG LEBIH RAPI & RAPAT */
    .stChatMessage {
        padding: 1rem;
        margin-bottom: 0.5rem; /* Jarak antar chat lebih dekat */
    }

    /* User (Siswa) - Hijau Muda */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #DCF8C6;
        border-radius: 15px 0px 15px 15px; /* Sudut tumpul khas WA */
        border: 1px solid #dcdcdc;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* AI (Guru) - Putih */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF;
        border-radius: 0px 15px 15px 15px; /* Sudut tumpul khas WA */
        border: 1px solid #dcdcdc;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* 4. MEMPERCANTIK JUDUL */
    h1 {
        color: #075E54; /* Hijau Tua WA */
        font-size: 1.8rem;
        text-align: center;
        margin-bottom: 0px;
    }
    p {
        color: #4a4a4a;
    }
    
    /* Sembunyikan elemen bawaan Streamlit yang mengganggu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. KONEKSI KE GOOGLE ---
def init_app():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Kunci belum dipasang.")
        return None, None
    
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash') 
    except Exception as e:
        st.error(f"Error AI: {e}")
        return None, None

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

# --- 3. FUNGSI SIMPAN DATA ---
def simpan_log(nama_siswa, role, pesan):
    if sheet:
        try:
            tz = pytz.timezone('Asia/Jakarta')
            waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([waktu, nama_siswa, role, pesan])
        except:
            pass

# --- 4. LOGIN SCREEN (Dibuat lebih compact) ---
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if not st.session_state.user_name:
    # Tampilan Login
    st.markdown("<br><br>", unsafe_allow_html=True) # Spasi dikit
    st.title("🧘 Math Relax AI")
    
    with st.container(border=True): # Masukkan dalam kotak putih
        st.markdown("<h3 style='text-align: center;'>👋 Masuk Kelas</h3>", unsafe_allow_html=True)
        st.write("Masukkan nama dulu ya biar Pak Guru kenal.")
        
        nama_input = st.text_input("Nama Panggilan:", placeholder="Contoh: Budi")
        
        if st.button("Mulai Chat 🚀", use_container_width=True):
            if nama_input.strip():
                st.session_state.user_name = nama_input.strip()
                st.rerun()
    st.stop()

# --- 5. CHAT ROOM UTAMA ---
# Header Chat (Sederhana)
st.title("Math Relax AI")
st.caption(f"👤 Siswa: {st.session_state.user_name} | 🟢 Online")

# Sapaan Awal
if "messages" not in st.session_state:
    st.session_state.messages = []
    sapaan = f"Halo {st.session_state.user_name}! 👋\n\nAnggap aja ini WA Pak Guru. Jangan sungkan buat tanya soal Pecahan yang bikin bingung ya. 😊"
    st.session_state.messages.append({"role": "model", "content": sapaan})

# Tampilkan History
for msg in st.session_state.messages:
    ikon = "🧑‍🎓" if msg["role"] == "user" else "🧘" 
    with st.chat_message(msg["role"], avatar=ikon):
        st.markdown(msg["content"])

# --- 6. INPUT PESAN ---
if prompt := st.chat_input("Ketik pesan..."):
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    simpan_log(st.session_state.user_name, "Siswa", prompt)

    with st.chat_message("model", avatar="🧘"):
        if model:
            placeholder = st.empty()
            try:
                chat_session = model.start_chat(history=[
                    {"role": "user", "parts": [f"Kamu adalah Guru SD ramah. Nama siswa: {st.session_state.user_name}. Materi: PECAHAN. Gaya bicara: Pendek, Santai seperti chatting WhatsApp, pakai emoji. Metode: Scaffolding."]},
                    {"role": "model", "parts": ["Siap!"]}
                ])
                
                for m in st.session_state.messages:
                    if m["role"] != "system":
                        role_google = "user" if m["role"] == "user" else "model"
                        try:
                            chat_session.history.append({"role": role_google, "parts": [m["content"]]})
                        except:
                            pass

                response = chat_session.send_message(prompt)
                jawaban_ai = response.text
                
                placeholder.markdown(jawaban_ai)
                st.session_state.messages.append({"role": "model", "content": jawaban_ai})
                simpan_log(st.session_state.user_name, "AI", jawaban_ai)
                
            except Exception as e:
                st.error("Koneksi lambat. Coba lagi.")
