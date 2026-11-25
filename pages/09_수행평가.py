import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor
)
from sklearn.model_selection import (
    train_test_split,
    KFold
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="식재료 가격 및 원가 관리",
    page_icon="🍽️",
    layout="wide"
)

st.title(
    "🍽️ 농축수산물 가격 분석 및 외식업 원가 관리 시스템"
)

st.caption(
    "공공데이터 기반 가격 분석 · 머신러닝 · 메뉴 원가 관리"
)

ROOT = Path(__file__).resolve().parent.parent

KEY = [
    "월",
    "품목명",
    "품종명",
    "등급명",
    "유통단계별무게",
    "유통단계별단위"
]

PRICE = "평균가격"

CAT = [
    "품목명",
    "품종명",
    "등급명",
    "유통단계별단위"
]

NUM = [
    "월",
    "유통단계별무게"
]

FEATURES = CAT + NUM

NAMES = [
    "선형 회귀",
    "랜덤 포레스트",
    "그래디언트 부스팅"
]

COLORS = dict(zip(
    NAMES,
    ["#2563EB", "#16A34A", "#F97316"]
))

# ==========================================
# 2. CSV 불러오기 및 데이터 전처리
# ==========================================

@st.cache_data
def load(path, modified):

    for enc in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            raw = pd.read_csv(
                path,
                encoding=enc
            )
            break

        except UnicodeError:
            continue

    else:
        raise ValueError("CSV 인코딩 오류")

    raw.columns = raw.columns.str.strip()

    required = [
        "가격등록연월"
    ] + KEY[1:] + [PRICE]

    if not set(required).issubset(raw.columns):
        raise ValueError(
            "필수 열이 없습니다: "
            + str(set(required) - set(raw.columns))
        )

    d = (
        raw.dropna(subset=required)
        .drop_duplicates()
        .copy()
    )

    for c in CAT:
        d[c] = d[c].astype(str).str.strip()

    for c in [PRICE, KEY[-2]]:
        d[c] = pd.to_numeric(
            d[c].astype(str).str.replace(",", ""),
            errors="coerce"
        )

    months = dict(zip(
        "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(),
        range(1, 13)
    ))

    d["월"] = (
        d["가격등록연월"]
        .astype(str)
        .str.strip()
        .str[:3]
        .str.title()
        .map(months)
    )

    d = d.dropna(
        subset=["월", PRICE, KEY[-2]]
    )

    d = d[
        (d[PRICE] > 0)
        & (d[KEY[-2]] > 0)
    ].copy()

    d["월"] = d["월"].astype(int)

    d = (
        d.groupby(
            KEY,
            as_index=False
        )[PRICE].mean()
    )

    d["판매단위"] = (
        d[KEY[-2]].map(lambda x: f"{x:g}")
        + d[KEY[-1]]
    )

    d["식재료"] = (
        d["품목명"]
        + " - "
        + d["품종명"]
    )

    d["비교단위"] = d[KEY[-1]].replace({
        "g": "kg"
    })

    d["환산가격"] = (
        d[PRICE] / d[KEY[-2]]
        * np.where(
            d[KEY[-1]].eq("g"),
            1000,
            1
        )
    )

    return raw, d


try:

    candidates = [
        ROOT / "food_price.csv",
        *sorted(
            ROOT.glob("*농축수산물*소매가격*.csv")
        )
    ]

    path = next(
        p for p in candidates if p.is_file()
    )

    raw, df = load(
        str(path),
        path.stat().st_mtime
    )

    if df.empty:
        raise ValueError(
            "분석 가능한 데이터가 없습니다."
        )

except StopIteration:

    st.error(
        "pages 상위 폴더에 food_price.csv "
        "또는 기존 CSV 파일을 넣어주세요."
    )

    st.stop()

except Exception as e:

    st.error(str(e))
    st.stop()

# ==========================================
# 3. 데이터 요약
# ==========================================

st.info(
    "연도 표기의 신뢰성이 불확실하여 "
    "같은 월·품목·품종·등급·판매단위의 "
    "기록을 평균으로 집계합니다. "
    "미래 가격 예측이 아닌 조건별 가격 추정입니다."
)

