import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor
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
    page_title="농축수산물 가격 분석",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ 농축수산물 가격 분석 및 예측 시스템")

st.markdown("""
농축수산물의 가격 변화를 분석하고
머신러닝 알고리즘을 활용하여
식재료 가격을 추정하는 프로그램입니다.

외식업의 효율적인 식재료 구매와
원가 관리를 목적으로 제작되었습니다.
""")

# ==========================================
# 2. CSV 파일 불러오기
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

@st.cache_data
def load_data():

    files = sorted(
        BASE_DIR.glob("*농축수산물*소매가격*.csv")
    )

    if files:
        path = files[0]
    else:
        path = BASE_DIR / "food_price.csv"

    if not path.exists():
        raise FileNotFoundError(
            "CSV 파일을 찾을 수 없습니다. "
            "pages 폴더의 상위 폴더에 "
            "CSV 파일을 넣어주세요."
        )

    for encoding in ["cp949", "utf-8-sig", "euc-kr"]:
        try:
            return pd.read_csv(
                path,
                encoding=encoding
            )
        except UnicodeError:
            continue

    raise ValueError("CSV 인코딩 오류입니다.")

try:
    raw_df = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()

df = raw_df.copy()
df.columns = df.columns.str.strip()

required = [
    "가격등록연월",
    "품목명",
    "품종명",
    "평균가격",
    "등급명",
    "유통단계별무게",
    "유통단계별단위"
]

if not set(required).issubset(df.columns):
    st.error("CSV 파일의 열 이름을 확인해주세요.")
    st.stop()

# ==========================================
# 3. 데이터 전처리
# ==========================================

missing_count = int(df[required].isna().sum().sum())
duplicate_count = int(df.duplicated().sum())

df = df.dropna(subset=required)
df = df.drop_duplicates().copy()

text_columns = [
    "가격등록연월",
    "품목명",
    "품종명",
    "등급명",
    "유통단계별단위"
]

for col in text_columns:
    df[col] = df[col].astype(str).str.strip()

df["평균가격"] = pd.to_numeric(
    df["평균가격"].astype(str).str.replace(",", ""),
    errors="coerce"
)

df["유통단계별무게"] = pd.to_numeric(
    df["유통단계별무게"],
    errors="coerce"
)

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

df["월"] = (
    df["가격등록연월"]
    .str[:3]
    .str.title()
    .map(month_map)
)

df = df.dropna(
    subset=[
        "평균가격",
        "유통단계별무게",
        "월"
    ]
)

df = df[
    (df["평균가격"] > 0)
    & (df["유통단계별무게"] > 0)
].copy()

if df.empty:
    st.error("분석 가능한 데이터가 없습니다.")
    st.stop()

df["월"] = df["월"].astype(int)

# 동일한 조건의 가격은 평균으로 집계

group_columns = [
    "월",
    "품목명",
    "품종명",
    "등급명",
    "유통단계별무게",
    "유통단계별단위"
]

df = (
    df.groupby(
        group_columns,
        as_index=False
    )["평균가격"].mean()
)

df["판매단위"] = (
    df["유통단계별무게"].map(
        lambda x: f"{x:g}"
    )
    + df["유통단계별단위"]
)

df["식재료"] = (
    df["품목명"]
    + " - "
    + df["품종명"]
)

# ==========================================
# 4. 가격 단위 환산
# ==========================================

df["비교단위"] = df["유통단계별단위"]

df["환산가격"] = (
    df["평균가격"]
    / df["유통단계별무게"]
)

gram_mask = df["유통단계별단위"] == "g"

df.loc[gram_mask, "환산가격"] *= 1000
df.loc[gram_mask, "비교단위"] = "kg"

# ==========================================
# 5. 데이터 요약
# ==========================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "원본 데이터",
    f"{len(raw_df):,}개"
)

c2.metric(
    "식재료 품목",
    f"{df['품목명'].nunique()}종"
)

c3.metric(
    "세부 품종",
    f"{df['식재료'].nunique()}종"
)

