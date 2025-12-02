import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Math Relax AI",
    page_icon="🧘",
    layout="centered"
)

# --- 2. KONEKSI GOOGLE SHEETS & AI ---
def init_connections():
    # Cek apakah secrets ada
    if "gcp_service_account" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
        st.error("⚠️ Error: Secrets belum lengkap. Cek pengaturan Streamlit.")
        return None, None

    # Setup Google Sheets
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open("Database_Math_Relax").sheet1
    except Exception as e:
        # Jika sheet error, kita abaikan dulu agar aplikasi tetap jalan
        sheet = None

    # Setup Gemini AI
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # KITA PAKAI MODEL YANG PALING AMAN: GEMINI-1.5-FLASH
        # Perhatikan: Kita TIDAK memasukkan system_instruction di sini agar tidak error 404
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Error AI: {e}")
        return None, None

    return sheet, model

sheet, model = init_connections()

# --- 3. FUNGSI LOGGING (Simpan ke Excel) ---
def save_log(nama, pesan, respon):
    if sheet:
        try:
            tz = pytz.timezone('Asia/Jakarta')
            waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([waktu, nama, pesan, respon])
        except:
            pass # Diam saja kalau gagal simpan, jangan bikin panik user

# --- 4. TAMPILAN & LOGIKA UTAMA ---
st.title("🧘 Math Relax AI")
st.caption("Teman Belajar Matematika SD Fase C")

# Input Nama
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if not st.session_state.user_name:
    nama = st.text_input("Tulis nama panggilanmu:", placeholder="Contoh: Budi")
    if st.button("Mulai"):
        if nama:
            st.session_state.user_name = nama
            st.rerun()
    st.stop()

st.success(f"Halo, **{st.session_state.user_name}**! Yuk cerita kesulitanmu.")

# Inisialisasi Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan Chat
for msg in st.session_state.messages:
    # Avatar: Siswa (👤) vs AI (🤖)
    icon = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

# Input Pesan Baru
if prompt := st.chat_input("Ketik di sini..."):
    # 1. Tampilkan pesan user
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Proses Jawaban AI (METODE ANTI-ERROR 404)
    with st.chat_message("assistant", avatar="🤖"):
        msg_box = st.empty()
        
        try:
            # --- RAHASIA JITU: KITA SELIPKAN INSTRUKSI DI SINI ---
            # Kita buat "Sejarah Buatan" agar AI tahu tugasnya tanpa perlu settingan rumit
            
            instruksi_guru = f"""
            PERAN: Kamu adalah 'Math Relax AI', guru privat matematika untuk siswa SD bernama {st.session_state.user_name}.
            TUGAS: Ajarkan Pecahan (Tambah, Kurang, Kali, Bagi).
            SIFAT: Sabar, ramah, gunakan emoji, jangan kaku.
            ATURAN: 
            1. JANGAN langsung kasih jawaban. Pandu langkah demi langkah (scaffolding).
            2. Validasi perasaan siswa (misal: "Tenang, jangan panik").
            3. Gunakan LaTeX untuk pecahan.
            """
            
            # Kita susun chat history manual
            history_ai = [
                {"role": "user", "parts": [instruksi_guru]},
                {"role": "model", "parts": ["Siap, saya mengerti. Saya akan menjadi guru yang ramah."]}
            ]
            
            # Masukkan chat asli siswa
            for m in st.session_state.messages:
                # Ubah role 'user'/'assistant' jadi format Gemini
                role_gemini = "user" if m["role"] == "user" else "model"
                history_ai.append({"role": role_gemini, "parts": [m["content"]]})
            
            # Mulai Chat dengan History yang sudah dimanipulasi
            chat = model.start_chat(history=history_ai[:-1]) # Ambil semua kecuali pesan terakhir
            response = chat.send_message(prompt) # Kirim pesan terakhir
            
            full_text = response.text
            msg_box.markdown(full_text)
            
            # Simpan ke memori tampilan
            st.session_state.messages.append({"role": "assistant", "content": full_text})
            
            # Simpan ke Excel
            save_log(st.session_state.user_name, prompt, full_text)
            
        except Exception as e:
            # Jika masih error, tampilkan pesan jelas
            st.error(f"Maaf, ada gangguan teknis: {e}")
            st.session_state.messages.append({"role": "assistant", "content": "Maaf, coba tanya lagi ya."})
