import streamlit as st
import pandas as pd
from saw import calculate_saw, CRITERIA

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Hoomly – DSS Pemilihan Rumah",
    page_icon="🏠",
    layout="wide",
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
.main-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #1a3c5e;
}

.sub-title {
    color: #666;
    margin-top: -10px;
    margin-bottom: 10px;
}

.block-container {
    padding-top: 2rem;
}

/* CARD METRIC */
[data-testid="metric-container"] {
    background-color: #111827;
    border: 1px solid #374151;
    padding: 20px;
    border-radius: 15px;
}

/* LABEL METRIC */
[data-testid="metric-container"] label {
    color: #D1D5DB !important;
}

/* VALUE METRIC */
[data-testid="metric-container"] div {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
col1, col2 = st.columns([1, 8])

with col1:
    st.markdown("# 🏠")

with col2:
    st.markdown(
        '<div class="main-title">Hoomly</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Sistem Pendukung Keputusan Pemilihan Rumah di Jabodetabek · Metode SAW</div>',
        unsafe_allow_html=True
    )

st.divider()

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    return pd.read_json("rumah_clean.json")

df = load_data()

kota_list = sorted(
    df["kota"].unique().tolist()
)

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown("## ⚙️ Preferensi Pengguna")

    # =====================================================
    # FILTER KOTA
    # =====================================================
    kota_sel = st.multiselect(
        "Pilih Kota",
        kota_list,
        default=kota_list
    )

    st.markdown("---")

    # =====================================================
    # FILTER HARGA
    # =====================================================
    st.markdown("### 💰 Rentang Harga")

    max_juta = int(
        df["harga"].max() // 1_000_000
    )

    harga_range = st.slider(
        "Harga Rumah (Juta Rp)",
        min_value=0,
        max_value=max_juta,
        value=(0, max_juta),
        step=100
    )

    st.markdown("---")

    # =====================================================
    # INPUT PREFERENSI RUMAH
    # =====================================================
    st.markdown("### 🏡 Preferensi Rumah")

    luas_bangunan = st.number_input(
        "📐 Minimal Luas Bangunan (m²)",
        min_value=0,
        value=0,
        step=10
    )

    luas_tanah = st.number_input(
        "🌳 Minimal Luas Tanah (m²)",
        min_value=0,
        value=0,
        step=10
    )

    kamar_tidur = st.number_input(
        "🛏️ Minimal Kamar Tidur",
        min_value=0,
        value=0,
        step=1
    )

    kamar_mandi = st.number_input(
        "🚿 Minimal Kamar Mandi",
        min_value=0,
        value=0,
        step=1
    )

    garasi = st.number_input(
        "🚗 Minimal Garasi",
        min_value=0,
        value=0,
        step=1
    )
    st.markdown("---")

    top_n = st.selectbox(
        "Tampilkan Top-N",
        [5, 10, 20, 50],
        index=1
    )

    run_btn = st.button(
        "🔍 Hitung Rekomendasi",
        use_container_width=True,
        type="primary"
    )

# =========================================================
# FILTER DATA
# =========================================================
df_filtered = df[
    (df["harga"] >= harga_range[0] * 1_000_000) &
    (df["harga"] <= harga_range[1] * 1_000_000) &
    (df["luas_bangunan"] >= luas_bangunan) &
    (df["luas_tanah"] >= luas_tanah) &
    (df["kamar_tidur"] >= kamar_tidur) &
    (df["kamar_mandi"] >= kamar_mandi) &
    (df["garasi"] >= garasi)
].copy()

# =========================================================
# MAIN CONTENT
# =========================================================
tab1 = st.tabs(["📊 Rekomendasi"])[0]

# =========================================================
# TAB REKOMENDASI
# =========================================================
with tab1:

    if not run_btn:

        st.info(
            "👈 Atur preferensi di sidebar lalu klik Hitung Rekomendasi."
        )

    else:

        if not kota_sel:

            st.warning(
                "⚠️ Pilih minimal satu kota."
            )

        else:

            result = calculate_saw(
                df_filtered,
                kota_filter=kota_sel
            )

            if result.empty:

                st.error(
                    "❌ Tidak ada rumah yang sesuai."
                )

            else:

                top = result.head(top_n)

                st.success(
                    f"✅ Ditemukan {len(result)} rumah sesuai preferensi."
                )

                # =================================================
                # DETAIL RUMAH TERBAIK
                # =================================================
                st.markdown(
                    "## 🏡 Detail Rumah Terbaik"
                )

                best = top.iloc[0]

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "💰 Harga",
                    f"Rp {best['harga']/1e9:.2f} M"
                )

                c2.metric(
                    "📐 Luas Bangunan",
                    f"{best['luas_bangunan']} m²"
                )

                c3.metric(
                    "🌳 Luas Tanah",
                    f"{best['luas_tanah']} m²"
                )

                c4, c5, c6 = st.columns(3)

                c4.metric(
                    "🛏️ Kamar Tidur",
                    best["kamar_tidur"]
                )

                c5.metric(
                    "🚿 Kamar Mandi",
                    best["kamar_mandi"]
                )

                c6.metric(
                    "🚗 Garasi",
                    best["garasi"]
                )

                # =================================================
                # TABEL REKOMENDASI
                # =================================================
                st.markdown(
                    f"## 🏆 Top {top_n} Rekomendasi Rumah"
                )

                display_cols = [
                    "ranking",
                    "kota",
                    "harga",
                    "luas_bangunan",
                    "luas_tanah",
                    "kamar_tidur",
                    "kamar_mandi",
                    "garasi",
                    "skor_saw"
                ]

                top_display = top[
                    display_cols
                ].copy()

                top_display["harga"] = top_display[
                    "harga"
                ].apply(
                    lambda x: f"Rp {x/1e9:.2f} M"
                )

                st.dataframe(
                    top_display.rename(columns={
                        "ranking": "Rank",
                        "kota": "Kota",
                        "harga": "Harga",
                        "luas_bangunan": "Luas Bangunan",
                        "luas_tanah": "Luas Tanah",
                        "kamar_tidur": "KT",
                        "kamar_mandi": "KM",
                        "garasi": "Garasi",
                        "skor_saw": "Skor SAW"
                    }),
                    use_container_width=True,
                    hide_index=True
                )

                # =================================================
                # DOWNLOAD CSV
                # =================================================
                csv = result.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    "⬇️ Download Hasil CSV",
                    data=csv,
                    file_name="hasil_rekomendasi.csv",
                    mime="text/csv"
                )

                

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")

st.markdown(
    """
    <center>
    <small>
    Hoomly © 2026 · Universitas Brawijaya · Fakultas Ilmu Komputer
    </small>
    </center>
    """,
    unsafe_allow_html=True
)