
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="월별 기온분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온분석")
st.write(
    "1907년부터 2026년까지의 "
    "월별 최고기온과 최저기온을 분석합니다."
)

# =====================================
# 2. CSV 파일 경로
# =====================================
# Python 파일: pages 폴더
# CSV 파일: 상위 폴더

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "temperature.csv"


# =====================================
# 3. 데이터 불러오기
# =====================================
@st.cache_data
def load_data():

    df = None

    # 한글 인코딩 처리
    for encoding in [
        "cp949",
        "euc-kr",
        "utf-8-sig",
        "utf-8"
    ]:
        try:
            df = pd.read_csv(
                CSV_PATH,
                encoding=encoding
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 인코딩 오류")

    df.columns = df.columns.str.strip()

    required = [
        "일시",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in required:
        if col not in df.columns:
            raise ValueError(
                f"CSV에 {col} 열이 없습니다."
            )

    # =================================
    # 4. 날짜 처리
    # =================================
    # 원본 날짜 예시:
    # Oct-07 = 1907년 10월
    # Jan-08 = 1908년 1월
    # Jan-00 = 2000년 1월
    # Oct-26 = 2026년 10월

    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
    }

    parts = (
        df["일시"]
        .astype(str)
        .str.strip()
        .str.extract(r"^([A-Za-z]{3})-(\d{2})$")
    )

    df["월"] = (
        parts[0]
        .str.title()
        .map(month_map)
    )

    df["두자리연도"] = pd.to_numeric(
        parts[1],
        errors="coerce"
    )

    # 1907년부터 순서대로 연도 복원
    years = []
    century = 1900
    previous_year = None

    for value in df["두자리연도"]:

        if pd.isna(value):
            years.append(None)
            continue

        current_year = int(value)

        # 1999 -> 2000으로 넘어가는 경우
        if (
            previous_year is not None
            and previous_year == 99
            and current_year == 0
        ):
            century += 100

        full_year = century + current_year

        years.append(full_year)

        previous_year = current_year

    df["연도"] = years

    # 기온 숫자 변환
    for col in [
        "최고기온(℃)",
        "최저기온(℃)"
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # 유효한 날짜만 사용
    df = df.dropna(
        subset=["연도", "월"]
    )

    df["연도"] = df["연도"].astype(int)
    df["월"] = df["월"].astype(int)

    # 분석 기간 제한
    df = df[
        df["연도"].between(1907, 2026)
    ]

    return df


# 데이터 로드
try:
    df = load_data()

except Exception as e:
    st.error(
        f"데이터를 불러올 수 없습니다: {e}"
    )
    st.stop()


# =====================================
# 5. 월 선택
# =====================================
selected_month = st.selectbox(
    "📅 분석할 월을 선택하세요",
    options=list(range(1, 13)),
    format_func=lambda x: f"{x}월"
)

# 선택한 월의 데이터
filtered = df[
    df["월"] == selected_month
].copy()

# 같은 연도에 여러 값이 있을 경우
# 최고는 최댓값, 최저는 최솟값
filtered = (
    filtered
    .groupby("연도", as_index=False)
    .agg({
        "최고기온(℃)": "max",
        "최저기온(℃)": "min"
    })
)

# =====================================
# 6. 1907~2026년 전체 연도 생성
# =====================================
all_years = pd.DataFrame({
    "연도": list(range(1907, 2027))
})

# 데이터가 없는 연도도 축에 포함
filtered = pd.merge(
    all_years,
    filtered,
    on="연도",
    how="left"
)

filtered = filtered.sort_values("연도")


# =====================================
# 7. 꺾은선 그래프
# =====================================
fig = go.Figure()

# 최고기온: 핫핑크
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
        marker=dict(
            size=4,
            color="#FF1493"
        ),
        connectgaps=False,
        hovertemplate=(
            "연도: %{x}년<br>"
            "최고기온: %{y:.1f}℃"
            "<extra></extra>"
        )
    )
)

# 최저기온: 하늘색
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
        marker=dict(
            size=4,
            color="#87CEEB"
        ),
        connectgaps=False,
        hovertemplate=(
            "연도: %{x}년<br>"
            "최저기온: %{y:.1f}℃"
            "<extra></extra>"
        )
    )
)

# =====================================
# 8. 그래프 디자인
# =====================================
fig.update_layout(
    title=dict(
        text="월별 기온분석",
        x=0.5,
        xanchor="center",
        font=dict(size=25)
    ),

    xaxis_title="연도",
    yaxis_title="온도 (℃)",

    font=dict(
        family=(
            "Malgun Gothic, "
            "Apple SD Gothic Neo, "
            "Noto Sans CJK KR, "
            "sans-serif"
        ),
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

    template="plotly_white",
    hovermode="x unified",
    height=600,
    margin=dict(
        l=60,
        r=30,
        t=120,
        b=70
    ),

    # 확대 상태 초기화
    uirevision=f"month_{selected_month}"
)

# =====================================
# 9. 가로축 1907~2026 고정
# =====================================
fig.update_xaxes(
    type="linear",

    # 반드시 1907년부터 시작
    range=[1907, 2026],

    autorange=False,

    # 확대 및 이동 방지
    fixedrange=True,

    # 연도 눈금 직접 지정
    tickmode="array",

    tickvals=[
        1907,
        1910,
        1920,
        1930,
        1940,
        1950,
        1960,
        1970,
        1980,
        1990,
        2000,
        2010,
        2020,
        2026
    ],

    ticktext=[
        "1907",
        "1910",
        "1920",
        "1930",
        "1940",
        "1950",
        "1960",
        "1970",
        "1980",
        "1990",
        "2000",
        "2010",
        "2020",
        "2026"
    ],

    showgrid=True,
    gridcolor="#E5E5E5",
    zeroline=False
)

# 세로축
fig.update_yaxes(
    title="온도 (℃)",
    ticksuffix="℃",
    showgrid=True,
    gridcolor="#E5E5E5"
)

# 그래프 출력
st.plotly_chart(
    fig,
    use_container_width=True,
    key=f"temperature_chart_{selected_month}",
    config={
        "scrollZoom": False,
        "displaylogo": False
    }
)


# =====================================
# 10. 기온 통계
# =====================================
st.subheader(
    f"📊 {selected_month}월 기온 통계"
)

valid = filtered.dropna(
    subset=[
        "최고기온(℃)",
        "최저기온(℃)"
    ]
)

if not valid.empty:

    col1, col2, col3 = st.columns(3)

    max_temp = valid["최고기온(℃)"].max()
    min_temp = valid["최저기온(℃)"].min()

    with col1:
        st.metric(
            "🌸 최고기온",
            f"{max_temp:.1f}℃"
        )

    with col2:
        st.metric(
            "❄️ 최저기온",
            f"{min_temp:.1f}℃"
        )

    with col3:
        st.metric(
            "📅 분석 연도 수",
            f"{len(valid)}개년"
        )

else:
    st.warning(
        "선택한 월의 기온 데이터가 없습니다."
    )


# =====================================
# 11. 상세 데이터
# =====================================
with st.expander(
    "📋 연도별 상세 데이터 보기"
):

    display_df = valid.rename(
        columns={
            "최고기온(℃)": "최고기온 (℃)",
            "최저기온(℃)": "최저기온 (℃)"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =====================================
# 12. 안내
# =====================================
st.info(
    "그래프의 가로축은 1907년부터 "
    "2026년까지 고정되어 있습니다. "
    "관측값이 없는 연도는 선이 연결되지 않습니다."
)

st.caption(
    "자료 출처: temperature.csv"
)