summary_items = [
    ("원본 데이터", len(raw)),
    ("분석 데이터", len(df)),
    ("식재료 품목", df["품목명"].nunique()),
    ("분석 가능 월", df["월"].nunique())
]

for c, (label, value) in zip(
    st.columns(4),
    summary_items
):
    c.metric(label, f"{value:,}")

# ==========================================
# 4. 공통 함수
# ==========================================

def chart(fig):

    st.plotly_chart(
        fig,
        use_container_width=True
    )


def table(d):

    st.dataframe(
        d.round(3),
        hide_index=True,
        use_container_width=True
    )


def month_axis(fig):

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=[
            f"{i}월" for i in range(1, 13)
        ]
    )

    fig.update_yaxes(
        tickformat=",.0f"
    )

    return fig


def choose(key, data=df, grade=True):

    cols = st.columns(
        4 if grade else 3
    )

    d = data

    fields = (
        ["품목명", "품종명"]
        + (["등급명"] if grade else [])
        + ["판매단위"]
    )

    for col, field in zip(cols, fields):

        v = col.selectbox(
            field,
            sorted(d[field].unique()),
            key=key + field
        )

        d = d[d[field] == v]

    return d

# ==========================================
# 5. 머신러닝 모델 설정
# ==========================================

def make_model(name):

    models = {

        NAMES[0]: LinearRegression(),

        NAMES[1]: RandomForestRegressor(
            n_estimators=150,
            random_state=42,
            n_jobs=1
        ),

        NAMES[2]: GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=3,
            random_state=42
        )
    }

    prep = ColumnTransformer([

        (
            "category",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            ),
            CAT
        ),

        (
            "number",
            "passthrough",
            NUM
        )
    ])

    return Pipeline([
        ("prep", prep),
        ("model", models[name])
    ])


def predict(model, x):

    return np.maximum(
        model.predict(x),
        0
    )


def scores(y, p):

    return {
        "MAE": mean_absolute_error(y, p),

        "RMSE": np.sqrt(
            mean_squared_error(y, p)
        ),

        "R²": r2_score(y, p)
    }

# ==========================================
# 6. 머신러닝 모델 학습
# ==========================================

@st.cache_resource
def train(data):

    a, b = train_test_split(
        data,
        test_size=0.2,
        random_state=42
    )

    models = {}
    rows = []

    preds = pd.DataFrame({
        "실제 가격": b[PRICE].to_numpy()
    })

    for name in NAMES:

        model = make_model(name)

        model.fit(
            a[FEATURES],
            a[PRICE]
        )

        p = predict(
            model,
            b[FEATURES]
        )

        models[name] = model

        rows.append({
            "알고리즘": name,
            **scores(b[PRICE], p)
        })

        preds[name] = p

    return (
        models,
        pd.DataFrame(rows),
        preds,
        len(a),
        len(b)
    )

# ==========================================
# 7. 5-Fold 교차 검증
# ==========================================

@st.cache_data
def cv_results(data):

    rows = []

    folds = KFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    for fold, (a, b) in enumerate(
        folds.split(data),
        1
    ):

        train_data = data.iloc[a]
        test_data = data.iloc[b]

        for name in NAMES:

            model = make_model(name)

            model.fit(
                train_data[FEATURES],
                train_data[PRICE]
            )

            p = predict(
                model,
                test_data[FEATURES]
            )

            rows.append({
                "알고리즘": name,
                "회차": fold,
                **scores(test_data[PRICE], p)
            })

    return pd.DataFrame(rows)

# ==========================================
# 8. 사이드바 메뉴
# ==========================================

menu = st.sidebar.radio(
    "분석 메뉴",
    [
        "월별 가격 분석",
        "품목별 가격 비교",
        "등급별 가격 비교",
        "가격 히트맵",
        "머신러닝 가격 예측",
        "알고리즘 성능 비교",
        "메뉴 원가 및 판매가격",
        "가격 변동률 순위",
        "5-Fold 교차 검증",
        "데이터 정보"
    ]
)

st.header(menu)

# ==========================================
# 9. 월별 가격 분석
# ==========================================

