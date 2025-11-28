import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Math Relax AI", page_icon="🧘", layout="centered")

# --- KONEKSI KE GOOGLE SHEETS & GEMINI ---
# Cek apakah secrets sudah ada
if "gcp_service_account" in st.secrets and "GEMINI_API_KEY" in st.secrets:
    # 1. Setup Gemini AI
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 2. Setup Google Sheets
    # Membuat objek credentials dari secrets Streamlit
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    client = gspread.authorize(creds)
    
    # Buka Sheet (Pastikan nama file di Google Drive SAMA PERSIS dengan ini)
    SHEET_NAME = "Database_Math_Relax" 
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except:
        st.error(f"Gagal menemukan Google Sheet dengan nama '{SHEET_NAME}'. Pastikan nama file benar dan sudah dibagikan ke email Service Account.")
        st.stop()
else:
    st.error("Secrets belum dikonfigurasi. Mohon cek Streamlit Cloud Dashboard.")
    st.stop()

# --- FUNGSI MENYIMPAN DATA ---
def save_to_sheet(nama, user_input, ai_response):
    # Waktu WIB
    tz = pytz.timezone('Asia/Jakarta')
    waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    
    # Tambah baris baru ke sheet
    # Format: [Waktu, Nama, Input Siswa, Respon AI]
    sheet.append_row([waktu, nama, user_input, ai_response])

# --- UI APLIKASI ---
st.title("🧘 Math Relax AI")

# Identitas Siswa (Penting untuk Data Penelitian)
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if st.session_state.user_name == "":
    st.info("Halo! Sebelum mulai, tulis nama panggilanmu dulu ya 👇")
    nama_input = st.text_input("Nama Kamu:", placeholder="Misal: Budi")
    if st.button("Mulai Belajar"):
        if nama_input:
            st.session_state.user_name = nama_input
            st.rerun() # Refresh halaman
else:
    st.write(f"Halo, **{st.session_state.user_name}**! Semangat belajar Pecahannya ya! 🌱")
    
    # System Instruction (Otak AI)
    system_instruction = """
    Kamu adalah 'Math Relax AI', teman belajar matematika siswa SD Fase C.
    Fokus materi: Pecahan.
    Gaya bahasa: Ramah, suportif, menggunakan Emoji, dan Scaffolding (bertahap).
    JANGAN memberi jawaban langsung. Validasi emosi siswa jika mereka merasa sulit.
    Gunakan format LaTeX untuk rumus matematika.
    """
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)

    # Inisialisasi Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Tampilkan Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input Chat
    if prompt := st.chat_input("Tulis soal atau curhatmu di sini..."):
        # Tampilkan pesan user
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate Jawaban AI
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages])
            response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        # Simpan ke Session State
        st.session_state.messages.append({"role": "model", "content": full_response})
        
        # --- AUTO SAVE KE GOOGLE SHEETS ---
        try:
            save_to_sheet(st.session_state.user_name, prompt, full_response)
            # Opsional: Beri tanda kecil bahwa data tersimpan (bisa dihilangkan agar tidak mengganggu)
            # st.toast("Chat tersimpan otomatis ✅") 
        except Exception as e:
            print(f"Gagal menyimpan ke database: {e}")
