import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="식재료 가격 분석",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ 농축수산물 가격 분석 시스템")
st.markdown(
    "식재료의 가격 변화를 분석하여 "
    "효율적인 구매와 원가 관리를 지원합니다."
)

# =====================================
# 1. CSV 파일 불러오기
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent

@st.cache_data
def load_data():
    files = sorted(
        BASE_DIR.glob("*농축수산물*소매가격*.csv")
    )

    if not files:
        path = BASE_DIR / "food_price.csv"

        if not path.exists():
            raise FileNotFoundError(
                "CSV 파일을 찾을 수 없습니다."
            )
    else:
        path = files[0]

    for encoding in ["cp949", "utf-8-sig", "euc-kr"]:
        try:
            return pd.read_csv(
                path,
                encoding=encoding
            )
        except UnicodeError:
            continue

    raise ValueError("CSV 인코딩을 확인해 주세요.")

try:
    df = load_data()
except Exception as e:
    st.error(str(e))
    st.stop()

# =====================================
# 2. 데이터 전처리
# =====================================

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
    st.error("CSV 파일의 열 이름을 확인해 주세요.")
    st.stop()

df = df.dropna(subset=required).copy()

df["평균가격"] = pd.to_numeric(
    df["평균가격"].astype(str).str.replace(",", ""),
    errors="coerce"
)

df["유통단계별무게"] = pd.to_numeric(
    df["유통단계별무게"],
    errors="coerce"
)

df["날짜"] = pd.to_datetime(
    df["가격등록연월"],
    format="%b-%y",
    errors="coerce"
)

df = df.dropna(
    subset=["평균가격", "유통단계별무게", "날짜"]
)

df = df[
    (df["유통단계별무게"] > 0)
    & (df["평균가격"] > 0)
].copy()

if df.empty:
    st.error("분석할 수 있는 데이터가 없습니다.")
    st.stop()

df["월"] = df["날짜"].dt.month

# 판매 단위 표시
df["판매단위"] = (
    df["유통단계별무게"].map(lambda x: f"{x:g}")
    + df["유통단계별단위"].astype(str)
)

# 가격 비교를 위한 단위 환산
df["비교단위"] = df["유통단계별단위"]
df["환산가격"] = (
    df["평균가격"] / df["유통단계별무게"]
)

# g 단위를 kg 단위로 환산
mask = df["유통단계별단위"] == "g"

df.loc[mask, "환산가격"] *= 1000
df.loc[mask, "비교단위"] = "kg"

# 품목과 품종을 합쳐 비교 이름 생성
df["식재료"] = (
    df["품목명"].astype(str)
    + " - "
    + df["품종명"].astype(str)
)

# =====================================
# 3. 기본 데이터 정보
# =====================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "전체 데이터",
    f"{len(df):,}개"
)

col2.metric(
    "식재료 품목",
    f"{df['품목명'].nunique()}종"
)

col3.metric(
    "세부 품종",
    f"{df['식재료'].nunique()}종"
)

col4.metric(
    "분석 가능 월",
    f"{df['월'].nunique()}개월"
)

st.divider()

# =====================================
# 4. 분석 메뉴
# =====================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 월별 가격 분석",
    "📊 식재료 가격 비교",
    "⚖️ 등급별 가격 비교",
    "🌡️ 가격 히트맵",
    "📋 원본 데이터"
])

# =====================================
# 5. 월별 가격 분석
# =====================================

with tab1:

    st.header("월별 식재료 가격 변화")

    c1, c2, c3, c4 = st.columns(4)

    item = c1.selectbox(
        "품목 선택",
        sorted(df["품목명"].unique()),
        key="item1"
    )

    selected = df[df["품목명"] == item]

    variety = c2.selectbox(
        "품종 선택",
        sorted(selected["품종명"].unique()),
        key="variety1"
    )

    selected = selected[
        selected["품종명"] == variety
    ]

    grade = c3.selectbox(
        "등급 선택",
        sorted(selected["등급명"].unique()),
        key="grade1"
    )

    selected = selected[
        selected["등급명"] == grade
    ]

    unit = c4.selectbox(
        "판매 단위 선택",
        sorted(selected["판매단위"].unique()),
        key="unit1"
    )

    selected = selected[
        selected["판매단위"] == unit
    ]

    monthly = (
        selected.groupby("월", as_index=False)
        ["평균가격"].mean()
        .sort_values("월")
    )

    fig = px.line(
        monthly,
        x="월",
        y="평균가격",
        markers=True,
        title=f"{item} ({variety}) 월별 가격 변화",
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

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=[
            f"{i}월" for i in range(1, 13)
        ]
    )

    fig.update_yaxes(tickformat=",.0f")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # 가격 분석
    min_row = monthly.loc[
        monthly["평균가격"].idxmin()
    ]

    max_row = monthly.loc[
        monthly["평균가격"].idxmax()
    ]

    avg_price = monthly["평균가격"].mean()

    min_price = min_row["평균가격"]
    max_price = max_row["평균가격"]

    saving = max_price - min_price

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
        f"{saving:,.0f}원"
    )

    st.subheader("식재료 구매 분석 결과")

    st.info(
        f"{item}의 기록상 최저가 월은 "
        f"{int(min_row['월'])}월이며, "
        f"{unit}당 평균가격은 "
        f"{min_price:,.0f}원입니다. "
        f"최고가 월과 비교하면 "
        f"{saving:,.0f}원의 차이가 있습니다."
    )

    st.caption(
        "과거 기록에 대한 분석이며 "
        "미래 가격을 보장하지 않습니다."
    )

    st.dataframe(
        monthly,
        use_container_width=True,
        hide_index=True
    )