c4.metric(
    "분석 가능 월",
    f"{df['월'].nunique()}개월"
)

st.divider()

# ==========================================
# 6. 분석 메뉴
# ==========================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 월별 가격 분석",
    "📊 품목별 가격 비교",
    "⚖️ 등급별 가격 비교",
    "🌡️ 가격 히트맵",
    "🤖 머신러닝 가격 예측",
    "🏆 알고리즘 성능 비교",
    "📋 데이터 정보"
])

# ==========================================
# 7. 공통 그래프 설정
# ==========================================

def month_axis(fig):

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=[
            f"{i}월" for i in range(1, 13)
        ]
    )

    fig.update_yaxes(tickformat=",.0f")

    return fig

# ==========================================
# 8. 식재료 선택 기능
# ==========================================

def select_food(key):

    c1, c2, c3, c4 = st.columns(4)

    item = c1.selectbox(
        "품목 선택",
        sorted(df["품목명"].unique()),
        key=f"{key}_item"
    )

    selected = df[
        df["품목명"] == item
    ]

    variety = c2.selectbox(
        "품종 선택",
        sorted(selected["품종명"].unique()),
        key=f"{key}_variety"
    )

    selected = selected[
        selected["품종명"] == variety
    ]

    grade = c3.selectbox(
        "등급 선택",
        sorted(selected["등급명"].unique()),
        key=f"{key}_grade"
    )

    selected = selected[
        selected["등급명"] == grade
    ]

    unit = c4.selectbox(
        "판매 단위 선택",
        sorted(selected["판매단위"].unique()),
        key=f"{key}_unit"
    )

    selected = selected[
        selected["판매단위"] == unit
    ]

    return selected, item, variety, grade, unit

# ==========================================
# 9. 월별 가격 분석
# ==========================================

with tab1:

    st.header("월별 식재료 가격 변화")

    selected, item, variety, grade, unit = (
        select_food("monthly")
    )

    monthly = (
        selected.groupby(
            "월",
            as_index=False
        )["평균가격"].mean()
        .sort_values("월")
    )

    fig = px.line(
        monthly,
        x="월",
        y="평균가격",
        markers=True,
        title=f"{item} 월별 가격 변화",
        labels={
            "월": "월",
            "평균가격": "평균가격(원)"
        }
    )

    fig.update_traces(
        line=dict(
            color="#2563EB",
            width=3
        ),
        marker=dict(size=9)
    )

    # 평균가격 기준선

    avg_price = monthly["평균가격"].mean()

    fig.add_hline(
        y=avg_price,
        line_dash="dash",
        line_color="gray",
        annotation_text="월평균 가격"
    )

    fig = month_axis(fig)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    min_row = monthly.loc[
        monthly["평균가격"].idxmin()
    ]

    max_row = monthly.loc[
        monthly["평균가격"].idxmax()
    ]

    min_price = min_row["평균가격"]
    max_price = max_row["평균가격"]

    difference = max_price - min_price

    change_rate = (
        difference / min_price * 100
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        f"최저가 ({int(min_row['월'])}월)",
        f"{min_price:,.0f}원"
    )

    c2.metric(
        f"최고가 ({int(max_row['월'])}월)",
        f"{max_price:,.0f}원"
    )

    c3.metric(
        "월평균 가격",
        f"{avg_price:,.0f}원"
    )

    c4.metric(
        "최고·최저 가격 차이",
        f"{difference:,.0f}원"
    )

    st.subheader("자동 분석 결과")

    st.info(
        f"{item}의 기록상 최저가 월은 "
        f"{int(min_row['월'])}월이며, "
        f"{unit}당 평균가격은 "
        f"{min_price:,.0f}원입니다. "
        f"최고가는 최저가보다 "
        f"{change_rate:.1f}% 높습니다."
    )

    st.dataframe(
        monthly,
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# 10. 품목별 가격 비교
# ==========================================

with tab2:

    st.header("식재료별 가격 비교")

    c1, c2, c3 = st.columns(3)

    month2 = c1.selectbox(
        "월 선택",
        sorted(df["월"].unique()),
        format_func=lambda x: f"{x}월",
        key="month2"
    )

    unit2 = c2.selectbox(
        "비교 단위",
        sorted(df["비교단위"].unique()),
        key="unit2"
    )

    grade2 = c3.selectbox(
        "등급 선택",
        sorted(df["등급명"].unique()),
        key="grade2"
    )

    compare = df[
        (df["월"] == month2)
        & (df["비교단위"] == unit2)
        & (df["등급명"] == grade2)
    ]

    if compare.empty:

        st.warning("해당 조건의 데이터가 없습니다.")

    else:

        compare = (
            compare.groupby(
                "식재료",
                as_index=False
            )["환산가격"].mean()
        )

        top_n = st.slider(
            "표시할 식재료 개수",
            1,
            30,
            10,
            key="top_n"
        )

        order = st.radio(
            "정렬 방식",
            ["가격 높은 순", "가격 낮은 순"],
            horizontal=True
        )

        compare = (
            compare.sort_values(
                "환산가격",
                ascending=(
                    order == "가격 낮은 순"
                )
            ).head(top_n)
        )

        fig = px.bar(
            compare,
            x="식재료",
            y="환산가격",
            color="환산가격",
            color_continuous_scale="Blues",
            title=f"{month2}월 식재료 가격 비교",
            labels={
                "식재료": "식재료",
                "환산가격": f"1{unit2}당 가격(원)"
            }
        )

        fig.update_layout(
            coloraxis_showscale=False
        )

        fig.update_yaxes(tickformat=",.0f")

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            compare,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "g과 kg은 1kg 기준으로 환산하며 "
            "개·마리·포기 등은 동일한 단위끼리 비교합니다."
        )

