import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- KONFIGURASI ---
st.set_page_config(page_title="Math Relax AI", page_icon="🧘")

# --- KONEKSI ---
def init():
    # 1. Cek Kunci
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Kunci AI belum dipasang di Secrets.")
        return None, None
    
    # 2. Setup AI (Dengan Auto-Detect Model)
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # TRIK JITU: Coba model satu per satu sampai ketemu yang bisa
    daftar_model = ['gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
    model_aktif = None
    
    for nama_model in daftar_model:
        try:
            m = genai.GenerativeModel(nama_model)
            # Tes panggil sedikit
            m.generate_content("Tes")
            model_aktif = m
            # st.toast(f"Tersambung ke otak: {nama_model}") # Debug info
            break
        except:
            continue
            
    if not model_aktif:
        st.error("Gagal menemukan model AI yang cocok. Coba buat API Key baru di Google AI Studio.")
        return None, None

    # 3. Setup Excel
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open("Database_Math_Relax").sheet1
    except:
        sheet = None

    return sheet, model_aktif

sheet, model = init()

# --- LOGIKA CHAT ---
st.title("🧘 Math Relax AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Tampilkan Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Chat
if prompt := st.chat_input("Ceritakan masalah matematikamu..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        if model:
            try:
                # Instruksi Guru (Manual di belakang layar)
                prompt_guru = f"""
                Bertindaklah sebagai guru SD yang ramah.
                Nama siswa: Teman.
                Tugas: Ajarkan pecahan dengan sabar. Jangan langsung beri jawaban.
                Pertanyaan siswa: {prompt}
                """
                
                response = model.generate_content(prompt_guru)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "model", "content": response.text})
                
                # Simpan ke Excel
                if sheet:
                    try:
                        tz = pytz.timezone('Asia/Jakarta')
                        waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                        sheet.append_row([waktu, "Siswa", prompt, response.text])
                    except:
                        pass
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("AI sedang istirahat. Refresh halaman.")