if menu == "월별 가격 분석":

    d = choose("monthly")

    m = (
        d.groupby(
            "월",
            as_index=False
        )[PRICE].mean()
        .sort_values("월")
    )

    fig = px.line(
        m,
        x="월",
        y=PRICE,
        markers=True,
        title="월별 식재료 가격 변화",
        labels={
            PRICE: "평균가격(원)"
        }
    )

    fig.update_traces(
        line=dict(
            color="#2563EB",
            width=3
        ),
        marker=dict(size=9)
    )

    fig.add_hline(
        y=m[PRICE].mean(),
        line_dash="dash",
        annotation_text="월평균 가격"
    )

    chart(month_axis(fig))

    lo = m.loc[m[PRICE].idxmin()]
    hi = m.loc[m[PRICE].idxmax()]

    items = [
        (
            f"최저가 ({int(lo['월'])}월)",
            lo[PRICE]
        ),
        (
            f"최고가 ({int(hi['월'])}월)",
            hi[PRICE]
        ),
        (
            "월평균 가격",
            m[PRICE].mean()
        ),
        (
            "최고·최저 가격 차이",
            hi[PRICE] - lo[PRICE]
        )
    ]

    for c, (label, value) in zip(
        st.columns(4),
        items
    ):

        c.metric(
            label,
            f"{value:,.0f}원"
        )

    change = (
        hi[PRICE] / lo[PRICE] - 1
    ) * 100

    st.subheader("자동 분석 결과")

    st.info(
        f"기록상 최저가는 {int(lo['월'])}월이며 "
        f"최고가는 최저가보다 "
        f"{change:.1f}% 높습니다."
    )

    table(m)

# ==========================================
# 10. 품목별 가격 비교
# ==========================================

elif menu == "품목별 가격 비교":

    month = st.selectbox(
        "월",
        sorted(df["월"].unique())
    )

    unit = st.selectbox(
        "비교 단위",
        sorted(df["비교단위"].unique())
    )

    grade = st.selectbox(
        "등급",
        sorted(df["등급명"].unique())
    )

    d = df[
        (df["월"] == month)
        & (df["비교단위"] == unit)
        & (df["등급명"] == grade)
    ]

    n = st.slider(
        "표시 개수",
        1,
        30,
        10
    )

    order = st.radio(
        "정렬",
        ["높은 순", "낮은 순"],
        horizontal=True
    )

    d = (
        d.groupby(
            "식재료",
            as_index=False
        )["환산가격"].mean()
        .sort_values(
            "환산가격",
            ascending=order == "낮은 순"
        )
        .head(n)
    )

    if d.empty:

        st.warning(
            "해당 조건의 데이터가 없습니다."
        )

    else:

        fig = px.bar(
            d,
            x="식재료",
            y="환산가격",
            color="환산가격",
            color_continuous_scale="Blues",
            title=f"{month}월 식재료 가격 비교",
            labels={
                "환산가격":
                    f"1{unit}당 가격(원)"
            }
        )

        fig.update_layout(
            coloraxis_showscale=False
        )

        chart(fig)
        table(d)

    st.caption(
        "g과 kg은 kg으로 환산하며 "
        "다른 단위는 동일 단위끼리 비교합니다."
    )

# ==========================================
# 11. 등급별 가격 비교
# ==========================================

elif menu == "등급별 가격 비교":

    d = choose(
        "grade",
        grade=False
    )

    m = (
        d.groupby(
            ["월", "등급명"],
            as_index=False
        )[PRICE].mean()
    )

    if m["등급명"].nunique() < 2:

        st.warning(
            "비교 가능한 등급이 하나뿐입니다."
        )

    fig = px.bar(
        m,
        x="월",
        y=PRICE,
        color="등급명",
        barmode="group",
        color_discrete_map={
            "상품": "#2563EB",
            "중품": "#F97316"
        },
        title="등급별 식재료 가격 비교"
    )

    chart(month_axis(fig))
    table(m)

# ==========================================
# 12. 가격 히트맵
# ==========================================