# ==========================================
# 11. 등급별 가격 비교
# ==========================================

with tab3:

    st.header("등급별 식재료 가격 비교")

    item3 = st.selectbox(
        "품목 선택",
        sorted(df["품목명"].unique()),
        key="item3"
    )

    grade_data = df[
        df["품목명"] == item3
    ]

    variety3 = st.selectbox(
        "품종 선택",
        sorted(grade_data["품종명"].unique()),
        key="variety3"
    )

    grade_data = grade_data[
        grade_data["품종명"] == variety3
    ]

    unit3 = st.selectbox(
        "판매 단위 선택",
        sorted(grade_data["판매단위"].unique()),
        key="unit3"
    )

    grade_data = grade_data[
        grade_data["판매단위"] == unit3
    ]

    grade_month = (
        grade_data.groupby(
            ["월", "등급명"],
            as_index=False
        )["평균가격"].mean()
    )

    if grade_month["등급명"].nunique() < 2:

        st.warning(
            "선택한 식재료의 등급이 한 종류뿐입니다."
        )

    fig = px.bar(
        grade_month,
        x="월",
        y="평균가격",
        color="등급명",
        barmode="group",
        color_discrete_map={
            "상품": "#2563EB",
            "중품": "#F97316"
        },
        title=f"{item3} 등급별 가격 비교",
        labels={
            "월": "월",
            "평균가격": "평균가격(원)",
            "등급명": "등급"
        }
    )

    fig = month_axis(fig)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        grade_month,
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# 12. 가격 히트맵
# ==========================================

