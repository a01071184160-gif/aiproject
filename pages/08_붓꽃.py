
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score

# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="AI 붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 AI 붓꽃 품종 예측 프로그램")

st.write("""
꽃잎 길이와 너비를 입력하면
3가지 인공지능 분류 알고리즘이
붓꽃의 품종을 예측합니다.
""")

# =====================================
# 2. CSV 파일 불러오기
# =====================================
@st.cache_data
def read_csv(file):
    for encoding in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            if hasattr(file, "seek"):
                file.seek(0)

            return pd.read_csv(
                file,
                encoding=encoding
            )

        except UnicodeDecodeError:
            continue

    raise ValueError("CSV 인코딩을 확인해주세요.")


current_dir = Path(__file__).resolve().parent

possible_paths = [
    current_dir / "iris.csv",
    current_dir.parent / "iris.csv",
    Path.cwd() / "iris.csv"
]

csv_path = next(
    (p for p in possible_paths if p.is_file()),
    None
)

st.sidebar.header("📁 데이터 파일")

uploaded_file = st.sidebar.file_uploader(
    "CSV 파일 직접 업로드",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        df = read_csv(uploaded_file)
        st.sidebar.success("CSV 업로드 성공")

    elif csv_path is not None:
        df = read_csv(csv_path)
        st.sidebar.success("CSV 자동 불러오기 성공")

    else:
        st.warning(
            "iris.csv 파일을 찾을 수 없습니다. "
            "왼쪽 메뉴에서 CSV 파일을 업로드해주세요."
        )
        st.stop()

except Exception as e:
    st.error(f"CSV 파일 읽기 오류: {e}")
    st.stop()

# =====================================
# 3. 데이터 전처리
# =====================================
df.columns = df.columns.astype(str).str.strip()

required_columns = [
    "꽃잎 길이",
    "꽃잎 너비",
    "꽃 품종"
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    st.error(f"필요한 열이 없습니다: {missing}")
    st.write("현재 CSV 열:", df.columns.tolist())
    st.stop()

df = df[required_columns].copy()

for col in ["꽃잎 길이", "꽃잎 너비"]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df["꽃 품종"] = (
    df["꽃 품종"]
    .astype("string")
    .str.strip()
    .str.lower()
)

name_map = {
    "iris-setosa": "Setosa",
    "iris-versicolor": "Versicolor",
    "iris-virginica": "Virginica",
    "setosa": "Setosa",
    "versicolor": "Versicolor",
    "virginica": "Virginica"
}

df["품종"] = df["꽃 품종"].map(name_map)

df = df.replace(
    [float("inf"), float("-inf")],
    float("nan")
)

df = df.dropna(
    subset=["꽃잎 길이", "꽃잎 너비", "품종"]
).reset_index(drop=True)

if len(df) < 15 or df["품종"].nunique() < 2:
    st.error("학습에 필요한 데이터가 부족합니다.")
    st.stop()

if df["품종"].value_counts().min() < 2:
    st.error("품종별 데이터가 부족합니다.")
    st.stop()

# =====================================
# 4. 입력 가능한 범위
# =====================================
length_min = float(df["꽃잎 길이"].min())
length_max = float(df["꽃잎 길이"].max())

width_min = float(df["꽃잎 너비"].min())
width_max = float(df["꽃잎 너비"].max())

st.subheader("📏 입력 가능한 꽃잎 크기")

st.info(
    f"꽃잎 길이: {length_min:.1f} ~ "
    f"{length_max:.1f} cm\n\n"
    f"꽃잎 너비: {width_min:.1f} ~ "
    f"{width_max:.1f} cm"
)

# =====================================
# 5. 사용자 입력
# =====================================
st.subheader("🌼 꽃잎 크기 입력")

col1, col2 = st.columns(2)

with col1:
    petal_length = st.number_input(
        "꽃잎 길이 (cm)",
        min_value=length_min,
        max_value=length_max,
        value=min(max(3.5, length_min), length_max),
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=min(max(1.0, width_min), width_max),
        step=0.1,
        format="%.1f"
    )

# =====================================
# 6. 학습 데이터와 테스트 데이터 분리
# =====================================
X = df[["꽃잎 길이", "꽃잎 너비"]]
y = df["품종"].astype(str)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# =====================================
# 7. 분류 알고리즘 3개 생성
# =====================================
models = {
    "KNN": make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(n_neighbors=5)
    ),

    "Decision Tree": DecisionTreeClassifier(
        max_depth=4,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        random_state=42
    )
}

# =====================================
# 8. 사용자 입력 데이터 생성
# =====================================
input_data = pd.DataFrame({
    "꽃잎 길이": [petal_length],
    "꽃잎 너비": [petal_width]
})

# =====================================
# 9. 모델 학습 및 예측
# =====================================
results = []
probability_results = []

for name, model in models.items():

    # 모델 학습
    model.fit(X_train, y_train)

    # 사용자 입력값 예측
    prediction = model.predict(input_data)[0]

    # 테스트 데이터 정확도 계산
    test_prediction = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        test_prediction
    )

    # 품종별 예측 비율
    probabilities = model.predict_proba(
        input_data
    )[0]

    results.append({
        "알고리즘": name,
        "예측 품종": prediction,
        "정확도(%)": round(accuracy * 100, 2),
        "예측 비율(%)": round(
            max(probabilities) * 100, 2
        )
    })

    for species, probability in zip(
        model.classes_,
        probabilities
    ):
        probability_results.append({
            "알고리즘": name,
            "품종": species,
            "예측 비율(%)": round(
                probability * 100, 2
            )
        })