elif menu == "가격 히트맵":

    grade = st.selectbox(
        "등급",
        sorted(df["등급명"].unique())
    )

    unit = st.selectbox(
        "단위",
        sorted(df["비교단위"].unique())
    )

    d = df[
        (df["등급명"] == grade)
        & (df["비교단위"] == unit)
    ]

    opts = sorted(
        d["식재료"].unique()
    )

    foods = st.multiselect(
        "식재료",
        opts,
        default=opts[:8]
    )

    if foods:

        p = (
            d[d["식재료"].isin(foods)]
            .pivot_table(
                index="식재료",
                columns="월",
                values="환산가격"
            )
            .reindex(columns=range(1, 13))
        )

        p = p.div(
            p.mean(axis=1),
            axis=0
        ) * 100

        p.columns = [
            f"{i}월" for i in range(1, 13)
        ]

        fig = px.imshow(
            p,
            text_auto=".0f",
            aspect="auto",
            color_continuous_scale=[
                "#2563EB",
                "#FFFFFF",
                "#DC2626"
            ],
            color_continuous_midpoint=100,
            height=max(
                400,
                len(foods) * 45 + 150
            ),
            title="식재료별 월별 상대 가격 수준"
        )

        chart(fig)

        st.markdown("""
        ### 히트맵 해석 방법

        - 파란색: 평균보다 저렴한 시기
        - 흰색: 평균과 비슷한 시기
        - 빨간색: 평균보다 비싼 시기
        - 100: 해당 식재료의 월평균 가격
        - 80: 평균보다 20% 저렴
        - 120: 평균보다 20% 비쌈
        - 빈칸: 해당 월의 기록 없음
        """)

    else:

        st.warning("식재료를 선택하세요.")

# ==========================================
# 13. 머신러닝 가격 예측 및 성능 비교
# ==========================================

