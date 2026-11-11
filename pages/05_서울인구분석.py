
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import streamlit as st

st.set_page_config(
    page_title="서울 연령별 인구 분석",
    page_icon="📈",
    layout="wide"
)

# CSV 파일은 pages 폴더의 상위 폴더에 위치
CSV_PATH = Path(__file__).resolve().parent.parent / "population.csv"


@st.cache_data(show_spinner=False)
def load_csv(path, modified):
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(path, encoding=enc, dtype=str)
            df.columns = (
                df.columns.astype(str)
                .str.replace("\ufeff", "", regex=False)
                .str.strip()
            )

            if "행정구역" not in df.columns:
                raise ValueError(
                    "행정구역 열이 없습니다. 열 이름: "
                    + ", ".join(df.columns[:8])
                )

            df["행정구역"] = (
                df["행정구역"]
                .fillna("")
                .str.replace(r"\s*\(\d+\)\s*$", "", regex=True)
                .str.strip()
            )

            return df

        except UnicodeDecodeError:
            continue

    raise ValueError("CSV를 UTF-8 또는 CP949로 읽을 수 없습니다.")


# 한글 폰트 설정
def set_font():
    candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]

    for path in candidates:
        if Path(path).is_file():
            font_manager.fontManager.addfont(path)
            plt.rcParams["font.family"] = (
                font_manager.FontProperties(fname=path).get_name()
            )
            break

    plt.rcParams["axes.unicode_minus"] = False


# 화면 제목
st.title("📈 서울특별시 연령별 인구 분석")
st.caption(
    "행정구역, 연도, 성별을 선택하면 연령대별 인구수를 표시합니다."
)

# CSV 파일 확인
if not CSV_PATH.is_file():
    st.error(
        "population.csv를 찾을 수 없습니다. "
        "Python 파일은 pages 폴더, CSV는 상위 폴더에 두세요."
    )
    st.code(str(CSV_PATH))
    st.stop()

try:
    df = load_csv(
        str(CSV_PATH),
        CSV_PATH.stat().st_mtime_ns
    )
except Exception as e:
    st.error(f"CSV 읽기 실패: {e}")
    st.stop()


# 연령별 데이터 열 자동 인식
# 예시: 2025년_남_거주자_0~9세
pattern = re.compile(
    r"^(\d{4})년_(?:(남|여)_)?거주자_(\d+~\d+세|100세 이상)$"
)

column_map = {}

for col in df.columns:
    m = pattern.fullmatch(col)

    if m:
        year, sex, age = m.groups()

        gender_name = {
            "남": "남성",
            "여": "여성",
            None: "전체"
        }[sex]

        column_map[
            (int(year), gender_name, age)
        ] = col


# 선택 가능한 연도와 행정구역
years = sorted({k[0] for k in column_map})

areas = [
    x for x in df["행정구역"].unique().tolist()
    if x
]

if not years or not areas:
    st.error(
        "연도 또는 행정구역을 확인할 수 없습니다. "
        "현재 파일의 열 이름을 확인하세요."
    )

    with st.expander("CSV 진단 정보", expanded=True):
        st.write("경로:", str(CSV_PATH))
        st.write("크기:", df.shape)
        st.write("처음 20개 열:", list(df.columns[:20]))

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


# 연령 구간 설정
age_labels = [
    f"{a}~{a+9}세"
    for a in range(0, 100, 10)
] + ["100세 이상"]


# 선택한 행정구역 데이터
row = df.loc[
    df["행정구역"].eq(area)
].iloc[0]

records = []

for age in age_labels:
    col = column_map.get((year, sex, age))

    if col is None:
        st.error(
            f"열을 찾을 수 없습니다: "
            f"{year}년 / {sex} / {age}"
        )
        st.stop()

    value = pd.to_numeric(
        str(row[col]).replace(",", "").strip(),
        errors="coerce"
    )

    if pd.isna(value):
        st.error(
            f"인구수 값이 비어 있거나 숫자가 아닙니다: {col}"
        )
        st.stop()

    records.append({
        "연령": age,
        "인구수": int(value)
    })


# 데이터프레임 생성
result = pd.DataFrame(records)

peak = result.loc[
    result["인구수"].idxmax()
]


# 인구 요약
metric1, metric2 = st.columns(2)

metric1.metric(
    "연령대 인구 합계",
    f"{result['인구수'].sum():,}명"
)

metric2.metric(
    "인구가 가장 많은 연령대",
    f"{peak['연령']} ({peak['인구수']:,}명)"
)


# 한글 폰트 적용
set_font()


# 검정색 꺾은선 그래프
fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    result["연령"],
    result["인구수"],
    color="black",
    linewidth=2,
    marker="o",
    markersize=4
)

ax.set_title(
    f"{area} · {year}년 · {sex} 연령별 인구",
    fontsize=15
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

# 세로축 기준 가로 구분선
ax.grid(
    axis="y",
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


# 상세 데이터 확인 및 다운로드
with st.expander("📋 데이터 표 및 다운로드"):

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
