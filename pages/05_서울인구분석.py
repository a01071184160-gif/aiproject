from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import streamlit as st

st.set_page_config(page_title='서울 인구 분석', page_icon='📈', layout='wide')
CSV_PATH = Path(__file__).resolve().parent.parent / 'population.csv'

@st.cache_data
def load_data():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(f'파일을 찾지 못했습니다: {CSV_PATH}')
    for enc in ('utf-8-sig', 'cp949', 'euc-kr'):
        try:
            df = pd.read_csv(CSV_PATH, encoding=enc, dtype=str)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError('CSV 인코딩을 확인할 수 없습니다.')
    df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
    if '행정구역' not in df.columns:
        raise ValueError('행정구역 열이 없습니다. CSV 파일을 확인하세요.')
    df['행정구역'] = df['행정구역'].str.replace(r'\s*\(\d+\)\s*$', '', regex=True).str.strip()
    for c in df.columns:
        if c != '행정구역':
            df[c] = pd.to_numeric(df[c].str.replace(',', '', regex=False), errors='coerce')
    return df

def set_font():
    paths = ['/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
             '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
             'C:/Windows/Fonts/malgun.ttf',
             '/System/Library/Fonts/AppleSDGothicNeo.ttc']
    for path in paths:
        if Path(path).is_file():
            font_manager.fontManager.addfont(path)
            plt.rcParams['font.family'] = font_manager.FontProperties(fname=path).get_name()
            break
    plt.rcParams['axes.unicode_minus'] = False

st.title('📈 서울특별시 연령별 인구 분석')
try:
    df = load_data()
except (FileNotFoundError, ValueError, pd.errors.ParserError) as e:
    st.error(str(e))
    st.stop()
set_font()

# 열 이름에서 연도, 성별, 연령 구간을 자동 추출
pattern = re.compile(r'^(\d{4})년_(?:(남|여)_)?거주자_(\d+~\d+세|100세 이상)$')
column_map = {}
for column in df.columns:
    match = pattern.fullmatch(column)
    if match:
        year, sex, age = match.groups()
        column_map[(int(year), sex or '전체', age)] = column

years = sorted({key[0] for key in column_map})
areas = df['행정구역'].dropna().unique().tolist()
if not years or not areas:
    st.error('연도 또는 행정구역 정보를 확인할 수 없습니다. population.csv를 확인하세요.')
    with st.expander('CSV 열 이름 확인'):
        st.write(df.columns.tolist())
    st.stop()

c1, c2, c3 = st.columns(3)
with c1:
    area = st.selectbox('🏙️ 행정구역', areas)
with c2:
    year = st.selectbox('📅 연도', years, index=len(years)-1)
with c3:
    gender = st.selectbox('👥 성별', ['전체', '남성', '여성'])

sex = {'전체': '전체', '남성': '남', '여성': '여'}[gender]
ages = [f'{n}~{n+9}세' for n in range(0, 100, 10)] + ['100세 이상']
missing = [age for age in ages if (year, sex, age) not in column_map]
if missing:
    st.error('선택 조건의 연령별 열을 찾지 못했습니다: ' + ', '.join(missing))
    with st.expander('문제 확인용 열 이름'):
        st.write(df.columns.tolist())
    st.stop()

selected = df.loc[df['행정구역'] == area]
if selected.empty:
    st.error('선택한 행정구역이 데이터에 없습니다.')
    st.stop()

record = selected.iloc[0]
data = pd.DataFrame({
    '연령': ages,
    '인구수': [record[column_map[(year, sex, age)]] for age in ages]
}).dropna(subset=['인구수'])
if data.empty:
    st.error('표시할 인구 데이터가 없습니다.')
    st.stop()

m1, m2 = st.columns(2)
m1.metric('선택 조건 인구 합계', f"{int(data['인구수'].sum()):,}명")
peak = data.loc[data['인구수'].idxmax()]
m2.metric('인구가 가장 많은 연령대', f"{peak['연령']} ({int(peak['인구수']):,}명)")
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(data['연령'], data['인구수'], color='black', marker='o', linewidth=2)
ax.set_title(f'{area} · {year}년 · {gender} 연령별 인구')
ax.set_xlabel('나이 (연령 구간)')
ax.set_ylabel('인구수 (명)')
ax.set_ylim(bottom=0)
ax.yaxis.set_major_locator(ticker.MultipleLocator(1000))
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
ax.grid(axis='y', color='#cccccc', linewidth=0.6)
ax.set_axisbelow(True)
ax.tick_params(axis='x', labelrotation=35)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

with st.expander('📋 연령별 인구 데이터'):
    table = data.copy()
    table['인구수'] = table['인구수'].astype(int)
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button('CSV 다운로드', table.to_csv(index=False).encode('utf-8-sig'),
                       file_name=f'{area}_{year}_{gender}_인구.csv', mime='text/csv')

