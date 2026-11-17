
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


# ==========================================
# 1. 스트림릿 기본 설정
# ==========================================

st.set_page_config(
    page_title="월별 기온 예측 비교",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 평균기온 예측: 머신러닝 3종 비교")

st.caption(
    "1907~2025년 실제 기온을 이용해 "
    "선형회귀, 2차 다항회귀, 랜덤 포레스트를 비교합니다."
)


# ==========================================
# 2. CSV 파일 자동 검색
# ==========================================

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
        "temperature.csv 파일을 찾지 못했습니다."
    )
    st.info(
        "GitHub에서 파일 이름과 위치를 확인하세요."
    )
    st.code(
        "\n".join(str(p) for p in CANDIDATES),
        language="text"
    )
    st.stop()


# ==========================================
# 3. CSV 데이터 읽기
# ==========================================

@st.cache_data
def load_data(file_path, modified_time):

    df = None

    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError(
            "CSV 인코딩을 읽을 수 없습니다."
        )

    df.columns = (
        df.columns.astype(str).str.strip()
    )

    required = {"일시", "평균기온(℃)"}

    if not required.issubset(df.columns):
        raise ValueError(
            "필수 열이 없습니다. "
            f"현재 열: {list(df.columns)}"
        )

    # Oct-07 형식의 날짜 처리
    dates = df["일시"].astype(str).str.strip()

    parts = dates.str.extract(
        r"^([A-Za-z]{3})-(\d{2})$"
    )

    if parts.isna().any().any():
        raise ValueError(
            "날짜 형식은 Oct-07과 같아야 합니다."
        )

    month_names = [
        "jan", "feb", "mar", "apr",
        "may", "jun", "jul", "aug",
        "sep", "oct", "nov", "dec"
    ]

    month_map = {
        name: i
        for i, name in enumerate(month_names, 1)
    }

    months = (
        parts[0].str.lower().map(month_map)
    )

    if months.isna().any():
        raise ValueError(
            "알 수 없는 월 이름이 있습니다."
        )

    suffixes = (
        parts[1].astype(int).to_numpy()
    )

    years = []
    century = 1900
    previous = None

    for suffix in suffixes:

        if previous is not None and suffix < previous:

            if previous >= 90 and suffix <= 10:
                century += 100
            else:
                raise ValueError(
                    "CSV 날짜가 시간순으로 "
                    "정렬되어 있지 않습니다."
                )

        years.append(
            century + int(suffix)
        )

        previous = suffix

    df["연도"] = years
    df["월"] = months.astype(int)

    df["평균기온"] = pd.to_numeric(
        df["평균기온(℃)"],
        errors="coerce"
    )

    # 실제 데이터는 2025년까지만 사용
    df = df.loc[
        df["연도"].between(1907, 2025)
    ].copy()

    df = df.dropna(
        subset=["평균기온"]
    )

    return df


try:
    data = load_data(
        str(CSV_PATH),
        CSV_PATH.stat().st_mtime_ns
    )

except Exception as exc:
    st.error(
        f"데이터 읽기 오류: {exc}"
    )
    st.stop()

if data.empty:
    st.error(
        "1907~2025년의 유효한 데이터가 없습니다."
    )
    st.stop()


# ==========================================
# 4. 사용자 입력
# ==========================================

st.subheader("📅 분석 조건 선택")

c1, c2 = st.columns(2)

with c1:
    month = st.selectbox(
        "분석할 월",
        range(1, 13),
        format_func=lambda m: f"{m}월"
    )

with c2:
    target_year = st.number_input(
        "예측 연도",
        min_value=1907,
        max_value=2300,
        value=2030,
        step=1
    )


# ==========================================
# 5. 월별 데이터 추출
# ==========================================

monthly = (
    data.loc[
        data["월"] == month,
        ["연도", "평균기온"]
    ]
    .groupby(
        "연도",
        as_index=False
    )["평균기온"]
    .mean()
    .sort_values("연도")
)

if len(monthly) < 12:
    st.error(
        "선택한 월의 유효한 데이터가 부족합니다."
    )
    st.stop()


# ==========================================
# 6. 머신러닝 알고리즘 3가지
# ==========================================

# 연도를 1900년 기준으로 변환
def to_x(years):

    return (
        np.asarray(
            years,
            dtype=float
        ).reshape(-1, 1) - 1900.0
    )


