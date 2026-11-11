
from pathlib import Path
import re

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker

st.set_page_config(
    page_title="서울 연령별 인구 분석",
    page_icon="📈",
    layout="wide"
)

# pages 폴더의 상위 폴더에서 CSV 읽기
CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "population.csv"
)

AGES = [
    f"{i}~{i+9}세"
    for i in range(0, 100, 10)
] + ["100세 이상"]


@st.cache_data(show_spinner=False)
def load_data(path, modified_time):
    for encoding in ("cp949", "utf-8-sig", "euc-kr"):
        try:
            df = pd.read_csv(
                path,
                encoding=encoding,
                dtype=str
            )
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("CSV 인코딩을 읽을 수 없습니다.")

    df.columns = [
        str(c).replace("\ufeff", "").strip()
        for c in df.columns
    ]

    if "행정구역" not in df.columns:
        raise ValueError("행정구역 열이 없습니다.")

    df["행정구역"] = (
        df["행정구역"]
        .fillna("")
        .astype(str)
        .str.replace(
            r"\s*\(\d+\)\s*$",
            "",
            regex=True
        )
        .str.strip()
    )

    return df


def set_korean_font():
    paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    ]

    for path in paths:
        if Path(path).is_file():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = (
                font_manager.FontProperties(
                    fname=path
                ).get_name()
            )
            break

    plt.rcParams["axes.unicode_minus"] = False


st.title("📈 서울특별시 연령별 인구 분석")
st.write("행정구역, 연도, 성별을 선택하세요.")

if not CSV_PATH.is_file():
    st.error(
        "population.csv 파일이 없습니다. "
        "pages 폴더의 상위 폴더에 넣어주세요."
    )
    st.stop()

try:
    df = load_data(
        str(CSV_PATH),
        CSV_PATH.stat().st_mtime_ns
    )
except Exception as e:
    st.error(f"CSV 읽기 오류: {e}")
    st.stop()


# 실제 CSV의 총인구수 열에서 연도 추출
pattern = re.compile(
    r"^(\d{4})년_거주자_총인구수$"
)

years = sorted({
    int(match.group(1))
    for col in df.columns
    if (match := pattern.fullmatch(col))
})

areas = (
    df["행정구역"]
    .loc[df["행정구역"].ne("")]
    .drop_duplicates()
    .tolist()
)

if not years or not areas:
    st.error(
        "연도 또는 행정구역을 확인할 수 없습니다. "
        "GitHub의 CSV 파일을 확인하세요."
    )
    st.stop()


# 선택 메뉴
c1, c2, c3 = st.columns(3)

with c1:
    area = st.selectbox("🏙️ 행정구역", areas)

with c2:
    year = st.selectbox(
        "📅 연도",
        years,
        index=len(years) - 1
    )

with c3:
    gender = st.selectbox(
        "👥 성별",
        ["전체", "남성", "여성"]
    )


# 성별에 따른 열 이름
prefix = {
    "전체": f"{year}년_거주자_",
    "남성": f"{year}년_남_거주자_",
    "여성": f"{year}년_여_거주자_"
}[gender]

needed = [prefix + age for age in AGES]

missing = [
    col for col in needed
    if col not in df.columns
]

if missing:
    st.error(
        "연령별 데이터 열이 없습니다: "
        + ", ".join(missing)
    )
    st.stop()


# 선택한 행정구역 데이터
selected = df.loc[
    df["행정구역"].eq(area)
]

if selected.empty:
    st.error("행정구역 데이터를 찾지 못했습니다.")
    st.stop()

row = selected.iloc[0]

values = pd.to_numeric(
    row[needed]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.strip(),
    errors="coerce"
)

if values.isna().any():
    st.error("인구수에 잘못된 값이 있습니다.")
    st.stop()

result = pd.DataFrame({
    "연령": AGES,
    "인구수": values.astype(int).to_numpy()
})

peak = result.loc[result["인구수"].idxmax()]


# 인구 요약
m1, m2 = st.columns(2)

m1.metric(
    "연령별 인구 합계",
    f"{result['인구수'].sum():,}명"
)

m2.metric(
    "가장 인구가 많은 연령대",
    f"{peak['연령']} ({peak['인구수']:,}명)"
)


# 검정색 꺾은선 그래프
set_korean_font()

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    result["연령"],
    result["인구수"],
    color="black",
    marker="o",
    linewidth=2,
    markersize=5
)

ax.set_title(
    f"{area} {year}년 {gender} 연령별 인구"
)

ax.set_xlabel("나이 (연령 구간)")
ax.set_ylabel("인구수 (명)")
ax.set_ylim(bottom=0)

maximum = int(result["인구수"].max())

# 1,000명 간격 가로 구분선
if maximum <= 40000:
    ax.yaxis.set_major_locator(
        ticker.MultipleLocator(1000)
    )
    ax.grid(
        axis="y",
        which="major",
        color="#cccccc",
        linewidth=0.6
    )
else:
    # 인구가 많은 경우 숫자 눈금 간격 조정
    step = max(
        1000,
        ((maximum // 12 + 999) // 1000) * 1000
    )

    ax.yaxis.set_major_locator(
        ticker.MultipleLocator(step)
    )

    ax.yaxis.set_minor_locator(
        ticker.MultipleLocator(1000)
    )

    ax.grid(
        axis="y",
        which="major",
        color="#bbbbbb",
        linewidth=0.6
    )

    ax.grid(
        axis="y",
        which="minor",
        color="#e7e7e7",
        linewidth=0.35
    )

ax.yaxis.set_major_formatter(
    ticker.StrMethodFormatter("{x:,.0f}")
)

ax.tick_params(axis="x", rotation=35)
ax.set_axisbelow(True)

fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# 상세 데이터
with st.expander("📋 상세 데이터 및 다운로드"):
    st.dataframe(
        result,
        hide_index=True,
        use_container_width=True
    )

    st.download_button(
        "CSV 다운로드",
        data=result.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"{area}_{year}_{gender}_인구.csv",
        mime="text/csv"
    )
