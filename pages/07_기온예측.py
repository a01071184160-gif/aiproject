
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

st.set_page_config(
    page_title="월별 평균기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 평균기온 분석 및 선형회귀 예측")
st.caption(
    "temperature.csv의 과거 관측값으로 "
    "선택한 월의 평균기온 추세를 분석합니다."
)

# CSV 자동 경로 검색
HERE = Path(__file__).resolve().parent

CANDIDATES = [
    HERE / "temperature.csv",
    HERE.parent / "temperature.csv"
]

CSV_PATH = next(
    (p for p in CANDIDATES if p.is_file()),
    None
)

if CSV_PATH is None:
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "GitHub에 정확한 파일명으로 업로드해 주세요."
    )
    st.code(
        "\n".join(str(p) for p in CANDIDATES),
        language="text"
    )
    st.stop()


@st.cache_data
def load_temperature(path):
    frame = None

    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            frame = pd.read_csv(
                path,
                encoding=encoding
            )
            break
        except UnicodeDecodeError:
            continue

    if frame is None:
        raise ValueError("CSV 인코딩을 읽을 수 없습니다.")

    frame.columns = frame.columns.astype(str).str.strip()

    required = {"일시", "평균기온(℃)"}

    if not required.issubset(frame.columns):
        raise ValueError(
            f"필수 열이 없습니다. 현재 열: {list(frame.columns)}"
        )

    # Oct-07 형식의 날짜 처리
    dates = frame["일시"].astype(str).str.strip()

    parsed = pd.to_datetime(
        dates,
        format="%b-%y",
        errors="coerce"
    )

    if parsed.isna().any():
        raise ValueError(
            "일시 열은 Oct-07 같은 형식이어야 합니다."
        )

    suffix = dates.str.extract(r"-(\d{2})$")[0]

    if suffix.isna().any():
        raise ValueError("연도를 읽을 수 없습니다.")

    yy = suffix.astype(int).to_numpy()

    years = []
    century = 1900
    previous = None

    for value in yy:
        if previous is not None and value < previous:
            if previous >= 90 and value <= 10:
                century += 100
            else:
                raise ValueError(
                    "날짜가 연도순으로 정렬되어 있지 않습니다."
                )

        years.append(century + int(value))
        previous = value

    frame["연도"] = years
    frame["월"] = parsed.dt.month.astype(int)

    frame["평균기온"] = pd.to_numeric(
        frame["평균기온(℃)"],
        errors="coerce"
    )

    return frame.dropna(
        subset=["평균기온"]
    ).copy()


# CSV 데이터 불러오기
try:
    df = load_temperature(str(CSV_PATH))

except Exception as exc:
    st.error(f"CSV 읽기 오류: {exc}")
    st.stop()


# 사용자 입력
left, right = st.columns(2)

with left:
    month = st.selectbox(
        "📅 분석할 월",
        list(range(1, 13)),
        format_func=lambda x: f"{x}월"
    )

with right:
    target_year = st.number_input(
        "🔮 예측 연도",
        min_value=int(df["연도"].min()),
        max_value=2300,
        value=2030,
        step=1
    )


# 선택한 월의 데이터
monthly = (
    df.loc[
        df["월"] == month,
        ["연도", "평균기온"]
    ]
    .groupby("연도", as_index=False)["평균기온"]
    .mean()
    .sort_values("연도")
)

if len(monthly) < 2:
    st.warning(
        "선택한 월의 유효한 기온 데이터가 부족합니다."
    )
    st.stop()


# 선형회귀 모델
X = monthly[["연도"]].to_numpy(dtype=float)
y = monthly["평균기온"].to_numpy(dtype=float)

model = LinearRegression()
model.fit(X, y)

prediction = float(
    model.predict(
        np.array([[float(target_year)]])
    )[0]
)

slope = float(model.coef_[0])
intercept = float(model.intercept_)
r_squared = float(model.score(X, y))

first_year = int(monthly["연도"].min())
last_year = int(monthly["연도"].max())
end_year = max(last_year, int(target_year))


# 결과 표시
m1, m2, m3 = st.columns(3)

m1.metric(
    f"{target_year}년 {month}월 예측 기온",
    f"{prediction:.2f} ℃"
)

