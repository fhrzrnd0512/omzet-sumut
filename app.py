import streamlit as st
import pandas as pd
import numpy as np
import urllib.parse

st.set_page_config(page_title="Koreksi Omzet 888 - BPS Sumut", layout="wide")
st.title("🛠️ Kalkulator & Smart Search Estimasi Omzet")

def is_888(val):
    try:
        return str(int(val)).endswith('888')
    except:
        return False

def hitung_estimasi(row):
    tk_total = row.get('tk_laki', 0) + row.get('tk_pr', 0)
    if pd.isna(tk_total) or tk_total == 0:
        tk_total = 1
        
    asumsi_gaji_tahunan = tk_total * 35910708 
    
    biaya_valid = 0
    for col in ['gaji', 'biaya_produksi', 'biaya_pembelian', 'operasional']:
        if col in row and not is_888(row[col]) and not pd.isna(row[col]):
            biaya_valid += row[col]
            
    batas_bawah = max(biaya_valid, asumsi_gaji_tahunan)
    batas_atas = batas_bawah * 1.5 
    return pd.Series([batas_bawah, batas_atas])

def generate_smart_search_url(row):
    nama = str(row.get('nama_usaha', '')).strip()
    alamat = str(row.get('alamat', '')).strip()
    kab_kode = str(row.get('kab', ''))
    
    lokasi = "Sumatera Utara"
    if kab_kode == "1275":
        lokasi = "Medan"
    elif kab_kode == "1212":
        lokasi = "Deli Serdang"
        
    if alamat.upper() == 'G' or pd.isna(alamat):
        alamat_query = ""
    else:
        alamat_query = alamat

    query = f'"{nama}" {alamat_query} {lokasi}'
    query_encoded = urllib.parse.quote(query)
    return f"https://www.google.com/search?q={query_encoded}"

with st.sidebar:
    st.header("🔍 Quick Google Search")
    search_query = st.text_input("Cari Usaha:", placeholder="Contoh: Toko Sembako Medan")
    if search_query:
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        st.markdown(f"[👉 **Klik di sini untuk mencari '{search_query}' di Google**]({search_url})")

uploaded_file = st.file_uploader("Upload file Excel penugasan", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if 'PIC PENGECEKAN' in df.columns:
        df = df[df['PIC PENGECEKAN'].str.contains('Fahriza', na=False, case=False)]
    
    df['is_omzet_888'] = df['nilai_pendapatan'].apply(is_888)
    df_filtered = df[df['is_omzet_888']].copy()
    
    if not df_filtered.empty:
        df_filtered[['Batas_Bawah_Est', 'Batas_Atas_Est']] = df_filtered.apply(hitung_estimasi, axis=1)
        df_filtered['GOOGLE_SEARCH'] = df_filtered.apply(generate_smart_search_url, axis=1)
        
        if 'PERKIRAAN OMSET' not in df_filtered.columns:
            df_filtered['PERKIRAAN OMSET'] = 0
            
        kolom_penting = ['nama_usaha', 'GOOGLE_SEARCH', 'Batas_Bawah_Est', 'Batas_Atas_Est', 
                         'PERKIRAAN OMSET', 'LINK', 'tk_laki', 'tk_pr', 'nilai_pendapatan']
            
        df_tampil = df_filtered[kolom_penting].copy()
        
        edited_df = st.data_editor(
            df_tampil,
            column_config={
                "GOOGLE_SEARCH": st.column_config.LinkColumn("🔍 Cari di Google", display_text="Googling Usaha"),
                "LINK": st.column_config.LinkColumn("🔗 Link FASIH", display_text="Buka FASIH"),
                "nilai_pendapatan": st.column_config.NumberColumn("Omzet 888", disabled=True),
                "Batas_Bawah_Est": st.column_config.NumberColumn("Est Bawah (Rp)", format="%d", disabled=True),
                "Batas_Atas_Est": st.column_config.NumberColumn("Est Atas (Rp)", format="%d", disabled=True),
                "PERKIRAAN OMSET": st.column_config.NumberColumn("Perkiraan Omzet Final (Rp)", format="%d"),
                "nama_usaha": st.column_config.TextColumn("Nama Usaha", disabled=True)
            },
            hide_index=True,
            num_rows="dynamic",
            height=600
        )
        
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Hasil Koreksi (CSV)",
            data=csv,
            file_name='hasil_koreksi_omzet_tervalidasi.csv',
            mime='text/csv',
        )
