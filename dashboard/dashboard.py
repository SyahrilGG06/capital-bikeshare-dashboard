from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Jam sewa | Capital Bikeshare", layout="wide")


@st.cache_data
def load_hours():
    path = Path(__file__).resolve().parents[1] / "data" / "hour.csv"
    return pd.read_csv(path, usecols=["dteday", "hr", "workingday", "cnt"], parse_dates=["dteday"])


st.title("Jam sewa Capital Bikeshare")
st.caption("Washington D.C. · Penyewaan sepeda per jam · 2011–2012")
year = st.sidebar.selectbox("Tahun pengamatan", [2012, 2011])
hours = load_hours()
selected = hours.loc[hours.dteday.dt.year.eq(year)]
profile = selected.groupby(["workingday", "hr"]).cnt.agg(["mean", "count"]).reset_index()
profile.columns = ["jenis", "jam", "rata_rata", "hari"]
low, high = profile.rata_rata.quantile([0.25, 0.75])
profile["kelas"] = pd.cut(profile.rata_rata, [-float("inf"), low, high, float("inf")],
                          labels=["Rendah", "Sedang", "Tinggi"])
work = profile.loc[profile.jenis.eq(1)].copy()
maintenance = profile.loc[profile.jenis.eq(0) & profile.jam.between(8, 17)].copy()
peak = work.nlargest(3, "rata_rata")
quiet = maintenance.nsmallest(1, "rata_rata")


def show_hours(frame, highlights, color):
    frame = frame.assign(fokus=frame.jam.isin(highlights.jam))
    chart = alt.Chart(frame).mark_bar().encode(
        x=alt.X("jam:O", title="Jam mulai (waktu setempat)", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("rata_rata:Q", title="Rata-rata penyewaan per jam", scale=alt.Scale(zero=True)),
        color=alt.condition(alt.datum.fokus, alt.value(color), alt.value("#aabdc7")),
        tooltip=[alt.Tooltip("jam:O", title="Pukul"), alt.Tooltip("rata_rata:Q", title="Rata-rata", format=".1f"),
                 alt.Tooltip("hari:Q", title="Hari teramati"), alt.Tooltip("kelas:N", title="Kelas permintaan")],
    ).properties(height=275)
    st.altair_chart(chart, use_container_width=True)


def number(value):
    return f"{value:.1f}".replace(".", ",")


st.header("Kapan armada perlu siap?")
st.write(f"Tiga jam tersibuk pada hari kerja selama {year}, diurutkan menurut rata-rata penyewaan.")
for column, row in zip(st.columns(3), peak.itertuples()):
    column.metric(f"Pukul {row.jam:02d}.00", number(row.rata_rata))
    column.caption(f"penyewaan per jam · {row.hari} hari teramati")
show_hours(work, peak, "#07695f")
st.header("Kapan menjadwalkan perawatan?")
candidate = quiet.iloc[0]
st.write(f"Pada hari nonkerja, pukul **{int(candidate.jam):02d}.00** memiliki permintaan terendah "
         f"dalam rentang 08.00–17.00, dengan rata-rata **{number(candidate.rata_rata)} penyewaan** "
         f"dari {int(candidate.hari)} hari. Pertimbangkan jam ini untuk uji perawatan bergilir.")
show_hours(maintenance, quiet, "#a64b18")
with st.expander("Lihat kelas permintaan untuk semua jam"):
    st.write(f"Pengelompokan memakai kuartil rata-rata dari 48 pasangan jenis hari dan jam pada {year}. "
             f"Batas rendah–sedang adalah {number(low)} dan batas sedang–tinggi adalah {number(high)} penyewaan.")
    table = profile.assign(jenis=profile.jenis.map({0: "Nonkerja", 1: "Kerja"}))
    st.dataframe(table.rename(columns={"jenis":"Jenis hari","jam":"Jam","rata_rata":"Rata-rata",
                                       "hari":"Hari teramati","kelas":"Kelas"}).round(1),
                 hide_index=True, use_container_width=True)
st.caption("Jam tanpa catatan dikeluarkan dari rata-rata. Hari nonkerja mencakup akhir pekan dan hari libur. "
           "Angka mewakili penyewaan seluruh jaringan. Sumber: Bike Sharing Dataset, Fanaee-T dan Gama.")