with tab4:

    st.header("식재료별 월별 가격 히트맵")

    heat_grade = st.selectbox(
        "등급 선택",
        sorted(df["등급명"].unique()),
        key="heat_grade"
    )

    heat_unit = st.selectbox(
        "비교 단위 선택",
        sorted(df["비교단위"].unique()),
        key="heat_unit"
    )

    heat = df[
        (df["등급명"] == heat_grade)
        & (df["비교단위"] == heat_unit)
    ].copy()

    if heat.empty:

        st.warning("분석 가능한 데이터가 없습니다.")

    else:

        options = sorted(
            heat["식재료"].unique()
        )

        foods = st.multiselect(
            "비교할 식재료 선택",
            options,
            default=options[:8]
        )

        if foods:

            heat = heat[
                heat["식재료"].isin(foods)
            ]

            pivot = heat.pivot_table(
                index="식재료",
                columns="월",
                values="환산가격",
                aggfunc="mean"
            )

            pivot = pivot.reindex(
                columns=range(1, 13)
            )

            relative = pivot.div(
                pivot.mean(axis=1),
                axis=0
            ) * 100

            relative.columns = [
                f"{i}월" for i in range(1, 13)
            ]

            fig = px.imshow(
                relative,
                text_auto=".0f",
                aspect="auto",
                color_continuous_scale=[
                    "#2563EB",
                    "#FFFFFF",
                    "#DC2626"
                ],
                color_continuous_midpoint=100,
                title="월별 상대 가격 수준",
                labels={
                    "x": "월",
                    "y": "식재료",
                    "color": "가격지수"
                }
            )

            fig.update_layout(
                height=max(
                    400,
                    len(foods) * 45 + 150
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.markdown("""
            ### 히트맵 해석

            - 🔵 파란색: 평균보다 저렴한 가격
            - ⚪ 흰색: 평균과 비슷한 가격
            - 🔴 빨간색: 평균보다 비싼 가격
            - 100: 해당 식재료의 월평균 가격
            - 80: 평균보다 20% 저렴
            - 120: 평균보다 20% 비쌈
            - 빈칸: 해당 월의 데이터 없음
            """)

        else:

            st.warning("식재료를 선택해주세요.")

# ==========================================
# 13. 머신러닝 데이터 설정
# ==========================================

categorical_features = [
    "품목명",
    "품종명",
    "등급명",
    "유통단계별단위"
]

numeric_features = [
    "월",
    "유통단계별무게"
]

features = (
    categorical_features
    + numeric_features
)

# ==========================================
# 14. 머신러닝 모델 학습
# ==========================================

@st.cache_resource
def train_models(data):

    X = data[features].copy()
    y = data["평균가격"].copy()

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )
    )

    model_list = {
        "선형 회귀": LinearRegression(),

        "랜덤 포레스트": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1
        ),

        "그래디언트 부스팅":
            GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=3,
                random_state=42
            )
    }

    trained_models = {}
    results = []

    predictions = pd.DataFrame({
        "실제 가격": y_test.to_numpy()
    })

    for name, model in model_list.items():

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "category",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False
                    ),
                    categorical_features
                ),
                (
                    "numeric",
                    "passthrough",
                    numeric_features
                )
            ]
        )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("model", model)
        ])

        pipeline.fit(
            X_train,
            y_train
        )

        pred = pipeline.predict(X_test)

        # 가격은 음수가 될 수 없으므로 보정
        pred = np.maximum(pred, 0)

        mae = mean_absolute_error(
            y_test,
            pred
        )

        rmse = np.sqrt(
            mean_squared_error(
                y_test,
                pred
            )
        )

        r2 = r2_score(
            y_test,
            pred
        )

        trained_models[name] = pipeline

        predictions[name] = pred

        results.append({
            "알고리즘": name,
            "MAE": mae,
            "RMSE": rmse,
            "R²": r2
        })

    result_df = pd.DataFrame(results)

    return (
        trained_models,
        result_df,
        predictions,
        len(X_train),
        len(X_test)
    )

try:

    with st.spinner(
        "머신러닝 알고리즘 3개를 학습하고 있습니다..."
    ):

        (
            models,
            performance,
            test_predictions,
            train_count,
            test_count
        ) = train_models(df)

except Exception as e:

    st.error(f"머신러닝 학습 오류: {e}")
    st.stop()

# ==========================================
# 15. 머신러닝 가격 예측
# ==========================================

