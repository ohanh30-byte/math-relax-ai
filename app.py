import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# --- 1. SETUP HALAMAN ---
st.set_page_config(page_title="Math Relax AI", page_icon="🧘", layout="centered")

# --- 2. KONEKSI KE GOOGLE (DENGAN MODEL YANG SUDAH TERBUKTI ADA) ---
def init_app():
    # Cek Kunci
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Kunci belum dipasang. Cek Secrets.")
        return None, None
    
    # Setup AI
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # KITA PAKAI MODEL YANG MUNCUL DI DIAGNOSA BAPAK TADI:
        model = genai.GenerativeModel('gemini-1.5-flash') 
    except Exception as e:
        st.error(f"Error Koneksi AI: {e}")
        return None, None

    # Setup Excel (Opsional, biar gak error kalau sheet bermasalah)
    sheet = None
    try:
        if "gcp_service_account" in st.secrets:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
            client = gspread.authorize(creds)
            sheet = client.open("Database_Math_Relax").sheet1
    except:
        pass # Lanjut saja kalau excel gagal

    return model, sheet

model, sheet = init_app()

# --- 3. FUNGSI SIMPAN DATA ---
def simpan_log(role, pesan):
    if sheet:
        try:
            tz = pytz.timezone('Asia/Jakarta')
            waktu = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([waktu, role, pesan])
        except:
            pass

# --- 4. TAMPILAN UTAMA ---
st.title("🧘 Math Relax AI")
st.caption("Teman Belajar Matematika SD Fase C - Pecahan")

# Sapaan Awal
if "messages" not in st.session_state:
    st.session_state.messages = []
    sapaan = "Halo! Aku Math Relax AI. Jangan takut sama matematika ya. Kita belajar Pecahan pelan-pelan. Kamu mau tanya apa?"
    st.session_state.messages.append({"role": "model", "content": sapaan})

# Tampilkan Chat History
for msg in st.session_state.messages:
    # Tentukan ikon
    ikon = "🧑‍🎓" if msg["role"] == "user" else "🧘" 
    with st.chat_message(msg["role"], avatar=ikon):
        st.markdown(msg["content"])

# --- 5. LOGIKA CHAT (METODE ANTI-ERROR) ---
if prompt := st.chat_input("Ketik soal atau curhatmu di sini..."):
    # Tampilkan Pesan Siswa
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    simpan_log("Siswa", prompt) # Simpan ke Excel

    # Proses Jawaban AI
    with st.chat_message("model", avatar="🧘"):
        if model:
            placeholder = st.empty()
            try:
                # KITA SELIPKAN INSTRUKSI GURU DI SINI (Supaya tidak Error 404 System Instruction)
                # Ini trik paling aman:
                chat_session = model.start_chat(history=[
                    {
                        "role": "user",
                        "parts": ["Mulai sekarang, berperanlah sebagai Guru SD yang sabar, ramah, dan menenangkan (Math Anxiety Therapy). Ajarkan materi PECAHAN. Jangan langsung beri jawaban, tapi bimbing langkah demi langkah. Panggil siswa dengan sebutan 'Teman'."]
                    },
                    {
                        "role": "model",
                        "parts": ["Siap! Saya akan menjadi guru matematika yang ramah, sabar, dan menenangkan untuk materi Pecahan."]
                    },
                ])
                
                # Masukkan history chat sebelumnya (supaya nyambung)
                for m in st.session_state.messages:
                    if m["role"] != "system": # Skip system jika ada
                        # Mapping role biar sesuai standar Google
                        role_google = "user" if m["role"] == "user" else "model"
                        try:
                            chat_session.history.append({"role": role_google, "parts": [m["content"]]})
                        except:
                            pass

                # Kirim Pesan Baru
                response = chat_session.send_message(prompt)
                jawaban_ai = response.text
                
                placeholder.markdown(jawaban_ai)
                st.session_state.messages.append({"role": "model", "content": jawaban_ai})
                simpan_log("AI", jawaban_ai) # Simpan ke Excel
                
            except Exception as e:
                st.error(f"Maaf, internet sedang gangguan. Coba lagi ya. Error: {e}")
        else:
            st.error("Sistem sedang memuat ulang. Coba refresh halaman.")
