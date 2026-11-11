
from pathlib import Path
import re

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import streamlit as st

st.set_page_config(
    page_title="서울 인구 분석",
    page_icon="📈",
    layout="wide"
)

# CSV는 pages 폴더의 상위 폴더에 있음
CSV_PATH = Path(__file__).resolve().parent.parent / "population.csv"


@st.cache_data
def load_data():
    if not CSV_PATH.exists():
        st.error(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}")
        st.stop()

    # 한글 인코딩 자동 처리
    df = None
    for encoding in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(
                CSV_PATH,
                encoding=encoding,
                dtype=str
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        st.error("CSV 인코딩을 확인할 수 없습니다.")
        st.stop()

    df.columns = df.columns.str.strip()

    # 행정구역 이름에서 행정코드 제거
    df["행정구역"] = (
        df["행정구역"]
        .str.replace(r"\s*\(\d+\)\s*$", "", regex=True)
        .str.strip()
    )

    # 쉼표 제거 후 숫자 변환
    for col in df.columns:
        if col != "행정구역":
            df[col] = pd.to_numeric(
                df[col].str.replace(",", "", regex=False),
                errors="coerce"
            )

    return df


# 한글 폰트 설정
def set_korean_font():
    paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    ]

    for path in paths:
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            font_name = font_manager.FontProperties(
                fname=path
            ).get_name()
            plt.rcParams["font.family"] = font_name
            break

    plt.rcParams["axes.unicode_minus"] = False


st.title("📈 서울특별시 연령별 인구 분석")
st.write("행정구역, 연도, 성별을 선택해 인구를 분석하세요.")

df = load_data()
set_korean_font()

# 선택 가능한 행정구역 및 연도
areas = df["행정구역"].dropna().unique().tolist()

years = sorted({
    int(match.group(1))
    for col in df.columns
    if (match := re.match(
        r"^(\d{4})년_거주자_총인구수$", col
    ))
})

# 선택 메뉴
col1, col2, col3 = st.columns(3)

with col1:
    area = st.selectbox("🏙️ 행정구역", areas)

with col2:
    year = st.selectbox(
        "📅 연도",
        years,
        index=len(years) - 1
    )

with col3:
    gender = st.selectbox(
        "👥 성별",
        ["전체", "남성", "여성"]
    )

# 성별에 따른 데이터 열 선택
prefix = {
    "전체": f"{year}년_거주자_",
    "남성": f"{year}년_남_거주자_",
    "여성": f"{year}년_여_거주자_"
}[gender]

# 연령 구간
ages = [
    f"{i}~{i+9}세"
    for i in range(0, 100, 10)
] + ["100세 이상"]

columns = [prefix + age for age in ages]

# 데이터 확인
missing = [c for c in columns if c not in df.columns]

if missing:
    st.error("필요한 연령별 데이터가 없습니다.")
    st.stop()

selected = df[df["행정구역"] == area]

if selected.empty:
    st.error("선택한 행정구역의 데이터가 없습니다.")
    st.stop()

values = selected.iloc[0][columns]

data = pd.DataFrame({
    "연령": ages,
    "인구수": values.to_numpy(dtype=float)
}).dropna()

if data.empty:
    st.warning("표시할 인구 데이터가 없습니다.")
    st.stop()

# 인구 요약
total = int(data["인구수"].sum())
peak = data.loc[data["인구수"].idxmax()]

m1, m2 = st.columns(2)

with m1:
    st.metric("총인구수", f"{total:,}명")

with m2:
    st.metric(
        "인구가 가장 많은 연령대",
        f"{peak['연령']} ({int(peak['인구수']):,}명)"
    )

# 검정색 꺾은선 그래프
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    data["연령"],
    data["인구수"],
    color="black",
    marker="o",
    linewidth=2,
    markersize=5
)

ax.set_title(
    f"{area} {year}년 {gender} 연령별 인구",
    fontsize=16
)

ax.set_xlabel("나이 (연령 구간)", fontsize=12)
ax.set_ylabel("인구수 (명)", fontsize=12)

# 세로축 1,000명 간격
ax.set_ylim(bottom=0)
ax.yaxis.set_major_locator(
    ticker.MultipleLocator(1000)
)

ax.yaxis.set_major_formatter(
    ticker.StrMethodFormatter("{x:,.0f}")
)

# 가로 구분선
ax.grid(
    axis="y",
    which="major",
    color="#cccccc",
    linestyle="-",
    linewidth=0.6
)

ax.set_axisbelow(True)
ax.tick_params(axis="x", labelrotation=35)

fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

# 상세 데이터
with st.expander("📋 연령별 인구 데이터 보기"):
    table = data.copy()
    table["인구수"] = table["인구수"].astype(int)

    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True
    )

    st.download_button(
        "CSV 다운로드",
        data=table.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"{area}_{year}_{gender}_인구.csv",
        mime="text/csv"
    )