with tab5:

    st.header("머신러닝 식재료 가격 예측")

    st.markdown("""
    사용자가 선택한 식재료의 조건을 바탕으로
    세 가지 머신러닝 알고리즘이
    평균가격을 각각 추정합니다.
    """)

    selected5, item5, variety5, grade5, unit5 = (
        select_food("predict")
    )

    month5 = st.slider(
        "가격을 추정할 월",
        1,
        12,
        6,
        key="predict_month"
    )

    sample = selected5.iloc[0]

    input_data = pd.DataFrame([{
        "품목명": item5,
        "품종명": variety5,
        "등급명": grade5,
        "유통단계별단위":
            sample["유통단계별단위"],
        "유통단계별무게":
            sample["유통단계별무게"],
        "월": month5
    }])

    prediction_results = []

    for name, model in models.items():

        price = float(
            model.predict(input_data)[0]
        )

        price = max(price, 0)

        prediction_results.append({
            "알고리즘": name,
            "예측가격": price
        })

    prediction_df = pd.DataFrame(
        prediction_results
    )

    c1, c2, c3 = st.columns(3)

    for col, result in zip(
        [c1, c2, c3],
        prediction_results
    ):

        col.metric(
            result["알고리즘"],
            f"{result['예측가격']:,.0f}원"
        )

    # 알고리즘별 예측 결과 그래프

    fig = px.bar(
        prediction_df,
        x="알고리즘",
        y="예측가격",
        color="알고리즘",
        color_discrete_map={
            "선형 회귀": "#2563EB",
            "랜덤 포레스트": "#16A34A",
            "그래디언트 부스팅": "#F97316"
        },
        text_auto=",.0f",
        title="알고리즘별 가격 예측 결과",
        labels={
            "예측가격": "예측가격(원)"
        }
    )

    # 실제 기록이 있는 경우 기준선 표시

    actual_data = selected5[
        selected5["월"] == month5
    ]

    if not actual_data.empty:

        actual_price = (
            actual_data["평균가격"].mean()
        )

        fig.add_hline(
            y=actual_price,
            line_dash="dash",
            line_color="red",
            annotation_text="실제 기록 가격"
        )

        st.success(
            f"{month5}월 실제 기록 가격: "
            f"{actual_price:,.0f}원"
        )

        prediction_df["절대오차"] = abs(
            prediction_df["예측가격"]
            - actual_price
        )

    else:

        st.warning(
            "선택한 월의 실제 기록이 없습니다. "
            "추정 결과만 표시합니다."
        )

    fig.update_yaxes(tickformat=",.0f")
    fig.update_layout(showlegend=False)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        prediction_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    best_model = performance.loc[
        performance["MAE"].idxmin(),
        "알고리즘"
    ]

    best_price = prediction_df.loc[
        prediction_df["알고리즘"] == best_model,
        "예측가격"
    ].iloc[0]

    st.subheader("추천 알고리즘 및 추정 가격")

    st.success(
        f"평가 데이터에서 MAE가 가장 낮은 "
        f"알고리즘은 {best_model}입니다. "
        f"해당 알고리즘의 {item5} "
        f"{unit5}당 추정 가격은 "
        f"{best_price:,.0f}원입니다."
    )

    st.caption(
        "선택한 조건의 실제 기록이 학습 데이터에 "
        "포함되었을 수 있습니다. 이 화면은 모델의 "
        "사용 예시이며 독립적인 성능 평가는 "
        "알고리즘 성능 비교 메뉴에서 확인할 수 있습니다."
    )

    st.divider()

    # 식재료 구매 비용 계산기

    st.subheader("식재료 구매 비용 계산기")

    quantity = st.number_input(
        f"구매할 판매 단위 수량 ({unit5} 기준)",
        min_value=1,
        max_value=10000,
        value=1,
        step=1
    )

    total_price = best_price * quantity

    st.metric(
        "예상 구매 비용",
        f"{total_price:,.0f}원"
    )

    st.caption(
        "머신러닝 추정 가격을 이용한 계산이며 "
        "실제 구매 가격과 차이가 발생할 수 있습니다."
    )

# ==========================================
# 16. 알고리즘 성능 비교
# ==========================================

