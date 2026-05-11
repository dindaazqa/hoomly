import pandas as pd
import numpy as np

# =========================================================
# KRITERIA & BOBOT
# =========================================================
CRITERIA = {
    "harga": {
        "type": "cost",
        "weight": 0.35
    },
    "luas_bangunan": {
        "type": "benefit",
        "weight": 0.25
    },
    "luas_tanah": {
        "type": "benefit",
        "weight": 0.15
    },
    "kamar_tidur": {
        "type": "benefit",
        "weight": 0.10
    },
    "kamar_mandi": {
        "type": "benefit",
        "weight": 0.10
    },
    "garasi": {
        "type": "benefit",
        "weight": 0.05
    }
}

# =========================================================
# NORMALISASI
# =========================================================
def normalize_matrix(df):

    norm = pd.DataFrame(index=df.index)

    for col, config in CRITERIA.items():

        if config["type"] == "benefit":

            max_val = df[col].max()

            norm[col] = (
                df[col] / max_val
                if max_val != 0 else 0
            )

        else:

            min_val = df[col].min()

            norm[col] = (
                min_val / df[col].replace(0, np.nan)
            )

            norm[col].fillna(0, inplace=True)

    return norm


# =========================================================
# HITUNG PREFERENSI
# =========================================================
def calculate_preference(norm_df):

    scores = pd.Series(
        0.0,
        index=norm_df.index
    )

    for col, config in CRITERIA.items():

        scores += (
            config["weight"] * norm_df[col]
        )

    return scores


# =========================================================
# RUN SAW
# =========================================================
def calculate_saw(df, kota_filter=None):

    result = df.copy()

    # FILTER KOTA
    if kota_filter:
        result = result[
            result["kota"].isin(kota_filter)
        ]

    # KALAU KOSONG
    if result.empty:
        return pd.DataFrame()

    # AMBIL KRITERIA
    criteria_cols = list(CRITERIA.keys())

    df_criteria = result[
        criteria_cols
    ].copy()

    # NORMALISASI
    norm_df = normalize_matrix(
        df_criteria
    )

    # HITUNG SKOR
    result["skor_saw"] = calculate_preference(
        norm_df
    )

    # SORTING
    result = result.sort_values(
        by="skor_saw",
        ascending=False
    ).reset_index(drop=True)

    # RANKING
    result["ranking"] = result.index + 1

    return result