result_df = pd.DataFrame(results)

# =====================================
# 10. 알고리즘별 예측 결과
# =====================================
st.divider()

st.subheader("🔮 3가지 알고리즘 예측 결과")

columns = st.columns(3)

for i, result in enumerate(results):
    with columns[i]:
        st.markdown(
            f"### {result['알고리즘']}"
        )

        st.metric(
            "예측 품종",
            result["예측 품종"]
        )

        st.metric(
            "테스트 정확도",
            f"{result['정확도(%)']:.2f}%"
        )

        st.write(
            f"예측 비율: "
            f"{result['예측 비율(%)']:.2f}%"
        )

# =====================================
# 11. 알고리즘 결과 비교
# =====================================
st.subheader("📊 알고리즘별 결과 비교")

st.dataframe(
    result_df,
    hide_index=True,
    use_container_width=True
)

st.caption(
    "정확도는 전체 데이터 중 20%를 "
    "테스트 데이터로 사용하여 계산했습니다. "
    "세 알고리즘 모두 동일한 데이터를 사용합니다."
)

# =====================================
# 12. 예측 결과 일치 여부
# =====================================
st.subheader("🤝 예측 결과 일치 여부")

prediction_counts = (
    result_df["예측 품종"].value_counts()
)

if len(prediction_counts) == 1:

    final_prediction = prediction_counts.index[0]

    st.success(
        f"3가지 알고리즘 모두 "
        f"{final_prediction}으로 예측했습니다!"
    )

elif prediction_counts.iloc[0] >= 2:

    final_prediction = prediction_counts.index[0]

    st.warning(
        f"알고리즘의 예측 결과가 서로 다릅니다. "
        f"다수결 결과는 {final_prediction}입니다."
    )

else:
    st.warning(
        "3가지 알고리즘의 예측 결과가 "
        "모두 달라 다수결로 결정할 수 없습니다."
    )

# =====================================
# 13. 정확도 비교 그래프
# =====================================
st.subheader("🏆 알고리즘 정확도 비교")

fig, ax = plt.subplots(figsize=(9, 4))

bars = ax.bar(
    result_df["알고리즘"],
    result_df["정확도(%)"],
    color=[
        "royalblue",
        "mediumseagreen",
        "mediumpurple"
    ]
)

for bar, accuracy in zip(
    bars,
    result_df["정확도(%)"]
):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        accuracy + 1,
        f"{accuracy:.2f}%",
        ha="center",
        fontweight="bold"
    )

ax.set_ylim(0, 110)
ax.set_ylabel("Accuracy (%)")
ax.set_title("Classification Model Comparison")
ax.grid(axis="y", alpha=0.3)

st.pyplot(fig)
plt.close(fig)

# 가장 높은 정확도 찾기
best_accuracy = result_df["정확도(%)"].max()

