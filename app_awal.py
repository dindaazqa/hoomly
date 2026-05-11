
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from saw import calculate_saw, CRITERIA

# ── Konfigurasi halaman ──────────────────────────────────────
st.set_page_config(
    page_title="Hoomly – DSS Pemilihan Rumah",
    page_icon="🏠",
    layout="wide",
)

# ── CSS kustom ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-title  { font-size:2.4rem; font-weight:800; color:#1a3c5e; }
    .sub-title   { font-size:1rem; color:#555; margin-top:-10px; }
    .metric-card { background:#f0f7ff; border-radius:12px;
                   padding:16px; text-align:center; }
    .stSlider > div { padding-top:4px; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.markdown("<div style='font-size:3rem'>🏠</div>", unsafe_allow_html=True)
with col_title:
    st.markdown('<p class="main-title">Hoomly</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Sistem Pendukung Keputusan Pemilihan Rumah di Jabodetabek · Metode SAW</p>',
                unsafe_allow_html=True)
st.divider()

# ── Load data ────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_json("rumah_clean.json")

df = load_data()
kota_list = sorted(df["kota"].unique().tolist())

# ── Sidebar: preferensi pengguna ─────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Preferensi Anda")
    st.markdown("**Filter Kota**")
    kota_sel = st.multiselect("Pilih kota:", kota_list, default=kota_list)

    st.markdown("---")
    st.markdown("**Rentang Harga (Juta Rp)**")

    min_juta = 0
    max_juta = int(df["harga"].max() // 1_000_000)

    harga_range = st.slider(
        "Harga",
        min_value=min_juta,
        max_value=max_juta,
        value=(0, max_juta),
        step=100   
    )


    st.markdown("---")
    st.markdown("**🎚️ Bobot Kriteria** *(total harus 100%)*")
    w_harga   = st.slider("C1 – Harga (cost)",          0, 100, 35)
    w_lb      = st.slider("C2 – Luas Bangunan",         0, 100, 25)
    w_lt      = st.slider("C3 – Luas Tanah",            0, 100, 15)
    w_kt      = st.slider("C4 – Kamar Tidur",           0, 100, 10)
    w_km      = st.slider("C5 – Kamar Mandi",           0, 100, 10)
    w_garasi  = st.slider("C6 – Garasi",                0, 100, 5)

    total_w = w_harga + w_lb + w_lt + w_kt + w_km + w_garasi
    if total_w == 0:
        st.error("⚠️ Semua bobot 0! Sesuaikan bobot.")
        st.stop()
    pct_bar = total_w / 100
    bar_color = "#2ecc71" if 95 <= total_w <= 105 else "#e74c3c"
    st.markdown(f"""
    <div style='background:#eee;border-radius:8px;height:12px'>
      <div style='background:{bar_color};border-radius:8px;
                  height:12px;width:{min(pct_bar*100,100):.0f}%'></div>
    </div>
    <small>Total bobot: <b>{total_w}%</b></small>
    """, unsafe_allow_html=True)

    st.markdown("---")
    top_n = st.selectbox("Tampilkan Top-N rumah", [5, 10, 20, 50], index=1)
    run_btn = st.button("🔍 Hitung Rekomendasi", use_container_width=True, type="primary")

# ── Pra-filter harga ─────────────────────────────────────────
df_filtered = df[
    (df["harga"] >= harga_range[0] * 1_000_000) &
    (df["harga"] <= harga_range[1] * 1_000_000)
].copy()

# ── Halaman utama: Tab ───────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Rekomendasi", "📈 Visualisasi", "📋 Dataset"])

weights = {
    "harga": w_harga, "luas_bangunan": w_lb, "luas_tanah": w_lt,
    "kamar_tidur": w_kt, "kamar_mandi": w_km, "garasi": w_garasi,
}

# ────────────────────────────────────────────────────────────
# TAB 1 – REKOMENDASI
# ────────────────────────────────────────────────────────────
with tab1:
    if not run_btn:
        st.info("👈 Atur preferensi di sidebar lalu klik **Hitung Rekomendasi**.")
    else:
        if not kota_sel:
            st.warning("Pilih minimal satu kota!")
        else:
            result = calculate_saw(df_filtered, weights, kota_filter=kota_sel)

            if result.empty:
                st.error("Tidak ada data untuk filter yang dipilih.")
            else:
                top = result.head(top_n)
                st.success(
                    f"✅ Ditemukan {len(result)} rumah yang sesuai dengan preferensi Anda."
                )

                # Metric summary
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🏆 Skor Tertinggi", f"{top['skor_saw'].iloc[0]:.4f}")
                c2.metric("💰 Harga Terbaik", f"Rp {top['harga'].iloc[0]/1e9:.2f} M")
                c3.metric("📐 Luas Bangunan", f"{top['luas_bangunan'].iloc[0]:.0f} m²")
                c4.metric("📍 Kota", top['kota'].iloc[0])

                st.markdown(f"#### 🏅 Top {top_n} Rekomendasi Rumah")


                display_cols = ["ranking", "kota", "harga", "luas_bangunan",
                                "luas_tanah", "kamar_tidur", "kamar_mandi",
                                "garasi", "skor_saw"]

                # Format harga jadi Rp
                top_display = top[display_cols].copy()
                top_display["harga"] = top_display["harga"].apply(
                    lambda x: f"Rp {x/1e9:.3f} M")
                

                st.dataframe(
                    top_display.rename(columns={
                        "ranking": "Rank", "kota": "Kota",
                        "harga": "Harga", "luas_bangunan": "Luas Bgn (m²)",
                        "luas_tanah": "Luas Tanah (m²)",
                        "kamar_tidur": "KT", "kamar_mandi": "KM",
                        "garasi": "Garasi", "skor_saw": "Skor SAW",
                    }),
                    use_container_width=True, hide_index=True,
                )

                # Download CSV
                csv = result.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Hasil Lengkap (CSV)",
                    data=csv, file_name="hasil_saw_hoomly.csv", mime="text/csv"
                )

                # Tabel normalisasi (expander)
                with st.expander("🔎 Lihat Detail Normalisasi SAW (Top 10)"):
                    from saw import normalize_matrix
                    norm_top = normalize_matrix(
                        result.head(10)[list(CRITERIA.keys())], CRITERIA
                    ).round(4)
                    norm_top.insert(0, "Kota", result.head(10)["kota"].values)
                    st.dataframe(norm_top, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────────────────
# TAB 2 – VISUALISASI
# ────────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### Jalankan rekomendasi dulu untuk melihat visualisasi lengkap.")

    # Distribusi harga per kota (selalu tampil)
    st.markdown("##### 📦 Distribusi Harga per Kota (seluruh dataset)")
    fig_box = px.box(
        df[df["kota"].isin(kota_sel)],
        x="kota", y="harga", color="kota",
        labels={"harga": "Harga (Rp)", "kota": "Kota"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_box.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_box, use_container_width=True)

    if run_btn and not result.empty:
        col_a, col_b = st.columns(2)

        # Bar chart skor SAW
        with col_a:
            st.markdown("##### 🏆 Skor SAW Top 15")
            top15 = result.head(15).copy()
            top15["label"] = top15["kota"] + " | Rp " + (top15["harga"]/1e9).round(2).astype(str) + "M"
            fig_bar = px.bar(
                top15, x="skor_saw", y="label", orientation="h",
                color="skor_saw", color_continuous_scale="Blues",
                labels={"skor_saw": "Skor SAW", "label": ""},
            )
            fig_bar.update_layout(height=420, yaxis={"autorange": "reversed"},
                                  coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        # Scatter harga vs luas bangunan
        with col_b:
            st.markdown("##### 💡 Harga vs Luas Bangunan (Top 50)")
            top50 = result.head(50)
            fig_sc = px.scatter(
                top50, x="luas_bangunan", y="harga",
                color="kota", size="skor_saw", hover_data=["kamar_tidur","kamar_mandi","garasi"],
                labels={"luas_bangunan": "Luas Bangunan (m²)", "harga": "Harga (Rp)"},
                color_discrete_sequence=px.colors.qualitative.Set1,
            )
            fig_sc.update_layout(height=420)
            st.plotly_chart(fig_sc, use_container_width=True)

        # Radar chart bobot
        st.markdown("##### 🕸️ Radar Chart Bobot Kriteria")
        cats = ["Harga", "Luas Bangunan", "Luas Tanah", "Kamar Tidur", "Kamar Mandi", "Garasi"]
        vals = [w_harga, w_lb, w_lt, w_kt, w_km, w_garasi]
        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", line_color="#1a3c5e", fillcolor="rgba(26,60,94,0.2)",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 50])),
            height=380,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ────────────────────────────────────────────────────────────
# TAB 3 – DATASET
# ────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f"**Dataset:** {len(df):,} baris · 7 kolom")
    st.markdown("Sumber: [Kaggle – Daftar Harga Rumah Jabodetabek](https://www.kaggle.com/datasets/nafisbarizki/daftar-harga-rumah-jabodetabek)")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("**Statistik Deskriptif**")
        desc = df.drop(columns=["kota"]).describe().round(2)
        st.dataframe(desc, use_container_width=True)
    with col_s2:
        st.markdown("**Jumlah Data per Kota**")
        kota_count = df["kota"].value_counts().reset_index()
        kota_count.columns = ["Kota", "Jumlah"]
        fig_pie = px.pie(kota_count, names="Kota", values="Jumlah",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("**Preview Data**")
    st.dataframe(df.head(50), use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(
    "<center><small>Hoomly © 2026 · Universitas Brawijaya · Fakultas Ilmu Komputer</small></center>",
    unsafe_allow_html=True,
)
