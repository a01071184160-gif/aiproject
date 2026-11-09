
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="세계 MBTI 분석",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 세계 MBTI 데이터 분석")
st.write("국가별 MBTI 비율과 MBTI 유형별 국가 순위를 분석해 보세요.")

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

    data["Country"] = data["Country"].astype(str).str.strip()

    for col in MBTI_TYPES:
        data[col] = pd.to_numeric(data[col], errors="raise")

    return data


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일을 읽을 수 없습니다: {e}")
    st.stop()


# 분석 메뉴
menu = st.radio(
    "📊 분석 방법을 선택하세요",
    ["🌍 국가별 MBTI 분석", "🏆 MBTI별 국가 순위"],
    horizontal=True
)

st.divider()


# ======================================
# 1. 국가별 MBTI 분석
# ======================================
if menu == "🌍 국가별 MBTI 분석":

    st.subheader("🌍 국가별 MBTI 비율")

    countries = sorted(df["Country"].dropna().unique())

    default_index = (
        list(countries).index("South Korea")
        if "South Korea" in countries
        else 0
    )

    country = st.selectbox(
        "분석할 국가를 선택하세요",
        countries,
        index=default_index
    )

    selected = df[df["Country"] == country].iloc[0]

    mbti_data = selected[MBTI_TYPES].sort_values(
        ascending=False
    )

    percentages = mbti_data * 100

    # 1위 빨간색, 나머지 파란색 그라데이션
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

    col1, col2, col3 = st.columns(3)

    col1.metric("선택 국가", country)
    col2.metric("가장 높은 MBTI", percentages.index[0])
    col3.metric("1위 비율", f"{percentages.iloc[0]:.2f}%")

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

    st.subheader("🏅 MBTI 순위표")

    result = pd.DataFrame({
        "순위": range(1, len(percentages) + 1),
        "MBTI": percentages.index,
        "비율 (%)": percentages.round(2).values
    })

    st.dataframe(
        result,
        hide_index=True,
        use_container_width=True
    )


# ======================================
# 2. MBTI별 국가 순위
# ======================================
else:

    st.subheader("🏆 MBTI별 국가 순위")

    selected_mbti = st.selectbox(
        "분석할 MBTI 유형을 선택하세요",
        sorted(MBTI_TYPES)
    )

    # 선택한 MBTI를 기준으로 국가 정렬
    ranking = df[["Country", selected_mbti]].copy()

    ranking = ranking.sort_values(
        by=selected_mbti,
        ascending=False
    ).reset_index(drop=True)

    ranking["비율 (%)"] = ranking[selected_mbti] * 100
    ranking["순위"] = range(1, len(ranking) + 1)

    # 상단 통계
    col1, col2, col3 = st.columns(3)

    col1.metric("선택 MBTI", selected_mbti)
    col2.metric("1위 국가", ranking.iloc[0]["Country"])
    col3.metric(
        "1위 국가 비율",
        f"{ranking.iloc[0]['비율 (%)']:.2f}%"
    )

    st.write(
        f"총 {len(ranking)}개 국가를 "
        f"{selected_mbti} 비율이 높은 순서대로 정렬했습니다."
    )

    # 국가가 많으므로 표시 범위 선택
    display_option = st.radio(
        "그래프에 표시할 국가 수",
        ["TOP 10", "TOP 30", "전체 국가"],
        horizontal=True
    )

    if display_option == "TOP 10":
        chart_data = ranking.head(10).copy()
    elif display_option == "TOP 30":
        chart_data = ranking.head(30).copy()
    else:
        chart_data = ranking.copy()

    # 보라색 계열 그라데이션
    chart_colors = []

    for i in range(len(chart_data)):
        ratio = i / max(len(chart_data) - 1, 1)

        start = (100, 45, 190)
        end = (215, 195, 245)

        r = round(start[0] + (end[0] - start[0]) * ratio)
        g = round(start[1] + (end[1] - start[1]) * ratio)
        b = round(start[2] + (end[2] - start[2]) * ratio)

        chart_colors.append(f"rgb({r},{g},{b})")

    # 가로 막대그래프
    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=chart_data["비율 (%)"],
            y=chart_data["Country"],
            orientation="h",
            marker_color=chart_colors,
            text=[
                f"{v:.2f}%"
                for v in chart_data["비율 (%)"]
            ],
            textposition="outside",
            hovertemplate=(
                "국가: %{y}<br>"
                "비율: %{x:.2f}%"
                "<extra></extra>"
            )
        )
    )

    fig2.update_layout(
        title=f"🌎 {selected_mbti} 비율 국가별 순위",
        xaxis_title="비율 (%)",
        yaxis_title="국가",
        yaxis=dict(
            autorange="reversed"
        ),
        xaxis=dict(
            range=[
                0,
                chart_data["비율 (%)"].max() * 1.2
            ]
        ),
        height=max(500, len(chart_data) * 28),
        showlegend=False,
        margin=dict(t=70, b=50, l=120, r=30)
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        "🟣 비율이 높은 국가부터 낮은 국가까지 "
        "보라색 그라데이션으로 표시합니다."
    )

    # 전체 순위표
    st.subheader(f"📋 {selected_mbti} 전체 국가 순위")

    result2 = ranking[
        ["순위", "Country", "비율 (%)"]
    ].copy()

    result2.columns = [
        "순위", "국가", "비율 (%)"
    ]

    result2["비율 (%)"] = (
        result2["비율 (%)"].round(2)
    )

    st.dataframe(
        result2,
        hide_index=True,
        use_container_width=True,
        height=500
    )


st.divider()

st.info(
    "참고: 원본 데이터의 조사 시기, 표본 수, "
    "조사 기관은 확인되지 않았습니다. "
    "따라서 국가 전체 인구의 실제 MBTI 분포로 "
    "단정할 수 없습니다."
)