best_models = result_df.loc[
    result_df["정확도(%)"] == best_accuracy,
    "알고리즘"
].tolist()

st.success(
    f"🏆 이번 테스트에서 가장 높은 정확도: "
    f"{', '.join(best_models)} "
    f"({best_accuracy:.2f}%)"
)

st.caption(
    "이번 테스트 결과가 가장 높다는 뜻이며, "
    "항상 가장 좋은 알고리즘이라는 의미는 아닙니다."
)

# =====================================
# 14. 품종별 예측 비율 비교
# =====================================
st.subheader("📈 품종별 예측 비율 비교")

prob_df = pd.DataFrame(probability_results)

prob_table = prob_df.pivot(
    index="알고리즘",
    columns="품종",
    values="예측 비율(%)"
)

st.dataframe(
    prob_table,
    use_container_width=True
)

st.bar_chart(prob_table)

st.caption(
    "예측 비율은 각 모델이 계산한 값이며, "
    "실제로 정답일 확률을 보장하지 않습니다."
)

# =====================================
# 15. 붓꽃 산점도
# =====================================
st.divider()

st.subheader("⭐ 꽃잎 크기와 사용자 입력 위치")

fig, ax = plt.subplots(figsize=(10, 6))

colors = {
    "Setosa": "royalblue",
    "Versicolor": "mediumseagreen",
    "Virginica": "mediumpurple"
}

for species in sorted(df["품종"].unique()):

    subset = df[df["품종"] == species]

    ax.scatter(
        subset["꽃잎 길이"],
        subset["꽃잎 너비"],
        color=colors.get(species, "gray"),
        label=species,
        alpha=0.7,
        s=55
    )

# 사용자 입력값을 노란색 별로 표시
ax.scatter(
    petal_length,
    petal_width,
    marker="*",
    color="yellow",
    edgecolor="black",
    linewidth=1.5,
    s=550,
    label="Your Input",
    zorder=10
)

ax.annotate(
    "Your Input",
    xy=(petal_length, petal_width),
    xytext=(12, 12),
    textcoords="offset points",
    fontsize=11,
    fontweight="bold"
)

ax.set_xlabel("Petal Length (cm)")
ax.set_ylabel("Petal Width (cm)")
ax.set_title("Iris Species Prediction")

ax.set_xlim(
    length_min - 0.4,
    length_max + 0.7
)

ax.set_ylim(
    width_min - 0.3,
    width_max + 0.5
)

ax.legend()
ax.grid(True, alpha=0.3)

st.pyplot(fig)
plt.close(fig)

st.info(
    f"⭐ 노란색 별의 위치\n\n"
    f"꽃잎 길이: {petal_length:.1f}cm\n\n"
    f"꽃잎 너비: {petal_width:.1f}cm"
)

# =====================================
# 16. 알고리즘 작동 원리 설명
# =====================================
st.divider()

st.subheader("🤖 분류 알고리즘 작동 원리")

tab1, tab2, tab3 = st.tabs([
    "KNN",
    "Decision Tree",
    "Random Forest"
])

# KNN 설명
with tab1:

    st.header("🔵 KNN (K-최근접 이웃)")

    st.write("""
    KNN은 새로운 데이터와 가장 비슷한
    기존 데이터를 찾아 분류하는 알고리즘입니다.

    ### 작동 방법

    1. 꽃잎 길이와 너비를 입력합니다.
    2. 데이터의 크기를 표준화합니다.
    3. 기존 꽃들과의 거리를 계산합니다.
    4. 가장 가까운 꽃 5개를 찾습니다.
    5. 가장 많이 등장한 품종으로 예측합니다.

    ### 쉬운 예시

    가까운 꽃 5개 중 Setosa가 4개,
    Versicolor가 1개라면
    Setosa로 예측합니다.

    ### 장점

    - 작동 원리가 간단합니다.
    - 비슷한 데이터를 쉽게 비교할 수 있습니다.

    ### 단점

    - 데이터가 많으면 예측이 느려질 수 있습니다.
    - K값에 따라 결과가 달라질 수 있습니다.
    """)

    st.info("현재 설정: K = 5")