elif menu in [
    "머신러닝 가격 예측",
    "알고리즘 성능 비교"
]:

    with st.spinner(
        "머신러닝 모델 학습 중..."
    ):

        models, perf, preds, na, nb = train(df)

    # --------------------------------------
    # 머신러닝 가격 예측
    # --------------------------------------

    if menu == "머신러닝 가격 예측":

        d = choose("predict")

        month = st.slider(
            "추정할 월",
            1,
            12,
            6
        )

        x = d[FEATURES].iloc[[0]].copy()
        x["월"] = month

        result = pd.DataFrame({

            "알고리즘": NAMES,

            "예측가격": [
                predict(models[n], x)[0]
                for n in NAMES
            ]
        })

        for c, row in zip(
            st.columns(3),
            result.itertuples(index=False)
        ):

            c.metric(
                row.알고리즘,
                f"{row.예측가격:,.0f}원"
            )

        fig = px.bar(
            result,
            x="알고리즘",
            y="예측가격",
            color="알고리즘",
            color_discrete_map=COLORS,
            text_auto=",.0f",
            title="알고리즘별 가격 예측 결과"
        )

        actual = d.loc[
            d["월"] == month,
            PRICE
        ]

        if not actual.empty:

            v = actual.mean()

            fig.add_hline(
                y=v,
                line_dash="dash",
                line_color="red",
                annotation_text="실제 기록"
            )

            result["절대오차"] = abs(
                result["예측가격"] - v
            )

            st.write(
                f"실제 기록 가격: {v:,.0f}원"
            )

        chart(fig)
        table(result)

        best = perf.loc[
            perf["MAE"].idxmin(),
            "알고리즘"
        ]

        price = result.loc[
            result["알고리즘"] == best,
            "예측가격"
        ].iloc[0]

        st.success(
            f"평가 MAE 기준 최저 오차 모델: {best}"
        )

        st.subheader("식재료 구매 비용 계산기")

        qty = st.number_input(
            f"구매 수량 ({d.iloc[0]['판매단위']} 기준)",
            1,
            10000,
            1
        )

        st.metric(
            "예상 구매 비용",
            f"{price * qty:,.0f}원"
        )

        st.caption(
            "실제 기록이 학습에 포함됐을 수 있으며 "
            "이 화면은 독립적인 성능 평가가 아닙니다."
        )

    # --------------------------------------
    # 알고리즘 성능 비교
    # --------------------------------------

    else:

        st.write(
            f"학습 데이터: {na}행 / "
            f"평가 데이터: {nb}행 "
            "(80:20 무작위 분리)"
        )

        table(perf)

        metric = st.radio(
            "평가 지표",
            ["MAE", "RMSE", "R²"],
            horizontal=True
        )

        fig = px.bar(
            perf,
            x="알고리즘",
            y=metric,
            color="알고리즘",
            color_discrete_map=COLORS,
            text_auto=".3f",
            title=f"알고리즘별 {metric} 비교"
        )

        chart(fig)

        if metric == "R²":

            best = perf.loc[
                perf[metric].idxmax(),
                "알고리즘"
            ]

        else:

            best = perf.loc[
                perf[metric].idxmin(),
                "알고리즘"
            ]

        st.success(
            f"{metric} 기준 가장 우수한 "
            f"알고리즘은 {best}입니다."
        )

        st.subheader(
            "실제 가격과 예측 가격 비교"
        )

        name = st.selectbox(
            "산점도 알고리즘",
            NAMES
        )

        fig = px.scatter(
            preds,
            x="실제 가격",
            y=name,
            labels={
                name: "예측 가격"
            },
            title=f"{name} 예측 성능"
        )

        lim = max(
            preds["실제 가격"].max(),
            preds[name].max()
        )

        fig.add_trace(
            go.Scatter(
                x=[0, lim],
                y=[0, lim],
                mode="lines",
                name="완벽한 예측",
                line=dict(
                    dash="dash",
                    color="red"
                )
            )
        )

        chart(fig)

        st.caption(
            "점이 빨간색 대각선에 가까울수록 "
            "실제 가격과 예측 가격의 차이가 작습니다."
        )

        st.subheader("평가 지표 설명")

        st.markdown("""
        **MAE (평균 절대 오차)**

        실제값과 예측값의 차이를 절댓값으로
        계산한 후 평균을 구합니다.
        값이 낮을수록 좋습니다.

        **RMSE (평균 제곱근 오차)**

        오차를 제곱하여 평균을 구하고
        제곱근을 계산합니다.
        큰 오차에 민감하며 낮을수록 좋습니다.

        **R² (결정계수)**

        실제 가격의 변동을 모델이 얼마나
        잘 설명하는지 나타냅니다.
        1에 가까울수록 좋으며 음수도 가능합니다.
        """)

        st.latex(
            r"MAE=\frac{1}{n}\sum_{i=1}^{n}"
            r"|y_i-\hat{y}_i|"
        )

        st.latex(
            r"RMSE=\sqrt{\frac{1}{n}"
            r"\sum_{i=1}^{n}(y_i-\hat{y}_i)^2}"
        )

        st.latex(
            r"R^2=1-\frac{\sum(y_i-\hat{y}_i)^2}"
            r"{\sum(y_i-\bar{y})^2}"
        )

        st.subheader(
            "머신러닝 알고리즘 작동 원리"
        )

        with st.expander(
            "① 선형 회귀 (Linear Regression)",
            expanded=True
        ):

            st.markdown("""
            선형 회귀는 입력 변수와 결과값 사이의
            선형 관계를 학습하는 알고리즘입니다.

            식재료의 종류, 월, 등급, 판매 단위 등의
            정보를 이용하여 가격을 추정합니다.

            **장점**

            - 학습 속도가 빠릅니다.
            - 작동 원리를 이해하기 쉽습니다.
            - 결과를 설명하기 쉽습니다.

            **단점**

            - 복잡한 비선형 관계에 약합니다.
            """)

            st.latex(
                r"y=b+w_1x_1+w_2x_2+\cdots+w_nx_n"
            )

        with st.expander(
            "② 랜덤 포레스트 (Random Forest)",
            expanded=True
        ):

            st.markdown("""
            랜덤 포레스트는 여러 개의 결정 트리를
            학습시킨 후 각각의 예측 결과를
            평균 내는 알고리즘입니다.

            이 프로그램에서는 150개의
            결정 트리를 사용합니다.

            **장점**

            - 복잡한 데이터 관계를 학습합니다.
            - 단일 결정 트리보다 과적합을 줄일 수 있습니다.

            **단점**

            - 학습 시간이 길어질 수 있습니다.
            - 개별 예측 결과의 설명이 어렵습니다.
            """)

        with st.expander(
            "③ 그래디언트 부스팅 (Gradient Boosting)",
            expanded=True
        ):

            st.markdown("""
            그래디언트 부스팅은 여러 결정 트리를
            순차적으로 학습시키는 알고리즘입니다.

            이전 모델의 예측 오차를 다음 모델이
            보완하는 과정을 반복합니다.

            이 프로그램에서는 150단계의
            트리 학습을 사용합니다.

            **장점**

            - 복잡한 비선형 관계를 학습합니다.
            - 예측 오차를 단계적으로 줄일 수 있습니다.

            **단점**

            - 학습 시간이 길어질 수 있습니다.
            - 설정에 따라 과적합이 발생할 수 있습니다.
            """)

        st.download_button(
            "성능 CSV 다운로드",
            perf.to_csv(
                index=False
            ).encode("utf-8-sig"),
            "model_performance.csv",
            "text/csv"
        )

        st.caption(
            "무작위 분리 결과는 미래 연도 "
            "예측 성능을 의미하지 않습니다."
        )