with tab6:

    st.header("머신러닝 알고리즘 성능 비교")

    c1, c2 = st.columns(2)

    c1.metric(
        "학습 데이터 (약 80%)",
        f"{train_count:,}개"
    )

    c2.metric(
        "평가 데이터 (약 20%)",
        f"{test_count:,}개"
    )

    st.markdown("""
    동일한 학습 데이터와 평가 데이터를 사용하여
    세 가지 알고리즘의 성능을 비교합니다.
    """)

    st.dataframe(
        performance.round(4),
        use_container_width=True,
        hide_index=True
    )

    metric = st.radio(
        "비교할 평가 지표",
        ["MAE", "RMSE", "R²"],
        horizontal=True
    )

    if metric == "R²":

        best_index = performance[
            metric
        ].idxmax()

    else:

        best_index = performance[
            metric
        ].idxmin()

    best_name = performance.loc[
        best_index,
        "알고리즘"
    ]

    colors = [
        "#DC2626" if name == best_name
        else "#60A5FA"
        for name in performance["알고리즘"]
    ]

    fig = go.Figure(
        go.Bar(
            x=performance["알고리즘"],
            y=performance[metric],
            marker_color=colors,
            text=performance[metric].round(3),
            textposition="auto"
        )
    )

    fig.update_layout(
        title=f"알고리즘별 {metric} 비교",
        xaxis_title="알고리즘",
        yaxis_title=metric
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.success(
        f"{metric} 기준 가장 우수한 알고리즘은 "
        f"{best_name}입니다."
    )

    # 실제 가격과 예측 가격 산점도

    st.subheader("실제 가격과 예측 가격 비교")

    selected_model = st.selectbox(
        "확인할 알고리즘",
        list(models.keys())
    )

    scatter_df = pd.DataFrame({
        "실제 가격":
            test_predictions["실제 가격"],
        "예측 가격":
            test_predictions[selected_model]
    })

    fig = px.scatter(
        scatter_df,
        x="실제 가격",
        y="예측 가격",
        title=f"{selected_model} 예측 성능",
        opacity=0.65,
        labels={
            "실제 가격": "실제 가격(원)",
            "예측 가격": "예측 가격(원)"
        }
    )

    max_value = max(
        scatter_df["실제 가격"].max(),
        scatter_df["예측 가격"].max()
    )

    fig.add_trace(
        go.Scatter(
            x=[0, max_value],
            y=[0, max_value],
            mode="lines",
            name="완벽한 예측 기준선",
            line=dict(
                color="red",
                dash="dash"
            )
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "점이 빨간색 대각선에 가까울수록 "
        "실제 가격과 예측 가격의 차이가 작습니다."
    )

    st.divider()

    # 평가 지표 설명

    st.subheader("머신러닝 평가 지표 설명")

    st.markdown("""
    **MAE (평균 절대 오차)**

    실제 가격과 예측 가격의 차이를
    절댓값으로 계산한 후 평균을 구합니다.
    값이 작을수록 좋습니다.

    **RMSE (평균 제곱근 오차)**

    실제 가격과 예측 가격의 차이를
    제곱하여 평균을 구하고 제곱근을 계산합니다.
    큰 오차에 더 민감하며 값이 작을수록 좋습니다.

    **R² (결정계수)**

    모델이 실제 가격의 변동을
    얼마나 잘 설명하는지 나타냅니다.
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

    st.divider()

    # 알고리즘 작동 원리

    st.subheader("머신러닝 알고리즘 작동 원리")

    with st.expander(
        "① 선형 회귀 (Linear Regression)",
        expanded=True
    ):

        st.markdown("""
        선형 회귀는 입력 변수와 결과값 사이의
        선형적인 관계를 학습하는 알고리즘입니다.

        식재료의 종류, 월, 등급, 판매 단위 등의
        정보를 이용하여 가격을 추정합니다.

        **장점**

        - 작동 원리가 비교적 단순합니다.
        - 학습 속도가 빠릅니다.
        - 결과를 설명하기 쉽습니다.

        **단점**

        - 복잡한 비선형 관계를 분석하기 어렵습니다.
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
        만들어 각각의 예측 결과를 평균 내는
        머신러닝 알고리즘입니다.

        여러 트리가 서로 다른 데이터와 조건을
        학습하기 때문에 하나의 결정 트리보다
        안정적인 예측을 할 수 있습니다.

        이 프로그램에서는 200개의 결정 트리를
        사용합니다.

        **장점**

        - 복잡한 데이터 관계를 학습할 수 있습니다.
        - 단일 결정 트리보다 과적합을 줄일 수 있습니다.

        **단점**

        - 선형 회귀보다 학습 시간이 길 수 있습니다.
        - 개별 예측의 이유를 설명하기 어렵습니다.
        """)

    with st.expander(
        "③ 그래디언트 부스팅 (Gradient Boosting)",
        expanded=True
    ):

        st.markdown("""
        그래디언트 부스팅은 여러 개의 결정 트리를
        순차적으로 학습시키는 알고리즘입니다.

        첫 번째 모델이 예측한 결과의 오차를
        다음 모델이 보완하는 과정을 반복합니다.

        이 프로그램에서는 200단계의 트리 학습을
        사용합니다.

        **장점**

        - 복잡한 비선형 관계를 학습할 수 있습니다.
        - 예측 오차를 단계적으로 줄일 수 있습니다.

        **단점**

        - 학습 시간이 길어질 수 있습니다.
        - 설정에 따라 과적합이 발생할 수 있습니다.
        """)

    st.warning(
        "성능 평가는 무작위로 분리한 평가 데이터를 "
        "기준으로 합니다. 새로운 연도의 미래 가격 "
        "예측 성능을 검증한 결과는 아닙니다."
    )

# ==========================================
# 17. 데이터 정보
# ==========================================

with tab7:

    st.header("데이터 전처리 및 원본 정보")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "원본 데이터",
        f"{len(raw_df):,}개"
    )

    c2.metric(
        "결측값",
        f"{missing_count:,}개"
    )

    c3.metric(
        "완전 중복 행",
        f"{duplicate_count:,}개"
    )

    c4.metric(
        "전처리 및 집계 후",
        f"{len(df):,}개"
    )

    st.subheader("원본 데이터")

    st.dataframe(
        raw_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("전처리된 데이터")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "전처리 데이터 다운로드",
        data=df.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="food_price_analysis.csv",
        mime="text/csv"
    )

    st.download_button(
        "알고리즘 성능 결과 다운로드",
        data=performance.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="model_performance.csv",
        mime="text/csv"
    )

    st.markdown("""
    ### 데이터 출처

    - 제공기관: 한국농수산식품유통공사
    - 데이터명: 월별 농축수산물 소매가격 정보
    - 출처: 공공데이터포털
    - 원본 데이터: 2,826행, 7개 열

    ### 사용한 라이브러리

    - Pandas: 데이터 분석 및 전처리
    - NumPy: 수치 계산
    - Plotly: 데이터 시각화
    - Scikit-learn: 머신러닝 학습 및 평가
    - Streamlit: 웹 프로그램 제작

    ### 데이터 분석 과정

    1. CSV 파일 불러오기
    2. 결측치 및 중복 데이터 처리
    3. 월별 데이터 변환
    4. 판매 단위 환산
    5. 데이터 시각화
    6. 학습 데이터와 평가 데이터 분리
    7. 머신러닝 알고리즘 학습
    8. 가격 추정 및 성능 비교

    ### 분석의 한계

    원본 데이터의 실제 조사 연도를 명확하게
    구분하기 어려우므로 동일한 월과 조건의
    가격을 평균으로 집계하였습니다.

    머신러닝은 주어진 조건의 가격을 추정하며
    미래 연도의 가격을 예측하는 것이 아닙니다.

    날씨, 생산량, 물류비 등 가격에 영향을 주는
    외부 요인은 포함되지 않았습니다.
    """)

st.divider()

st.caption(
    "농축수산물 가격 분석 및 예측 시스템 | "
    "외식경영 · 데이터 분석 · 머신러닝"
)
