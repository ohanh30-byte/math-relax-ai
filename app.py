import streamlit as st
from google import genai
import time
import os
from gtts import gTTS
from io import BytesIO
import base64

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Math Relax AI",
    page_icon="🧩",
    layout="centered"
)

# --- 2. FUNGSI SUARA OTOMATIS (AUTOPLAY) ---
def text_to_speech_autoplay(text):
    """Mengubah teks jadi suara dan memutarnya otomatis"""
    try:
        # Hapus karakter aneh agar suara bersih
        clean_text = text.replace("*", "").replace("#", "").replace("-", " ")
        
        tts = gTTS(text=clean_text, lang='id', slow=False)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        audio_base64 = base64.b64encode(mp3_fp.read()).decode('utf-8')
        audio_html = f"""
            <audio controls autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            </audio>
            """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.caption("🔇 (Suara sedang istirahat)")

# --- 3. SETUP KONEKSI (DIPERBAIKI DENGAN AUTO-PILOT) ---
@st.cache_resource
def setup_connection():
    api_key = None
    # Cek File Lokal
    if os.path.exists("apikey.txt"):
        with open("apikey.txt", "r") as f:
            api_key = f.read().strip()
    # Cek Secrets (Online)
    elif "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    
    if not api_key:
        return None, None

    try:
        client = genai.Client(api_key=api_key)
        
        # --- LOGIKA AUTO-DETEKSI (KEMBALI DIADAKAN) ---
        # Mencari model yang PASTI ada di akun Bapak
        all_models = list(client.models.list())
        chosen_model = ""
        
        # Cari yang mengandung 'flash' (cepat)
        for m in all_models:
            if "gemini" in m.name and "flash" in m.name and "exp" not in m.name:
                chosen_model = m.name.replace("models/", "")
                break
        
        # Jika tidak ketemu, ambil sembarang gemini
        if not chosen_model:
            for m in all_models:
                if "gemini" in m.name:
                    chosen_model = m.name.replace("models/", "")
                    break
                    
        return client, chosen_model
        
    except Exception as e:
        return None, None

# --- 4. LOGIN ---
if "user_name" not in st.session_state:
    st.session_state.user_name = None

if st.session_state.user_name is None:
    st.title("🧩 Math Relax AI")
    st.write("Belajar Pecahan Kelas 6 SD")
    with st.form("login_form"):
        input_nama = st.text_input("Halo! Siapa namamu?", placeholder="Tulis nama di sini...")
        submit_btn = st.form_submit_button("Masuk Kelas 🚀")
        if submit_btn and input_nama:
            st.session_state.user_name = input_nama
            st.rerun()
    st.stop()

# --- 5. TAMPILAN UTAMA ---
client, model_name = setup_connection()

if not client or not model_name:
    st.error("❌ Koneksi Gagal. Cek API Key atau Internet.")
    st.stop()

st.markdown(f"### Hai, {st.session_state.user_name}! 👋")
st.caption("Teman Belajar Pecahan yang Sabar & Santai")
st.divider()

# --- 6. INSTRUKSI GURU (MODE SCAFFOLDING) ---
SYSTEM_INSTRUCTION = f"""
PERAN:
Kamu adalah "Kak Gemmy", tutor matematika pribadi untuk siswa SD Kelas 6.
Siswa: {st.session_state.user_name}.
Topik: Pecahan (Fractions).

ATURAN WAJIB (STRICT RULES):
1.  **DILARANG MEMBERIKAN JAWABAN AKHIR SECARA LANGSUNG.**
2.  Gunakan metode "Scaffolding" (Bertingkat). Bimbing siswa langkah demi langkah.
3.  Jika siswa bertanya soal (misal: "1/2 + 1/3 berapa?"), JAWABLAH dengan pertanyaan pancingan: "Oke, yuk kita lihat penyebutnya (angka bawah). Angka 2 dan 3 sudah sama belum ya?"
4.  Gunakan bahasa percakapan yang sangat santai.
5.  Sebutkan angka pecahan dengan huruf (contoh: tulis "satu per dua" jangan hanya "1/2") agar suara robot lancar.

TUJUAN:
Menurunkan kecemasan siswa.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
    sapaan = f"Halo {st.session_state.user_name}! Kak Gemmy siap bantu. Ada soal pecahan yang bikin kamu bingung?"
    st.session_state.messages.append({"role": "assistant", "content": sapaan})

# Tampilkan Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 7. INPUT & RESPON ---
if prompt := st.chat_input("Tanya Kak Gemmy di sini..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_box = st.empty()
        full_response = ""
        try:
            chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            full_prompt = f"{SYSTEM_INSTRUCTION}\n\nRiwayat:\n{chat_history}\n\nSiswa: {prompt}\nKak Gemmy:"
            
            # Gunakan model_name hasil auto-deteksi (bukan hardcode)
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            full_response = response.text
            
            message_box.markdown(full_response)
            
            # Autoplay Suara
            with st.spinner("Kak Gemmy sedang bicara..."):
                text_to_speech_autoplay(full_response)
            
        except Exception as e:
            full_response = "Yah, sinyalnya putus. Coba tanya lagi ya!"
            st.error(f"Error detail: {e}") # Tampilkan error asli biar jelas

    st.session_state.messages.append({"role": "assistant", "content": full_response})