def make_models():

    return {

        # 알고리즘 1: 선형회귀
        "선형회귀": LinearRegression(),

        # 알고리즘 2: 2차 다항회귀
        "2차 다항회귀": make_pipeline(
            StandardScaler(),
            PolynomialFeatures(
                degree=2,
                include_bias=False
            ),
            LinearRegression()
        ),

        # 알고리즘 3: 랜덤 포레스트
        "랜덤 포레스트": RandomForestRegressor(
            n_estimators=150,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1
        )
    }


# ==========================================
# 7. 알고리즘 정확도 검증
# ==========================================

# 과거 마지막 최대 20개 연도를
# 테스트 데이터로 분리

test_count = min(
    20,
    max(3, len(monthly) // 5)
)

train = monthly.iloc[:-test_count]
test = monthly.iloc[-test_count:]

if len(train) < 5:
    st.error(
        "모델 학습에 필요한 데이터가 부족합니다."
    )
    st.stop()

scores = {}

for name, model in make_models().items():

    model.fit(
        to_x(train["연도"]),
        train["평균기온"].to_numpy()
    )

    test_predictions = model.predict(
        to_x(test["연도"])
    )

    scores[name] = float(
        mean_absolute_error(
            test["평균기온"],
            test_predictions
        )
    )


# ==========================================
# 8. 전체 데이터로 다시 학습
# ==========================================

models = make_models()

for model in models.values():

    model.fit(
        to_x(monthly["연도"]),
        monthly["평균기온"].to_numpy()
    )


# ==========================================
# 9. 선택한 연도의 기온 예측
# ==========================================

predictions = {}

for name, model in models.items():

    predictions[name] = float(
        model.predict(
            to_x([target_year])
        )[0]
    )


st.subheader(
    f"🔮 {target_year}년 {month}월 예측 평균기온"
)

cols = st.columns(3)

for col, (name, value) in zip(
    cols,
    predictions.items()
):

    col.metric(
        name,
        f"{value:.2f} ℃"
    )


# ==========================================
# 10. 그래프 생성
# ==========================================

st.subheader(
    "📈 실제 기온과 머신러닝 예측 비교"
)

first_year = int(
    monthly["연도"].min()
)

last_year = int(
    monthly["연도"].max()
)

end_year = max(
    last_year,
    int(target_year)
)

plot_years = np.arange(
    first_year,
    end_year + 1
)

colors = {
    "선형회귀": "#F05265",
    "2차 다항회귀": "#16A34A",
    "랜덤 포레스트": "#9B59B6"
}

fig = go.Figure()


# 실제 관측 기온
fig.add_trace(
    go.Scatter(
        x=monthly["연도"],
        y=monthly["평균기온"],

        mode="markers",

        name="실제 평균기온 (2025년까지)",

        marker=dict(
            color="#289BE6",
            size=6
        ),

        hovertemplate=(
            "%{x}년: %{y:.2f} ℃"
            "<extra>관측값</extra>"
        )
    )
)


# 세 알고리즘의 그래프
for name, model in models.items():

    fitted = model.predict(
        to_x(plot_years)
    )

    past_mask = (
        plot_years <= last_year
    )

    future_mask = (
        plot_years >= last_year
    )

    # 과거 데이터 적합선
    fig.add_trace(
        go.Scatter(
            x=plot_years[past_mask],
            y=fitted[past_mask],

            mode="lines",

            name=f"{name} (과거 적합)",

            line=dict(
                color=colors[name],
                width=2.5
            )
        )
    )

    # 미래 예측선
    if end_year > last_year:

        fig.add_trace(
            go.Scatter(
                x=plot_years[future_mask],
                y=fitted[future_mask],

                mode="lines",

                name=f"{name} (미래 예측)",

                line=dict(
                    color=colors[name],
                    width=3,
                    dash="dash"
                )
            )
        )

    # 사용자가 입력한 연도의 예측값
    fig.add_trace(
        go.Scatter(
            x=[target_year],
            y=[predictions[name]],

            mode="markers",

            name=f"{name} 선택 연도",

            marker=dict(
                color=colors[name],
                size=12,
                symbol="star"
            ),

            hovertemplate=(
                f"{name}: %{{y:.2f}} ℃"
                "<extra></extra>"
            )
        )
    )


# 그래프 디자인
fig.update_layout(

    title=(
        f"{month}월 실제 평균기온과 "
        "세 알고리즘 비교"
    ),

    xaxis_title="연도",

    yaxis_title="평균기온 (℃)",

    xaxis=dict(
        range=[
            first_year - 3,
            end_year + 3
        ]
    ),

    hovermode="x unified",

    height=600,

    legend=dict(
        orientation="h",
        y=-0.25
    ),

    margin=dict(
        t=65,
        b=130
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

st.caption(
    "파란 점은 실제 관측값입니다. "
    "실선은 과거 데이터에 대한 모델의 적합 결과, "
    "점선은 관측 종료 이후의 예측입니다. "
    "별은 선택한 연도의 예측값입니다."
)


# ==========================================
# 11. 알고리즘별 오차 비교
# ==========================================

st.subheader(
    "📊 알고리즘별 예측 오차 비교"
)

score_df = pd.DataFrame({

    "알고리즘": list(scores),

    "MAE (℃)": list(
        scores.values()
    )

}).sort_values(
    "MAE (℃)"
)

st.dataframe(
    score_df.style.format({
        "MAE (℃)": "{:.2f}"
    }),
    hide_index=True,
    use_container_width=True
)


# MAE 막대그래프
bar = go.Figure(
    go.Bar(
        x=score_df["알고리즘"],
        y=score_df["MAE (℃)"],

        marker_color=[
            colors[name]
            for name in score_df["알고리즘"]
        ]
    )
)

bar.update_layout(
    title="알고리즘별 평균절대오차",

    xaxis_title="알고리즘",

    yaxis_title="MAE (℃)",

    height=350
)

st.plotly_chart(
    bar,
    use_container_width=True
)

st.write(
    f"과거 마지막 **{test_count}개 관측 연도**를 "
    "학습에서 제외하고 예측한 뒤 "
    "실제 기온과 비교했습니다."
)

st.info(
    "MAE가 작을수록 검증 구간에서 "
    "실제 기온과 예측 기온의 차이가 작습니다. "
    "단, 미래 예측의 정확도를 보장하지는 않습니다."
)


# ==========================================
# 12. 알고리즘 설명
# ==========================================

st.subheader(
    "📘 세 가지 머신러닝 알고리즘 설명"
)

st.markdown("""
### 🔴 1. 선형회귀

과거 기온 데이터에 가장 잘 맞는
**직선**을 찾는 알고리즘입니다.

직선의 기울기를 이용해 미래 기온을 예측합니다.

**특징**
- 작동 원리가 간단합니다.
- 장기적인 기온 변화 추세를 파악하기 좋습니다.
- 복잡한 기온 변화를 표현하는 데 한계가 있습니다.

---

### 🟢 2. 다항회귀

직선 대신 **곡선**을 이용해
데이터의 변화 추세를 분석합니다.

이번 프로그램에서는 2차 다항회귀를 사용합니다.

**특징**
- 기온 변화의 굴곡을 표현할 수 있습니다.
- 직선보다 복잡한 패턴을 학습할 수 있습니다.
- 먼 미래에는 예측값이 급격하게 변할 수 있습니다.

---

### 🟣 3. 랜덤 포레스트

여러 개의 **결정트리**가 각각 예측한 결과를
평균하여 최종 기온을 예측합니다.

**특징**
- 복잡한 데이터 패턴을 학습할 수 있습니다.
- 여러 결정트리를 사용합니다.
- 관측하지 않은 먼 미래의 상승·하락 추세를
  예측하는 데는 한계가 있습니다.

---

### 📏 MAE란?

MAE는 평균절대오차입니다.

**MAE = 실제 기온과 예측 기온의 차이의 절댓값을 평균한 값**

예를 들어 MAE가 1.5℃라면
검증 구간에서 평균적으로 1.5℃의
예측 오차가 발생했다는 뜻입니다.
""")


# ==========================================
# 13. 예측의 한계
# ==========================================

st.warning(
    "⚠️ 이 프로그램은 연도만을 이용해 "
    "미래 평균기온을 예측합니다. "
    "온실가스 배출량, 기상 조건 등은 "
    "반영하지 않습니다. "
    "특히 먼 미래의 예측은 "
    "불확실성이 클 수 있습니다."
)


# ==========================================
# 14. 실제 데이터 확인 및 다운로드
# ==========================================

with st.expander(
    "📋 실제 기온 데이터 확인 및 다운로드"
):

    st.dataframe(
        monthly.rename(
            columns={
                "평균기온": "평균기온(℃)"
            }
        ),
        hide_index=True,
        use_container_width=True
    )

    csv_data = monthly.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        "📥 CSV 다운로드",
        data=csv_data,
        file_name=f"temperature_{month}month.csv",
        mime="text/csv"
    )
