
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

# =====================================
# 1. 페이지 설정
# =====================================
st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 프로그램")
st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "KNN 알고리즘으로 붓꽃 품종을 예측합니다."
)

# =====================================
# 2. CSV 파일 불러오기
# =====================================
@st.cache_data
def load_data():
    current_dir = Path(__file__).resolve().parent

    possible_paths = [
        current_dir / "iris.csv",
        current_dir.parent / "iris.csv"
    ]

    file_path = next(
        (p for p in possible_paths if p.is_file()),
        None
    )

    if file_path is None:
        raise FileNotFoundError(
            "iris.csv 파일을 찾을 수 없습니다."
        )

    df = None

    for encoding in ["utf-8-sig", "cp949", "euc-kr"]:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 인코딩을 확인해주세요.")

    # 열 이름의 앞뒤 공백 제거
    df.columns = df.columns.str.strip()

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
        raise ValueError(
            f"필요한 열이 없습니다: {missing}"
        )

    df = df[required_columns].copy()

    for col in ["꽃잎 길이", "꽃잎 너비"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df = df.dropna()

    if df.empty:
        raise ValueError("학습할 데이터가 없습니다.")

    return df


try:
    df = load_data()
except (FileNotFoundError, ValueError) as e:
    st.error(str(e))
    st.stop()

# =====================================
# 3. 품종 이름 설정
# =====================================
name_map = {
    "Iris-setosa": "Setosa",
    "Iris-versicolor": "Versicolor",
    "Iris-virginica": "Virginica"
}

df["품종"] = df["꽃 품종"].replace(name_map)

# =====================================
# 4. 입력 범위 설정
# =====================================
length_min = float(df["꽃잎 길이"].min())
length_max = float(df["꽃잎 길이"].max())

width_min = float(df["꽃잎 너비"].min())
width_max = float(df["꽃잎 너비"].max())

st.subheader("📏 입력 가능한 범위")

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
        value=3.5,
        step=0.1,
        format="%.1f"
    )

with col2:
    petal_width = st.number_input(
        "꽃잎 너비 (cm)",
        min_value=width_min,
        max_value=width_max,
        value=1.0,
        step=0.1,
        format="%.1f"
    )

# =====================================
# 6. KNN 모델 학습
# =====================================
X = df[["꽃잎 길이", "꽃잎 너비"]]
y = df["품종"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = make_pipeline(
    StandardScaler(),
    KNeighborsClassifier(n_neighbors=5)
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

# =====================================
# 7. 품종 예측
# =====================================
st.subheader("🔍 품종 예측 결과")

input_data = pd.DataFrame({
    "꽃잎 길이": [petal_length],
    "꽃잎 너비": [petal_width]
})

prediction = model.predict(input_data)[0]
probabilities = model.predict_proba(input_data)[0]

st.success(f"🌸 예측된 붓꽃 품종: {prediction}")

st.write(
    f"**테스트 데이터 정확도: {accuracy * 100:.2f}%**"
)

st.caption(
    "정확도는 전체 데이터의 20%를 테스트용으로 "
    "분리하여 계산했습니다."
)

# 예측 확률
st.subheader("📊 품종별 예측 확률")

prob_df = pd.DataFrame({
    "품종": model.classes_,
    "예측 확률(%)": probabilities * 100
})

st.dataframe(
    prob_df.style.format({
        "예측 확률(%)": "{:.1f}%"
    }),
    hide_index=True,
    use_container_width=True
)

# =====================================
# 8. 산점도 시각화
# =====================================
st.subheader("⭐ 붓꽃 데이터와 입력 위치")

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
        label=species,
        color=colors.get(species, "gray"),
        alpha=0.65,
        s=45
    )

# 사용자가 입력한 위치를 노란 별로 표시
ax.scatter(
    petal_length,
    petal_width,
    color="yellow",
    edgecolor="black",
    linewidth=1.5,
    marker="*",
    s=450,
    label="Your Input",
    zorder=10
)

ax.annotate(
    "Your Input",
    (petal_length, petal_width),
    xytext=(10, 12),
    textcoords="offset points",
    fontsize=10,
    fontweight="bold"
)

ax.set_xlabel("Petal Length (cm)")
ax.set_ylabel("Petal Width (cm)")
ax.set_title("Iris Species Prediction (KNN)")

ax.legend()
ax.grid(True, alpha=0.3)

ax.set_xlim(
    length_min - 0.3,
    length_max + 0.5
)

ax.set_ylim(
    width_min - 0.2,
    width_max + 0.4
)

st.pyplot(fig)
plt.close(fig)

st.caption(
    "노란색 별(★)은 사용자가 입력한 꽃잎 길이와 "
    "너비의 위치입니다."
)

# =====================================
# 9. 품종별 평균 데이터
# =====================================
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
# 10. 알고리즘 설명
# =====================================
with st.expander("🤖 KNN 알고리즘 설명"):
    st.write(
        """
        KNN(K-Nearest Neighbors)은
        새로운 데이터와 가까운 기존 데이터를
        비교하여 분류하는 머신러닝 알고리즘입니다.

        이 프로그램은 K=5를 사용합니다.

        1. 꽃잎 길이와 너비를 입력합니다.
        2. 두 특성을 표준화합니다.
        3. 가장 가까운 학습 데이터 5개를 찾습니다.
        4. 가장 많이 나타난 품종으로 분류합니다.

        꽃받침 너비 데이터는 사용하지 않습니다.
        """
    )
