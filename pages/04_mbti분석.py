
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="국가별 MBTI 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 국가별 MBTI 비율 분석")
st.write("국가를 선택하면 MBTI 16개 유형의 비율을 확인할 수 있습니다.")

# CSV 파일은 pages 폴더의 상위 폴더에 있음
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "countriesMBTI_16types.csv"

MBTI_TYPES = [
    "INFJ", "ISFJ", "INTP", "ISFP",
    "ENTP", "INFP", "ENTJ", "ISTP",
    "INTJ", "ESFP", "ESTJ", "ENFP",
    "ESTP", "ISTJ", "ENFJ", "ESFJ"
]


@st.cache_data
def load_data():
    data = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    required = ["Country"] + MBTI_TYPES
    missing = [c for c in required if c not in data.columns]

    if missing:
        raise ValueError(f"CSV에 없는 열: {missing}")

    for col in MBTI_TYPES:
        data[col] = pd.to_numeric(data[col], errors="raise")

    return data


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일을 읽을 수 없습니다: {e}")
    st.stop()

# 국가 선택
countries = sorted(df["Country"].dropna().unique())

default_index = (
    list(countries).index("South Korea")
    if "South Korea" in countries
    else 0
)

country = st.selectbox(
    "🌐 국가를 선택하세요",
    countries,
    index=default_index
)

# 선택한 국가의 MBTI 데이터
selected = df[df["Country"] == country].iloc[0]

mbti_data = selected[MBTI_TYPES].sort_values(
    ascending=False
)

# 비율을 백분율로 변환
percentages = mbti_data * 100

# 색상 설정
colors = []

for i in range(len(percentages)):
    if i == 0:
        colors.append("#E53935")
    else:
        ratio = (i - 1) / 14

        start = (25, 76, 190)
        end = (195, 220, 250)

        r = round(start[0] + (end[0] - start[0]) * ratio)
        g = round(start[1] + (end[1] - start[1]) * ratio)
        b = round(start[2] + (end[2] - start[2]) * ratio)

        colors.append(f"rgb({r},{g},{b})")

# 상단 정보
col1, col2, col3 = st.columns(3)

col1.metric("선택 국가", country)
col2.metric("가장 높은 MBTI", percentages.index[0])
col3.metric("1위 비율", f"{percentages.iloc[0]:.2f}%")

st.divider()

# 막대그래프
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=percentages.index.tolist(),
        y=percentages.tolist(),
        marker_color=colors,
        text=[f"{v:.2f}%" for v in percentages],
        textposition="outside",
        hovertemplate=(
            "MBTI: %{x}<br>"
            "비율: %{y:.2f}%"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    title=f"📊 {country}의 MBTI 비율",
    xaxis_title="MBTI 유형",
    yaxis_title="비율 (%)",
    yaxis=dict(
        range=[0, max(percentages) * 1.2]
    ),
    height=550,
    showlegend=False,
    margin=dict(t=70, b=50, l=30, r=20)
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "🔴 1위: 빨간색 | "
    "🔵 2~16위: 진한 파란색에서 연한 파란색"
)

# 순위표
st.subheader("🏆 MBTI 순위")

result = pd.DataFrame({
    "순위": range(1, 17),
    "MBTI": percentages.index,
    "비율 (%)": percentages.round(2).values
})

st.dataframe(
    result,
    hide_index=True,
    use_container_width=True
)

st.info(
    "이 데이터는 조사 시기와 표본 크기가 확인되지 않아 "
    "국가 전체 인구의 실제 MBTI 분포로 단정할 수 없습니다."
)
