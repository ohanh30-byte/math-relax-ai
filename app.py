import streamlit as st
import google.generativeai as genai

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="Math Relax AI", page_icon="🧘", layout="centered")

# 2. Judul dan Intro yang Menenangkan
st.title("🧘 Math Relax AI")
st.write("Hai! Aku teman belajarmu. Kita bahas **Pecahan** dengan santai ya. Jangan takut salah, kita belajar sama-sama!")

# 3. Pengaturan API Key (Akan kita set di langkah deployment)
# Mengambil API key dari "Secrets" Streamlit agar aman
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("API Key belum dipasang. Mohon konfigurasi di Streamlit Cloud.")

# 4. Inisialisasi Model AI & Prompt Pedagogis (Bagian Terpenting untuk Tesis)
# Disini kita mengatur "Otak" dan "Kepribadian" AI
system_instruction = """
Kamu adalah 'Math Relax AI', asisten belajar matematika khusus untuk siswa SD Fase C (Kelas 5-6).
Tujuan utamamu adalah:
1. Menurunkan kecemasan matematika siswa (Math Anxiety).
2. Mengajarkan materi PECAHAN (Penjumlahan, Pengurangan, Perkalian, Pembagian).

Aturan Menjawab:
- Gunakan bahasa Indonesia yang santai, ramah, dan menyemangati (seperti kakak yang baik).
- JANGAN langsung memberikan jawaban akhir. Gunakan metode Scaffolding (bertahap).
- Jika siswa bertanya soal (misal: 1/2 + 1/3), ajak siswa mencari KPK penyebutnya dulu.
- Selalu validasi perasaan siswa (contoh: "Wah, soal ini memang terlihat rumit, tapi kamu pasti bisa!").
- Tuliskan pecahan menggunakan format LaTeX (contoh: $ \\frac{1}{2} $) agar rapi.
- Jika siswa bertanya di luar matematika/pecahan, arahkan kembali ke topik dengan sopan.
"""

model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)

# 5. Mengelola Riwayat Chat (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Menampilkan chat sebelumnya di layar
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Logika Chatting (Input & Respon)
if prompt := st.chat_input("Ketik soal atau curhatmu di sini..."):
    # Tampilkan pesan siswa
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Proses jawaban AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Mengirim history chat agar AI ingat konteks percakapan
        chat = model.start_chat(history=[
            {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages
        ])
        
        response = chat.send_message(prompt, stream=True)
        
        # Efek mengetik
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
    
    # Simpan jawaban AI ke memori
    st.session_state.messages.append({"role": "model", "content": full_response})
