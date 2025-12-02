import streamlit as st
import google.generativeai as genai
import sys

st.set_page_config(page_title="Dokter Diagnosa", page_icon="👨‍⚕️")

st.title("👨‍⚕️ Cek Diagnosa Math Relax AI")
st.write("Sedang memeriksa sistem Pak Ohan...")

# 1. CEK VERSI ALAT (Library)
st.divider()
st.subheader("1. Cek Versi Alat")
st.write(f"Versi Python: `{sys.version}`")
try:
    ver = genai.__version__
    st.write(f"Versi Google AI Library: **{ver}**")
    # Versi minimal harus 0.7.0 ke atas
except:
    st.error("Library Google AI rusak/tidak terbaca.")

# 2. CEK KUNCI RAHASIA
st.divider()
st.subheader("2. Cek Kunci (Secrets)")
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Kunci 'GEMINI_API_KEY' TIDAK DITEMUKAN di Secrets!")
    st.stop()
else:
    # Tampilkan 5 huruf depan saja untuk memastikan bukan kosong
    st.success(f"✅ Kunci ditemukan. Depan: `{api_key[:5]}...`")
    
    # Cek apakah ada spasi yang tidak sengaja terbawa
    if " " in api_key:
        st.warning("⚠️ Hati-hati! Sepertinya ada SPASI di dalam kunci Bapak. Cek Secrets lagi.")

# 3. CEK KONEKSI KE GOOGLE (Momen Penentuan)
st.divider()
st.subheader("3. Tes Koneksi ke Server Google")

genai.configure(api_key=api_key)

try:
    st.info("Mencoba mengetuk pintu server Google...")
    # Kita coba minta daftar model yang tersedia
    list_model = genai.list_models()
    
    found_models = []
    for m in list_model:
        # Cari model yang bisa generate text
        if 'generateContent' in m.supported_generation_methods:
            found_models.append(m.name)
    
    if found_models:
        st.success("🎉 ALHAMDULILLAH! KONEKSI BERHASIL!")
        st.write("Model yang tersedia untuk akun Bapak:")
        st.code(found_models)
        st.write("---")
        st.write("**Kesimpulan:** Akun Bapak SEHAT. Masalah sebelumnya ada di kode pemanggil model.")
    else:
        st.warning("Koneksi berhasil, tapi Google bilang TIDAK ADA model yang boleh Bapak pakai. (Biasanya karena akun Kampus/Region)")

except Exception as e:
    st.error("❌ GAGAL TERHUBUNG (CRITICAL ERROR)")
    st.markdown(f"**Pesan Error Asli dari Google:**")
    st.code(f"{e}")
    
    # Analisa Error Sederhana
    pesan_error = str(e)
    if "403" in pesan_error or "API key not valid" in pesan_error:
        st.write("👉 **Artinya:** Kunci Salah / Typo / Sudah dihapus.")
    elif "404" in pesan_error:
        st.write("👉 **Artinya:** Versi Library Lama atau Model tidak tersedia di akun ini.")
    elif "User location is not supported" in pesan_error:
        st.write("👉 **Artinya:** Lokasi/IP Bapak terblokir.")
