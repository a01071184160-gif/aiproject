
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

st.set_page_config(
    page_title="월별 평균기온 선형회귀 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 평균기온 분석 및 선형회귀 예측")
st.caption("과거 월평균 기온을 이용해 연도별 변화와 선형회귀 추세를 살펴봅니다.")

CSV_PATH = Path(__file__).resolve().parent / "temperature.csv"


@st.cache_data
def load_data(path):
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(
            "CSV 인코딩을 읽지 못했습니다. UTF-8 또는 CP949 파일인지 확인하세요."
        )

    required = {"일시", "평균기온(℃)"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"필수 열이 없습니다: {', '.join(sorted(missing))}")

    # 첨부 자료는 1907년부터 월별로 이어지는 데이터입니다.
    # Oct-07 같은 두 자리 연도 날짜를 처리합니다.
    raw_dates = df["일시"].astype(str).str.strip()

    parsed = pd.to_datetime(
        raw_dates,
        format="%b-%y",
        errors="coerce"
    )

    if parsed.isna().any():
        raise ValueError(
            "'일시' 열의 날짜 형식이 Oct-07과 같은지 확인하세요."
        )

    first_year = 1907
    first_month = int(parsed.iloc[0].month)

    month_index = (
        first_year * 12 + first_month - 1
    ) + np.arange(len(df))

    expected_months = (month_index % 12) + 1

    if not np.array_equal(
        parsed.dt.month.to_numpy(),
        expected_months
    ):
        raise ValueError("날짜가 연속된 월별 자료가 아닙니다.")

    expected_year_suffix = (month_index // 12) % 100

    actual_suffix = (
        raw_dates.str.extract(r"-(\d{2})$")[0]
        .astype(int)
        .to_numpy()
    )

    if not np.array_equal(
        expected_year_suffix,
        actual_suffix
    ):
        raise ValueError("연도 순서가 예상과 다릅니다.")

    df["연도"] = month_index // 12
    df["월"] = expected_months

    df["평균기온"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    return df.dropna(subset=["평균기온"]).copy()


# 데이터 불러오기
try:
    data = load_data(str(CSV_PATH))

except FileNotFoundError:
    st.error(
        "temperature.csv를 찾을 수 없습니다. "
        "app.py와 같은 폴더에 업로드하세요."
    )
    st.stop()

except Exception as e:
    st.error(f"데이터 읽기 오류: {e}")
    st.stop()


# 사용자 입력
col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox(
        "📅 분석할 월",
        range(1, 13),
        format_func=lambda m: f"{m}월",
        index=0
    )

with col2:
    prediction_year = st.number_input(
        "🔮 예측 연도",
        min_value=int(data["연도"].min()),
        max_value=2300,
        value=2030,
        step=1
    )


# 선택한 월의 데이터 추출
monthly = data.loc[
    data["월"] == selected_month,
    ["연도", "평균기온"]
].sort_values("연도")

monthly = monthly.groupby(
    "연도",
    as_index=False
)["평균기온"].mean()

if len(monthly) < 2:
    st.warning(
        "이 월에는 선형회귀를 계산할 데이터가 충분하지 않습니다."
    )
    st.stop()


# 선형회귀 모델 학습
X = monthly[["연도"]].to_numpy(dtype=float)
y = monthly["평균기온"].to_numpy(dtype=float)

model = LinearRegression()
model.fit(X, y)


# 예측 기온 계산
predicted = float(
    model.predict(
        np.array([[prediction_year]], dtype=float)
    )[0]
)

start_year = int(monthly["연도"].min())
last_year = int(monthly["연도"].max())

line_years = np.linspace(
    start_year,
    max(last_year, int(prediction_year)),
    350
)

line_temps = model.predict(
    line_years.reshape(-1, 1)
)

r2 = float(model.score(X, y))
slope = float(model.coef_[0])


# 분석 결과 표시
m1, m2, m3 = st.columns(3)

m1.metric(
    f"{prediction_year}년 {selected_month}월 예측 평균기온",
    f"{predicted:.2f} ℃"
)

m2.metric(
    "연간 추세 변화",
    f"{slope:+.3f} ℃/년"
)

m3.metric(
    "결정계수 R²",
    f"{r2:.3f}"
)


# 그래프 생성
fig = go.Figure()


# 실제 관측 평균기온
fig.add_trace(
    go.Scatter(
        x=monthly["연도"],
        y=monthly["평균기온"],
        mode="markers",
        name="실제 관측 평균기온",
        marker=dict(
            color="#36A3E9",
            size=7
        ),
        hovertemplate=(
            "%{x}년<br>"
            "관측: %{y:.1f} ℃"
            "<extra></extra>"
        )
    )
)


# 선형회귀 추세선
fig.add_trace(
    go.Scatter(
        x=line_years,
        y=line_temps,
        mode="lines",
        name="선형회귀 추세선",
        line=dict(
            color="#FF6B6B",
            width=3
        ),
        hovertemplate=(
            "%{x:.0f}년<br>"
            "회귀 추정: %{y:.2f} ℃"
            "<extra></extra>"
        )
    )
)


# 미래 예측 구간
if prediction_year > last_year:

    future_years = np.linspace(
        last_year,
        int(prediction_year),
        100
    )

    future_temps = model.predict(
        future_years.reshape(-1, 1)
    )

    fig.add_trace(
        go.Scatter(
            x=future_years,
            y=future_temps,
            mode="lines",
            name="미래 외삽 구간",
            line=dict(
                color="#F59E0B",
                width=4,
                dash="dash"
            )
        )
    )


# 예측 기온 강조
fig.add_trace(
    go.Scatter(
        x=[prediction_year],
        y=[predicted],
        mode="markers+text",
        name="선택 연도 예측값",
        marker=dict(
            color="#7C3AED",
            size=14,
            symbol="star"
        ),
        text=[f"{predicted:.2f}℃"],
        textposition="top center",
        hovertemplate=(
            "%{x}년 예측: %{y:.2f} ℃"
            "<extra></extra>"
        )
    )
)


# 그래프 디자인
fig.update_layout(
    title=(
        f"{selected_month}월 평균기온 변화 및 "
        "선형회귀 예측"
    ),
    xaxis_title="연도",
    yaxis_title="평균기온 (℃)",
    hovermode="closest",
    legend=dict(
        orientation="h",
        y=-0.23
    ),
    margin=dict(
        t=65,
        b=90
    ),
    height=540
)

fig.update_xaxes(
    range=[
        start_year - 3,
        max(last_year, int(prediction_year)) + 4
    ]
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# 선형회귀 알고리즘 설명
st.subheader("📘 선형회귀 알고리즘은 어떻게 작동할까요?")

st.markdown("""
**선형회귀**는 과거 데이터에 가장 잘 맞는 직선을 찾아
미래 값을 추정하는 방법입니다.

1. **파란 점**은 해당 연도와 월에 실제로 관측된 평균기온입니다.

2. **빨간 직선**은 파란 점들과의 세로 거리(오차)를
   제곱해 합한 값이 가장 작도록 찾은 직선입니다.

3. **보라색 별**은 사용자가 입력한 연도를
   이 직선에 대입해 계산한 예측 기온입니다.

4. **주황색 점선**은 관측된 마지막 연도 이후까지
   직선을 연장한 부분입니다.
   미래 예측의 불확실성이 특히 큰 구간입니다.

### 📐 선형회귀 공식

**예측 평균기온 = 기울기 × 연도 + 절편**

- 기울기가 양수이면 기온이 올라가는 추세입니다.
- 기울기가 음수이면 기온이 내려가는 추세입니다.
- 기울기가 0에 가까우면 장기적인 변화가 작다는 뜻입니다.
""")


# 실제 데이터로 계산한 회귀식
st.info(
    f"이번 {selected_month}월 데이터의 회귀식: "
    f"예측 기온 = "
    f"({slope:.5f} × 연도) + "
    f"({float(model.intercept_):.3f})"
)

st.caption(
    "R²는 직선이 과거 기온 변동을 어느 정도 "
    "설명하는지 보여주는 지표입니다. "
    "1에 가까울수록 과거 데이터에 잘 맞지만, "
    "미래 예측의 정확도를 보장하지는 않습니다. "
    "이 예측은 단순한 직선 추세이며 "
    "기후모형의 전망과는 다릅니다."
)


# 원본 분석 데이터 확인
with st.expander("📋 사용한 과거 평균기온 데이터 보기"):

    st.dataframe(
        monthly.rename(
            columns={"평균기온": "평균기온(℃)"}
        ),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "선택 월 데이터 CSV 내려받기",
        monthly.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"temperature_month_{selected_month}.csv",
        mime="text/csv"
    )
