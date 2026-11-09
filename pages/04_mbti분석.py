from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="세계 국가별 MBTI 비율", page_icon="🌍", layout="wide")

MBTI_TYPES = [
    "INFJ", "ISFJ", "INTP", "ISFP", "ENTP", "INFP", "ENTJ", "ISTP",
    "INTJ", "ESFP", "ESTJ", "ENFP", "ESTP", "ISTJ", "ENFJ", "ESFJ",
]

@st.cache_data
def load_data():
    path = Path(__file__).resolve().parent / "countriesMBTI_16types.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")
    needed = ["Country", *MBTI_TYPES]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"CSV 파일에 필요한 열이 없습니다: {', '.join(missing)}")
    for col in MBTI_TYPES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def blue_gradient(count):
    """진한 파랑에서 연한 파랑으로 선형 보간한 색 목록."""
    start = (21, 83, 188)
    end = (199, 224, 250)
    colors = []
    for i in range(count):
        t = i / max(count - 1, 1)
        rgb = tuple(round(a + (b - a) * t) for a, b in zip(start, end))
        colors.append(f"rgb({rgb[0]},{rgb[1]},{rgb[2]})")
    return colors


st.title("🌍 세계 국가별 MBTI 비율 분석")
st.write("국가를 선택하면 16가지 MBTI 유형의 비율을 순위별로 확인할 수 있어요.")

try:
    df = load_data()
except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
    st.error(f"데이터 파일을 읽을 수 없습니다: {exc}")
    st.info("app.py와 countriesMBTI_16types.csv를 같은 폴더에 업로드해 주세요.")
    st.stop()

countries = sorted(df["Country"].dropna().astype(str).unique().tolist())
selected_country = st.selectbox("🌐 분석할 국가를 선택하세요", countries)
country_rows = df.loc[df["Country"] == selected_country, MBTI_TYPES]
if country_rows.empty:
    st.warning("선택한 국가의 데이터를 찾을 수 없습니다.")
    st.stop()

ranked = (country_rows.iloc[0].dropna().mul(100).sort_values(ascending=False))
if ranked.empty:
    st.warning("이 국가에는 표시할 MBTI 비율이 없습니다.")
    st.stop()

first_type, first_percent = ranked.index[0], ranked.iloc[0]
col1, col2, col3 = st.columns(3)
col1.metric("🥇 가장 높은 MBTI", first_type)
col2.metric("📊 1위 비율", f"{first_percent:.2f}%")
col3.metric("🔎 분석 유형 수", f"{len(ranked)}개")

colors = ["#F04444"] + blue_gradient(max(len(ranked) - 1, 0))
fig = go.Figure(
    go.Bar(
        x=ranked.values,
        y=ranked.index.tolist(),
        orientation="h",
        marker=dict(color=colors),
        text=[f"{v:.2f}%" for v in ranked.values],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>비율: %{x:.2f}%<extra></extra>",
    )
)
fig.update_layout(
    title=f"{selected_country} · MBTI 유형별 비율 순위",
    xaxis_title="비율 (%)",
    yaxis_title="MBTI 유형",
    yaxis=dict(autorange="reversed"),
    xaxis=dict(range=[0, max(ranked.values) * 1.22]),
    height=660,
    margin=dict(l=20, r=35, t=65, b=30),
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
)
fig.update_xaxes(showgrid=True, gridcolor="#E7ECF2", zeroline=False)
fig.update_yaxes(showgrid=False)
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 MBTI 유형별 상세 데이터"):
    detail = pd.DataFrame({
        "순위": range(1, len(ranked) + 1),
        "MBTI": ranked.index,
        "비율 (%)": ranked.values.round(2),
    })
    st.dataframe(detail, hide_index=True, use_container_width=True)

sum_percent = ranked.sum()
if abs(sum_percent - 100) > 0.1:
    st.caption(f"참고: 선택한 국가의 원본 비율 합계는 {sum_percent:.2f}%로, 정확히 100%가 아닙니다. 원본 값을 임의로 보정하지 않았습니다.")
st.caption("출처: 제공된 countriesMBTI_16types.csv · 조사 시기와 표본의 대표성은 확인되지 않았습니다.")