# ==========================================
# 14. 메뉴 원가 및 판매가격 계산기
# ==========================================

elif menu == "메뉴 원가 및 판매가격":

    st.markdown("""
    여러 식재료의 사용량을 입력하여
    메뉴의 총 식재료 원가와
    목표 판매가격을 계산합니다.
    """)

    name = st.text_input(
        "메뉴 이름",
        "나의 메뉴"
    )

    month = st.selectbox(
        "가격 기준 월",
        sorted(df["월"].unique())
    )

    d = df[df["월"] == month]

    if "recipe" not in st.session_state:

        st.session_state.recipe = []

    if st.session_state.get("recipe_month") != month:

        st.session_state.recipe = []
        st.session_state.recipe_month = month

    selected = choose(
        "recipe",
        d
    )

    row = selected.iloc[0]

    unit = row["비교단위"]

    input_unit = (
        "g" if unit == "kg" else unit
    )

    qty = st.number_input(
        f"사용량 ({input_unit})",
        min_value=0.01,
        value=100.0 if unit == "kg" else 1.0,
        step=1.0
    )

    cost = (
        row["환산가격"] * qty
        / (1000 if unit == "kg" else 1)
    )

    st.write(
        f"기록 기준 사용 비용: {cost:,.0f}원"
    )

    if st.button("식재료 추가"):

        st.session_state.recipe.append({

            "식재료": row["식재료"],
            "등급": row["등급명"],
            "기준 판매단위": row["판매단위"],
            "사용량": qty,
            "단위": input_unit,
            "비용": float(cost)
        })

    if st.button("전체 초기화"):

        st.session_state.recipe = []

    if st.session_state.recipe:

        recipe = pd.DataFrame(
            st.session_state.recipe
        )

        st.subheader("선택한 식재료")

        table(recipe)

        if st.button("마지막 식재료 삭제"):

            st.session_state.recipe.pop()
            st.rerun()

        portions = st.number_input(
            "완성 분량(인분)",
            1,
            10000,
            1
        )

        rate = st.slider(
            "목표 식재료 원가율 (%)",
            10,
            80,
            30
        )

        total = recipe["비용"].sum()

        per = total / portions

        selling = np.ceil(
            per / (rate / 100) / 100
        ) * 100

        items = [

            (
                "총 식재료 원가",
                total
            ),

            (
                "1인분 원가",
                per
            ),

            (
                "1인분 목표 판매가격",
                selling
            )
        ]

        for c, (label, v) in zip(
            st.columns(3),
            items
        ):

            c.metric(
                label,
                f"{v:,.0f}원"
            )

        cost_data = recipe.groupby(
            "식재료",
            as_index=False
        )["비용"].sum()

        fig = px.bar(
            cost_data,
            x="식재료",
            y="비용",
            color="식재료",
            title="식재료별 원가 구성"
        )

        chart(fig)

        fig = px.pie(
            cost_data,
            names="식재료",
            values="비용",
            title="식재료별 원가 비율",
            hole=0.35
        )

        chart(fig)

        st.subheader("판매가격 계산 원리")

        st.latex(
            r"\text{판매가격}="
            r"\frac{\text{1인분 식재료 원가}}"
            r"{\text{목표 원가율}}"
        )

        st.info(
            f"{name}의 1인분 식재료 원가는 "
            f"{per:,.0f}원이며, "
            f"목표 원가율 {rate}%를 적용한 "
            f"목표 판매가격은 "
            f"{selling:,.0f}원입니다."
        )

        st.download_button(
            "메뉴 원가 CSV 다운로드",
            recipe.assign(
                메뉴=name,
                기준월=month
            ).to_csv(
                index=False
            ).encode("utf-8-sig"),
            "recipe_cost.csv",
            "text/csv"
        )

    st.caption(
        "월 변경 시 식재료 목록이 초기화됩니다. "
        "손질 손실, 인건비, 임대료, 세금 등은 "
        "포함하지 않습니다. 판매가격은 "
        "100원 단위로 올림한 목표값입니다."
    )