# Decision Tree 설명
with tab2:

    st.header("🟢 Decision Tree (의사결정나무)")

    st.write("""
    의사결정나무는 여러 조건을 순서대로
    판단하여 데이터를 분류하는 알고리즘입니다.

    ### 작동 방법

    1. 학습 데이터의 특징을 분석합니다.
    2. 품종을 잘 구분하는 조건을 찾습니다.
    3. 조건에 따라 데이터를 나눕니다.
    4. 여러 조건을 반복하여 품종을 결정합니다.

    ### 쉬운 예시

    - 꽃잎 길이가 2.5cm 이하인가?
    - 꽃잎 너비가 1.7cm 이하인가?

    이러한 질문에 예 또는 아니요로
    답하면서 품종을 결정합니다.

    실제 분류 조건은 학습 과정에서 결정됩니다.

    ### 장점

    - 판단 과정을 이해하기 쉽습니다.
    - 데이터 표준화가 필수적이지 않습니다.

    ### 단점

    - 학습 데이터에 지나치게 맞춰질 수 있습니다.
    - 데이터가 바뀌면 판단 기준도 달라질 수 있습니다.
    """)

    st.info("현재 설정: 나무의 최대 깊이 = 4")

# Random Forest 설명
with tab3:

    st.header("🟣 Random Forest (랜덤 포레스트)")

    st.write("""
    랜덤 포레스트는 여러 의사결정나무를
    만들어 결과를 종합하는 알고리즘입니다.

    ### 작동 방법

    1. 학습 데이터에서 무작위로 표본을 뽑습니다.
    2. 여러 개의 의사결정나무를 만듭니다.
    3. 각 나무가 붓꽃의 품종을 예측합니다.
    4. 각 나무의 품종별 예측 확률을 평균냅니다.
    5. 평균 예측 확률이 가장 높은 품종을 선택합니다.

    ### 쉬운 예시

    100개의 의사결정나무가 판단한 결과를
    종합하여 최종 품종을 결정합니다.

    여러 사람의 의견을 모아 판단하는 것과
    비슷한 원리입니다.

    ### 장점

    - 여러 나무의 판단을 종합합니다.
    - 하나의 나무보다 과적합을 줄이기 좋습니다.

    ### 단점

    - 학습에 더 많은 시간이 필요할 수 있습니다.
    - 전체 판단 과정을 설명하기 어렵습니다.
    """)

    st.info("현재 설정: 의사결정나무 100개")

# =====================================
# 17. 알고리즘 특징 비교
# =====================================
st.subheader("📚 알고리즘 특징 비교")

comparison = pd.DataFrame({
    "알고리즘": [
        "KNN",
        "Decision Tree",
        "Random Forest"
    ],

    "작동 원리": [
        "가까운 데이터 비교",
        "조건에 따른 분류",
        "여러 나무의 결과 종합"
    ],

    "주요 설정": [
        "이웃 5개",
        "최대 깊이 4",
        "의사결정나무 100개"
    ],

    "장점": [
        "이해하기 쉬움",
        "판단 과정 확인 가능",
        "과적합 감소에 유리"
    ],

    "단점": [
        "거리와 K값에 영향",
        "과적합 가능성",
        "복잡한 판단 과정"
    ]
})

st.dataframe(
    comparison,
    hide_index=True,
    use_container_width=True
)

# =====================================
# 18. 품종별 평균 크기
# =====================================
st.divider()

st.subheader("📋 품종별 평균 꽃잎 크기")

summary = (
    df.groupby("품종")[
        ["꽃잎 길이", "꽃잎 너비"]
    ]
    .mean()
    .round(2)
)

st.dataframe(
    summary,
    use_container_width=True
)

# =====================================
# 19. 원본 데이터 확인
# =====================================
with st.expander("📁 학습 데이터 확인"):

    st.write(f"전체 데이터: {len(df)}개")
    st.write(f"학습 데이터: {len(X_train)}개")
    st.write(f"테스트 데이터: {len(X_test)}개")

    st.dataframe(
        df,
        use_container_width=True
    )

st.divider()

st.caption(
    "🌸 Pandas + Scikit-learn + Streamlit "
    "| KNN · Decision Tree · Random Forest"
)
