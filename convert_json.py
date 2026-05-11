import pandas as pd

# baca CSV
df = pd.read_csv("rumah_clean.csv")

# convert ke JSON
df.to_json(
    "rumah_clean.json",
    orient="records",
    indent=4
)

print("JSON berhasil dibuat!")