# ==========================================
# 15. 식재료 가격 변동률 순위
# ==========================================

elif menu == "가격 변동률 순위":

    st.markdown("""
    식재료의 최고가와 최저가를 비교하여
    가격 변동 폭이 큰 식재료를 분석합니다.
    """)

    grade = st.selectbox(
        "등급",
        sorted(df["등급명"].unique())
    )

    unit = st.selectbox(
        "단위",
        sorted(df["비교단위"].unique())
    )

    n = st.slider(
        "표시 개수",
        1,
        30,
        10
    )

    min_months = st.slider(
        "최소 기록 월 수",
        2,
        12,
        6
    )

    d = df[
        (df["등급명"] == grade)
        & (df["비교단위"] == unit)
    ]

    rows = []

    for (food, pack), g in d.groupby(
        ["식재료", "판매단위"]
    ):

        m = g.groupby("월")[PRICE].mean()

        if len(m) >= min_months:

            rows.append({

                "식재료": food + " / " + pack,

                "최저가 월": int(m.idxmin()),

                "최고가 월": int(m.idxmax()),

                "기록 월 수": len(m),

                "변동률(%)": (
                    m.max() / m.min() - 1
                ) * 100
            })

    if rows:

        r = (
            pd.DataFrame(rows)
            .sort_values(
                "변동률(%)",
                ascending=False
            )
            .head(n)
        )

        fig = px.bar(
            r,
            x="식재료",
            y="변동률(%)",
            color="변동률(%)",
            color_continuous_scale="Reds",
            title="식재료 가격 변동률 순위"
        )

        chart(fig)
        table(r)

        top = r.iloc[0]

        st.info(
            f"가격 변동률이 가장 높은 식재료는 "
            f"{top['식재료']}이며, "
            f"변동률은 "
            f"{top['변동률(%)']:.1f}%입니다."
        )

    else:

        st.warning(
            "조건에 맞는 데이터가 없습니다."
        )

    st.latex(
        r"\text{가격 변동률}="
        r"\frac{\text{최고가}-\text{최저가}}"
        r"{\text{최저가}}\times100"
    )

    st.caption(
        "동일 판매단위를 기준으로 비교하며 "
        "월간 수익률이나 표준편차가 아닙니다."
    )

# ==========================================
# 16. 5-Fold 교차 검증
# ==========================================

