
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온분석")
st.write("월을 선택하면 연도별 최고기온과 최저기온을 확인할 수 있습니다.")

# CSV 파일 경로
# py 파일은 pages 폴더, CSV는 상위 폴더에 위치
BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "temperature.csv"

@st.cache_data
def load_data():
    # 한글 CSV 인코딩 처리
    df = None

    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            df = pd.read_csv(CSV_PATH, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 파일의 인코딩을 확인할 수 없습니다.")

    # 열 이름 공백 제거
    df.columns = df.columns.str.strip()

    required = ["일시", "최고기온(℃)", "최저기온(℃)"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"필요한 열이 없습니다: {col}")

    # 원본 날짜 예시: Oct-07
    # 1907년부터 2026년까지의 데이터
    date_text = df["일시"].astype(str).str.strip()

    # 월 이름 추출
    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3,
        "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9,
        "Oct": 10, "Nov": 11, "Dec": 12
    }

    parts = date_text.str.extract(
        r"^([A-Za-z]{3})-(\d{2})$"
    )

    df["월"] = parts[0].str.title().map(month_map)

    # 연도 변환
    # 07~99 -> 1907~1999
    # 00~26 -> 2000~2026
    yy = pd.to_numeric(parts[1], errors="coerce")

    df["연도"] = yy.apply(
        lambda x: (
            2000 + int(x) if x <= 26
            else 1900 + int(x)
        ) if pd.notna(x) else None
    )

    # 기온을 숫자로 변환
    for col in ["최고기온(℃)", "최저기온(℃)"]:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    # 유효한 날짜만 사용
    df = df.dropna(subset=["연도", "월"])

    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)

    return df


try:
    df = load_data()

except Exception as e:
    st.error(f"데이터를 불러올 수 없습니다: {e}")
    st.stop()


# 월 선택
month_names = {
    1: "1월", 2: "2월", 3: "3월",
    4: "4월", 5: "5월", 6: "6월",
    7: "7월", 8: "8월", 9: "9월",
    10: "10월", 11: "11월", 12: "12월"
}

selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요",
    options=list(month_names.keys()),
    format_func=lambda x: month_names[x]
)

# 선택한 월의 데이터
filtered = df[df["월"] == selected_month].copy()

filtered = filtered.sort_values("연도")

# 결측값 제거
filtered = filtered.dropna(
    subset=["최고기온(℃)", "최저기온(℃)"]
)

if filtered.empty:
    st.warning("선택한 월에 분석할 데이터가 없습니다.")
    st.stop()

# 같은 연도와 월이 중복된 경우 정리
filtered = filtered.groupby(
    "연도", as_index=False
).agg({
    "최고기온(℃)": "max",
    "최저기온(℃)": "min"
})

# 그래프 생성
fig = go.Figure()

# 최고기온 - 핫핑크
fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=filtered["최고기온(℃)"],
        mode="lines+markers",
        name="최고기온",
        line=dict(
            color="#FF1493",
            width=3
        ),
        marker=dict(size=6),
        connectgaps=False,
        hovertemplate=(
            "연도: %{x}년<br>"
            "최고기온: %{y:.1f}℃"
            "<extra></extra>"
        )
    )
)

# 최저기온 - 하늘색
fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=filtered["최저기온(℃)"],
        mode="lines+markers",
        name="최저기온",
        line=dict(
            color="#87CEEB",
            width=3
        ),
        marker=dict(size=6),
        connectgaps=False,
        hovertemplate=(
            "연도: %{x}년<br>"
            "최저기온: %{y:.1f}℃"
            "<extra></extra>"
        )
    )
)

# 그래프 디자인
fig.update_layout(
    title=dict(
        text="월별 기온분석",
        x=0.5,
        font=dict(size=24)
    ),
    xaxis_title="연도",
    yaxis_title="온도 (℃)",
    font=dict(
        family="Arial, Malgun Gothic, sans-serif",
        size=14
    ),
    legend=dict(
        title="범례",
        orientation="h",
        x=0.5,
        xanchor="center",
        y=1.08,
        yanchor="bottom"
    ),
    hovermode="x unified",
    template="plotly_white",
    height=550,
    margin=dict(t=120)
)

fig.update_xaxes(
    type="linear",
    tickformat="d",
    showgrid=True
)

fig.update_yaxes(
    ticksuffix="℃",
    showgrid=True,
    zeroline=True
)

# 그래프 출력
st.plotly_chart(
    fig,
    use_container_width=True
)

# 통계 정보
st.subheader(f"📊 {selected_month}월 기온 통계")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🌸 가장 높은 최고기온",
        f"{filtered['최고기온(℃)'].max():.1f}℃"
    )

with col2:
    st.metric(
        "❄️ 가장 낮은 최저기온",
        f"{filtered['최저기온(℃)'].min():.1f}℃"
    )

with col3:
    st.metric(
        "📅 분석 연도 수",
        f"{len(filtered)}개년"
    )

# 상세 데이터
with st.expander("📋 연도별 상세 데이터 보기"):
    st.dataframe(
        filtered.rename(columns={
            "연도": "연도",
            "최고기온(℃)": "최고기온 (℃)",
            "최저기온(℃)": "최저기온 (℃)"
        }),
        use_container_width=True,
        hide_index=True
    )

st.caption("자료 출처: temperature.csv")