m2.metric(
    "연간 추세 변화",
    f"{slope:+.3f} ℃/년"
)

m3.metric(
    "결정계수 R²",
    f"{r_squared:.3f}"
)


# 그래프 생성
fig = go.Figure()

# 실제 평균기온
fig.add_trace(
    go.Scatter(
        x=monthly["연도"],
        y=monthly["평균기온"],
        mode="markers",
        name="실제 평균기온",
        marker=dict(
            color="#3199E8",
            size=7
        ),
        hovertemplate=(
            "%{x}년: %{y:.1f} ℃"
            "<extra>관측값</extra>"
        )
    )
)


# 선형회귀 추세선
observed_years = np.linspace(
    first_year,
    last_year,
    300
)

fig.add_trace(
    go.Scatter(
        x=observed_years,
        y=model.predict(
            observed_years.reshape(-1, 1)
        ),
        mode="lines",
        name="선형회귀 추세선",
        line=dict(
            color="#F05265",
            width=3
        )
    )
)


# 미래 예측 구간
if target_year > last_year:

    future_years = np.linspace(
        last_year,
        int(target_year),
        120
    )

    future_temps = model.predict(
        future_years.reshape(-1, 1)
    )

    fig.add_trace(
        go.Scatter(
            x=future_years,
            y=future_temps,
            mode="lines",
            name="미래 예측 구간",
            line=dict(
                color="#F59E0B",
                width=3,
                dash="dash"
            )
        )
    )


# 예측값 표시
fig.add_trace(
    go.Scatter(
        x=[target_year],
        y=[prediction],
        mode="markers+text",
        name="선택 연도 예측값",
        marker=dict(
            color="#7C3AED",
            size=15,
            symbol="star"
        ),
        text=[f"{prediction:.2f} ℃"],
        textposition="top center"
    )
)


# 그래프 설정
fig.update_layout(
    title=f"{month}월 평균기온 변화와 선형회귀 예측",
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    xaxis=dict(
        range=[
            first_year - 3,
            end_year + 4
        ]
    ),
    height=550,
    hovermode="closest",
    legend=dict(
        orientation="h",
        y=-0.23
    ),
    margin=dict(
        t=65,
        b=90
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# 알고리즘 설명
st.subheader(
    "📘 선형회귀 알고리즘은 어떻게 작동할까요?"
)

st.markdown("""
선형회귀는 **과거 데이터에 가장 잘 맞는 직선**을
찾고, 그 직선을 이용해 기온을 예측하는 방법입니다.

1. **파란 점**은 실제로 관측한 평균기온입니다.

2. **빨간 직선**은 실제 기온과 직선 사이의
   오차를 제곱해 더한 값이 가장 작아지도록
   계산한 선형회귀 추세선입니다.

3. **주황색 점선**은 마지막 관측 연도 이후로
   회귀직선을 연장한 미래 예측 구간입니다.

4. **보라색 별**은 사용자가 선택한 연도의
   예측 평균기온을 나타냅니다.

### 📐 선형회귀 공식

**예측 기온 = 기울기 × 연도 + 절편**

- 기울기가 양수이면 기온이 상승하는 추세입니다.
- 기울기가 음수이면 기온이 하락하는 추세입니다.
- 기울기가 0에 가까우면 장기적인 변화가 작습니다.
""")

st.info(
    f"이번 {month}월의 회귀식: "
    f"예측 기온 = "
    f"({slope:.5f} × 연도) + "
    f"({intercept:.3f})"
)

st.caption(
    "R²는 회귀직선이 과거 데이터의 변동을 "
    "얼마나 설명하는지 나타냅니다. "
    "미래 예측의 정확도를 보장하지 않으며, "
    "먼 미래의 예측일수록 불확실성이 커질 수 있습니다."
)


# 분석 데이터 확인
with st.expander("📋 분석에 사용한 데이터 보기"):

    st.dataframe(
        monthly.rename(
            columns={
                "평균기온": "평균기온(℃)"
            }
        ),
        hide_index=True,
        use_container_width=True
    )

    st.download_button(
        "선택한 월의 데이터 다운로드",
        monthly.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"temperature_{month}month.csv",
        mime="text/csv"
    )