elif menu == "5-Fold 교차 검증":

    st.markdown("""
    ### 5-Fold 교차 검증이란?

    전체 데이터를 5개의 그룹으로 나누고,
    4개 그룹은 학습에 사용하며
    나머지 1개 그룹은 평가에 사용합니다.

    평가 그룹을 바꾸면서 총 5번 반복하고,
    각 알고리즘의 평균 성능을 비교합니다.

    세 가지 알고리즘이 각각 5번씩 학습하므로
    총 15회의 학습과 평가를 진행합니다.
    """)

    if st.button("교차 검증 실행"):

        with st.spinner(
            "15개 모델 학습 중..."
        ):

            st.session_state.cv = cv_results(df)

    if "cv" in st.session_state:

        r = st.session_state.cv

        summary = r.groupby(
            "알고리즘"
        )[
            ["MAE", "RMSE", "R²"]
        ].agg(
            ["mean", "std"]
        )

        summary.columns = [

            f"{a} {'평균' if b == 'mean' else '표준편차'}"

            for a, b in summary.columns
        ]

        st.subheader("교차 검증 평균 성능")

        table(summary.reset_index())

        st.subheader("회차별 성능")

        table(r)

        metric = st.radio(
            "평가 지표",
            ["MAE", "RMSE", "R²"],
            horizontal=True
        )

        fig = px.box(
            r,
            x="알고리즘",
            y=metric,
            color="알고리즘",
            color_discrete_map=COLORS,
            points="all",
            title=f"알고리즘별 {metric} 분포"
        )

        chart(fig)

        mean_data = (
            r.groupby(
                "알고리즘",
                as_index=False
            )[metric].mean()
        )

        fig = px.bar(
            mean_data,
            x="알고리즘",
            y=metric,
            color="알고리즘",
            color_discrete_map=COLORS,
            text_auto=".3f",
            title=f"교차 검증 평균 {metric} 비교"
        )

        chart(fig)

        if metric == "R²":

            best = summary[
                metric + " 평균"
            ].idxmax()

        else:

            best = summary[
                metric + " 평균"
            ].idxmin()

        st.success(
            f"교차 검증 평균 {metric} 기준 "
            f"우수 모델은 {best}입니다."
        )

        st.markdown("""
        **교차 검증의 장점**

        - 한 번의 데이터 분리에 의존하지 않습니다.
        - 알고리즘의 평균 성능을 비교할 수 있습니다.
        - 표준편차를 통해 성능의 안정성을 확인합니다.
        """)

        st.download_button(
            "교차 검증 CSV 다운로드",
            r.to_csv(
                index=False
            ).encode("utf-8-sig"),
            "cross_validation.csv",
            "text/csv"
        )

    st.caption(
        "같은 식재료의 다른 월이 학습과 평가에 "
        "함께 포함될 수 있습니다. 미래 가격 또는 "
        "새로운 품목의 성능을 검증한 것은 아닙니다."
    )

# ==========================================
# 17. 데이터 정보
# ==========================================

else:

    st.subheader("데이터 전처리 결과")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "원본 데이터",
        f"{len(raw):,}행"
    )

    c2.metric(
        "결측값",
        f"{raw.isna().sum().sum():,}개"
    )

    c3.metric(
        "완전 중복",
        f"{raw.duplicated().sum():,}행"
    )

    c4.metric(
        "전처리 후 데이터",
        f"{len(df):,}행"
    )

    st.subheader("원본 데이터")

    table(raw)

    st.subheader("전처리된 데이터")

    table(df)

    st.download_button(
        "전처리 CSV 다운로드",
        df.to_csv(
            index=False
        ).encode("utf-8-sig"),
        "food_price_analysis.csv",
        "text/csv"
    )

    st.markdown("""
    ### 데이터 출처

    - 제공기관: 한국농수산식품유통공사
    - 데이터명: 월별 농축수산물 소매가격 정보
    - 출처: 공공데이터포털

    ### 사용한 라이브러리

    - Pandas: 데이터 분석 및 전처리
    - NumPy: 수치 계산
    - Plotly: 데이터 시각화
    - Scikit-learn: 머신러닝 학습 및 평가
    - Streamlit: 웹 프로그램 제작

    ### 데이터 분석 과정

    1. CSV 파일 불러오기
    2. 결측값 및 완전 중복 데이터 제거
    3. 숫자 및 월 데이터 변환
    4. 동일 조건 가격 평균 집계
    5. 식재료 판매 단위 환산
    6. 데이터 시각화
    7. 머신러닝 모델 학습
    8. 알고리즘 성능 비교
    9. 5-Fold 교차 검증
    10. 메뉴 원가 및 판매가격 계산

    ### 분석의 한계

    원본 데이터의 실제 조사 연도가
    명확하게 구분되지 않으므로
    동일 조건의 월별 가격을 평균으로 집계했습니다.

    기상, 생산량, 물류비 등 외부 요인은
    분석에 포함되지 않았습니다.

    머신러닝 결과는 기록에 기반한 가격 추정이며
    미래 가격을 보장하지 않습니다.
    """)

    st.link_button(
        "공공데이터포털 바로가기",
        "https://www.data.go.kr/"
    )

# ==========================================
# 18. 하단 정보
# ==========================================

st.divider()

st.caption(
    "농축수산물 가격 분석 및 외식업 원가 관리 시스템"
    " | Pandas · NumPy · Plotly · "
    "Scikit-learn · Streamlit"
)
