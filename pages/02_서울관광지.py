import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title='서울 관광지 TOP 10', page_icon='🇰🇷', layout='wide')
st.title('🇰🇷 외국인에게 추천하는 서울 관광지 TOP 10')
st.write('서울의 대표 관광지와 1박 2일 추천 여행 일정을 확인해 보세요!')
st.caption('※ TOP 10은 공식 방문객 순위가 아닌 추천 목록이며, 일정과 이동 시간은 예시입니다.')

places = [
    {'name':'경복궁','english':'Gyeongbokgung Palace','lat':37.5796,'lon':126.9770,'category':'역사·문화','description':'조선 시대의 대표 궁궐로 전통 건축과 한복 문화를 경험할 수 있습니다.'},
    {'name':'N서울타워','english':'N Seoul Tower','lat':37.5512,'lon':126.9882,'category':'자연·전망','description':'남산에 위치한 전망 명소로 서울의 전경과 야경을 감상할 수 있습니다.'},
    {'name':'명동','english':'Myeongdong','lat':37.5636,'lon':126.9827,'category':'쇼핑·음식','description':'K-뷰티와 패션 쇼핑, 다양한 길거리 음식을 즐길 수 있습니다.'},
    {'name':'북촌한옥마을','english':'Bukchon Hanok Village','lat':37.5826,'lon':126.9830,'category':'역사·문화','description':'한옥이 모여 있는 주거 지역으로 조용히 걸으며 전통적인 풍경을 감상할 수 있습니다.'},
    {'name':'인사동','english':'Insadong','lat':37.5740,'lon':126.9855,'category':'역사·문화','description':'전통 공예품, 기념품, 찻집이 모여 있는 문화 거리입니다.'},
    {'name':'롯데월드타워','english':'Lotte World Tower','lat':37.5125,'lon':127.1025,'category':'자연·전망','description':'서울스카이 전망대와 쇼핑시설을 즐길 수 있는 초고층 랜드마크입니다.'},
    {'name':'홍대거리','english':'Hongdae Street','lat':37.5563,'lon':126.9236,'category':'쇼핑·음식','description':'버스킹과 개성 있는 카페, 패션 매장 등 젊은 문화를 만날 수 있습니다.'},
    {'name':'동대문디자인플라자','english':'Dongdaemun Design Plaza','lat':37.5665,'lon':127.0092,'category':'예술·디자인','description':'독특한 건축 디자인과 다양한 전시·문화 행사를 즐길 수 있습니다.'},
    {'name':'광장시장','english':'Gwangjang Market','lat':37.5700,'lon':126.9995,'category':'쇼핑·음식','description':'빈대떡과 김밥 등 한국의 전통시장 먹거리를 맛볼 수 있습니다.'},
    {'name':'청계천','english':'Cheonggyecheon Stream','lat':37.5690,'lon':126.9785,'category':'자연·전망','description':'서울 도심의 하천을 따라 산책하며 쉬어 갈 수 있습니다.'},
]
place_by_name = {p['name']: p for p in places}

# 각 일정은 (시간, 관광지, 추천 활동) 순서입니다.
day1 = [
    ('09:00~10:30','경복궁','궁궐 관람과 한복 체험'),
    ('10:45~11:45','북촌한옥마을','한옥 골목 산책 및 사진 촬영'),
    ('12:00~13:15','인사동','점심 식사와 전통 기념품 구경'),
    ('13:30~14:45','광장시장','시장 먹거리 체험'),
    ('15:15~16:30','동대문디자인플라자','건축물과 전시 관람'),
    ('17:15~19:30','명동','저녁 식사와 쇼핑'),
]
day2 = [
    ('09:00~10:00','청계천','도심 하천 산책'),
    ('11:00~12:45','홍대거리','거리 구경과 점심 식사'),
    ('14:15~16:15','롯데월드타워','전망대 관람 및 쇼핑'),
    ('18:00~19:30','N서울타워','서울 야경 감상'),
]

st.divider()
category = st.selectbox('🔎 관광지 유형 선택', ['전체','역사·문화','쇼핑·음식','자연·전망','예술·디자인'])
filtered = [p for p in places if category == '전체' or p['category'] == category]

st.subheader('🗺️ 서울 관광지 지도')
m = folium.Map(location=[37.558,126.991], zoom_start=11, tiles='OpenStreetMap')
for p in filtered:
    rank = places.index(p) + 1
    popup = folium.Popup(
        f'<b>{rank}. {p["name"]}</b><br>{p["english"]}<br>{p["description"]}',
        max_width=270,
    )
    folium.Marker(
        [p['lat'],p['lon']],
        tooltip=f'{rank}. {p["name"]}',
        popup=popup,
        icon=folium.DivIcon(html=f'''<div style="background:#e63946;color:white;border:2px solid white;border-radius:50%;width:32px;height:32px;line-height:28px;text-align:center;font-size:14px;font-weight:bold;box-shadow:0 2px 5px #555">{rank}</div>'''),
    ).add_to(m)
st_folium(m, height=520, use_container_width=True, returned_objects=[])
st.caption('📍 마커를 클릭하면 관광지 설명이 나타납니다. 유형 필터는 지도와 관광지 소개에 적용됩니다.')

# 지도 바로 아래에 1박 2일 일정 표시
st.divider()
st.header('🧳 서울 1박 2일 추천 여행 일정')
st.write('전통문화부터 쇼핑, 시장 음식, 야경까지 10곳을 둘러보는 예시 코스입니다.')
tab1, tab2 = st.tabs(['☀️ 1일 차 · 전통과 문화', '🌃 2일 차 · 도심과 야경'])

def show_schedule(items):
    for time, name, activity in items:
        with st.container(border=True):
            st.markdown(f'**🕒 {time}  |  📍 {name}**')
            st.write(f'✨ {activity}')
            st.caption(place_by_name[name]['description'])

with tab1:
    show_schedule(day1)
    st.info('🏨 숙박 추천 지역: 명동 또는 종로 일대 (숙소 예약은 별도)')
with tab2:
    show_schedule(day2)

st.subheader('📋 전체 여행 일정표')
rows = []
for day_label, items in [('1일 차',day1),('2일 차',day2)]:
    for time, name, activity in items:
        rows.append({'날짜':day_label,'시간':time,'관광지':name,'추천 활동':activity})
st.dataframe(rows, hide_index=True, use_container_width=True)
st.warning('⏱️ 이동 시간과 관광지 운영시간은 방문 날짜에 따라 달라집니다. 경복궁 휴궁일, 북촌 방문 제한 시간, 전망대 운영시간 등을 방문 전 확인하세요. 특히 2일 차 이동 구간은 여유 있게 조정하는 것이 좋습니다.')

st.divider()
st.subheader('🏙️ 관광지 소개')
for p in filtered:
    rank = places.index(p) + 1
    with st.expander(f'{rank}. {p["name"]} ({p["english"]})'):
        st.write(f'**관광 유형:** {p["category"]}')
        st.write(p['description'])
        url = f'https://www.google.com/maps/search/?api=1&query={p["lat"]},{p["lon"]}'
        st.link_button('📍 구글 지도에서 보기', url)

st.divider()
st.success('🇰🇷 서울의 역사, 음식, 쇼핑, 문화, 야경을 1박 2일 동안 즐겨 보세요!')