# =====================================
# 6. 식재료별 가격 비교
# =====================================

with tab2:

    st.header("식재료별 가격 비교")

    c1, c2, c3 = st.columns(3)

    month = c1.selectbox(
        "분석할 월",
        sorted(df["월"].unique()),
        format_func=lambda x: f"{x}월",
        key="month2"
    )

    compare_unit = c2.selectbox(
        "가격 비교 단위",
        sorted(df["비교단위"].unique()),
        key="unit2"
    )

    grade = c3.selectbox(
        "등급 선택",
        sorted(df["등급명"].unique()),
        key="grade2"
    )

    compare = df[
        (df["월"] == month)
        & (df["비교단위"] == compare_unit)
        & (df["등급명"] == grade)
    ]

    if compare.empty:

        st.warning("해당 조건의 데이터가 없습니다.")

    else:

        compare = (
            compare.groupby(
                "식재료",
                as_index=False
            )["환산가격"].mean()
            .sort_values(
                "환산가격",
                ascending=False
            )
        )

        top_n = st.slider(
            "표시할 식재료 수",
            1,
            30,
            10
        )

        order = st.radio(
            "정렬 방식",
            ["가격 높은 순", "가격 낮은 순"],
            horizontal=True
        )

        compare = compare.sort_values(
            "환산가격",
            ascending=(order == "가격 낮은 순")
        ).head(top_n)

        fig = px.bar(
            compare,
            x="식재료",
            y="환산가격",
            color="환산가격",
            color_continuous_scale="Blues",
            title=f"{month}월 식재료 가격 비교",
            labels={
                "식재료": "식재료",
                "환산가격": f"1{compare_unit}당 가격(원)"
            }
        )

        fig.update_yaxes(tickformat=",.0f")
        fig.update_layout(coloraxis_showscale=False)

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
            "g과 kg은 1kg 기준으로 환산하며, "
            "개·마리·포기 등은 같은 단위끼리 비교합니다."
        )

# =====================================
# 7. 등급별 가격 비교
# =====================================

with tab3:

    st.header("상품과 중품 가격 비교")

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
            "선택한 식재료는 비교 가능한 "
            "등급이 한 종류뿐입니다."
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

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(range(1, 13)),
        ticktext=[
            f"{i}월" for i in range(1, 13)
        ]
    )

    fig.update_yaxes(tickformat=",.0f")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "동일 품종과 판매 단위에서 "
        "등급에 따른 가격 차이를 비교합니다."
    )

    st.dataframe(
        grade_month,
        use_container_width=True,
        hide_index=True
    )

# =====================================
# 8. 월별 가격 히트맵
# =====================================

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

        selected_foods = st.multiselect(
            "비교할 식재료 선택",
            options,
            default=options[:8]
        )

        if not selected_foods:

            st.warning("식재료를 선택해 주세요.")

        else:

            heat = heat[
                heat["식재료"].isin(selected_foods)
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

            # 식재료별 평균가격을 100으로 설정
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
                title="식재료별 상대 가격 수준",
                labels={
                    "x": "월",
                    "y": "식재료",
                    "color": "가격지수"
                }
            )

            fig.update_layout(
                height=max(
                    400,
                    len(selected_foods) * 45 + 150
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.markdown("""
            **히트맵 해석 방법**

            - 🔵 파란색: 평균보다 저렴한 시기
            - ⚪ 흰색: 평균과 비슷한 시기
            - 🔴 빨간색: 평균보다 비싼 시기
            - 100: 해당 식재료의 월평균 가격
            - 80: 평균보다 20% 저렴
            - 120: 평균보다 20% 비쌈
            - 빈칸: 해당 월의 데이터 없음
            """)

# =====================================
# 9. 원본 데이터 확인
# =====================================

with tab5:

    st.header("농축수산물 소매가격 데이터")

    st.dataframe(
        df[required],
        use_container_width=True,
        hide_index=True
    )

    csv = df[required].to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="CSV 데이터 다운로드",
        data=csv,
        file_name="food_price_analysis.csv",
        mime="text/csv"
    )

    st.markdown("""
    ### 데이터 출처

    - 제공기관: 한국농수산식품유통공사
    - 데이터명: 월별 농축수산물 소매가격 정보
    - 출처: 공공데이터포털
    - 분석 도구: Pandas, Plotly, Streamlit

    ### 분석 시 주의사항

    원본 CSV의 연월 표기를 그대로 사용했습니다.
    동일한 월의 중복 기록은 평균으로 집계했습니다.
    실제 조사 연도가 명확하게 구분되지 않으므로
    미래 가격 예측에는 사용하지 않았습니다.
    """)

st.divider()

st.caption(
    "농축수산물 가격 분석 시스템 | "
    "외식경영 및 식재료 원가 관리"
)
