
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import streamlit as st

st.set_page_config(
    page_title="서울 연령별 인구 분석",
    page_icon="📈",
    layout="wide"
)

# CSV는 pages 폴더의 상위 폴더에 위치
CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "population.csv"
)


@st.cache_data
def load_data(path, file_mtime):
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
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


def set_font():
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
st.caption("행정구역, 연도, 성별을 선택하세요.")

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


# 연령 구간
ages = [
    f"{a}~{a+9}세"
    for a in range(0, 100, 10)
] + ["100세 이상"]


# 실제 CSV 열 이름에서 데이터 자동 인식
column_map = {}

for column in df.columns:
    parts = column.split("_")

    if len(parts) not in (3, 4):
        continue

    year_text = parts[0].strip()

    if not (
        year_text.endswith("년")
        and year_text[:-1].isdigit()
    ):
        continue

    year = int(year_text[:-1])

    if len(parts) == 3 and parts[1] == "거주자":
        sex = "전체"
        age = parts[2].strip()

    elif (
        len(parts) == 4
        and parts[2] == "거주자"
        and parts[1] in ("남", "여")
    ):
        sex = "남성" if parts[1] == "남" else "여성"
        age = parts[3].strip()

    else:
        continue

    if age in ages:
        column_map[(year, sex, age)] = column


# 연도와 행정구역
years = sorted({
    key[0] for key in column_map
})

areas = [
    area
    for area in df["행정구역"].unique().tolist()
    if area
]

if not years or not areas:
    st.error(
        "데이터를 분석할 수 없습니다. "
        "population.csv 파일을 확인하세요."
    )
    st.stop()


# 선택 메뉴
c1, c2, c3 = st.columns(3)

with c1:
    area = st.selectbox(
        "🏙️ 행정구역",
        areas
    )

with c2:
    year = st.selectbox(
        "📅 연도",
        years,
        index=len(years) - 1
    )

with c3:
    sex = st.selectbox(
        "👥 성별",
        ["전체", "남성", "여성"]
    )


# 선택한 행정구역
selected = df.loc[
    df["행정구역"] == area
]

if selected.empty:
    st.error("행정구역 데이터를 찾을 수 없습니다.")
    st.stop()

row = selected.iloc[0]

records = []

for age in ages:
    column = column_map.get((year, sex, age))

    if column is None:
        st.error(
            f"{year}년 {sex} {age} "
            "데이터 열이 없습니다."
        )
        st.stop()

    value = pd.to_numeric(
        str(row[column])
        .replace(",", "")
        .strip(),
        errors="coerce"
    )

    if pd.isna(value):
        st.error(f"{age} 인구수가 숫자가 아닙니다.")
        st.stop()

    records.append({
        "연령": age,
        "인구수": int(value)
    })


result = pd.DataFrame(records)

peak = result.loc[
    result["인구수"].idxmax()
]


# 인구 요약
m1, m2 = st.columns(2)

m1.metric(
    "연령별 인구 합계",
    f"{result['인구수'].sum():,}명"
)

m2.metric(
    "인구가 가장 많은 연령대",
    f"{peak['연령']} ({peak['인구수']:,}명)"
)


# 그래프
set_font()

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
    f"{area} {year}년 {sex} 연령별 인구"
)

ax.set_xlabel("나이 (연령 구간)")
ax.set_ylabel("인구수 (명)")

# 세로축 1,000명 간격
ax.set_ylim(bottom=0)

ax.yaxis.set_major_locator(
    ticker.MultipleLocator(1000)
)

ax.yaxis.set_major_formatter(
    ticker.StrMethodFormatter("{x:,.0f}")
)

# 구분선
ax.grid(
    axis="y",
    which="major",
    color="#cccccc",
    linewidth=0.6
)

ax.tick_params(
    axis="x",
    rotation=35
)

fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# 상세 데이터
with st.expander("📋 상세 데이터"):
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
        file_name=f"{area}_{year}_{sex}_인구.csv",
        mime="text/csv"
    )
