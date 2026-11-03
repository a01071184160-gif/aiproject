import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title='내가 가고 싶은 도시, 부산', page_icon='🌊', layout='wide')
st.title('🌊 내가 가고 싶은 도시, 부산')
st.write('바다와 야경, 맛있는 음식이 어우러진 도시 부산으로 떠나는 1박 2일 여행!')
st.info('**부산에 가고 싶은 이유**: 푸른 바다를 감상하고, 다양한 지역 음식을 맛보며, 부산만의 활기찬 분위기를 경험하고 싶기 때문입니다.')

places = [
    {'name':'감천문화마을','lat':35.0975,'lon':129.0106,'category':'문화','desc':'산비탈을 따라 이어진 알록달록한 집과 골목길이 인상적인 마을입니다.'},
    {'name':'자갈치시장','lat':35.0967,'lon':129.0305,'category':'음식','desc':'부산의 대표적인 수산시장으로 신선한 해산물과 시장 문화를 만날 수 있습니다.'},
    {'name':'BIFF 광장','lat':35.0987,'lon':129.0285,'category':'문화·음식','desc':'영화와 길거리 먹거리로 유명한 남포동의 활기찬 거리입니다.'},
    {'name':'흰여울문화마을','lat':35.0786,'lon':129.0443,'category':'문화·바다','desc':'바다를 내려다보며 골목길과 풍경을 감상할 수 있는 마을입니다.'},
    {'name':'해운대해수욕장','lat':35.1587,'lon':129.1604,'category':'바다','desc':'넓은 백사장과 도시 풍경이 어우러진 부산의 대표 해변입니다.'},
    {'name':'동백섬','lat':35.1537,'lon':129.1529,'category':'자연','desc':'해안 산책로를 따라 바다와 누리마루 APEC하우스 주변 풍경을 즐길 수 있습니다.'},
    {'name':'청사포','lat':35.1603,'lon':129.1912,'category':'바다','desc':'등대와 해안 풍경이 아름다운 작은 포구입니다.'},
    {'name':'광안리해수욕장','lat':35.1532,'lon':129.1186,'category':'야경','desc':'광안대교를 배경으로 바다와 아름다운 야경을 감상할 수 있습니다.'},
]

st.subheader('🗺️ 부산 여행 지도')
selected_day = st.radio('지도에 표시할 일정', ['전체','1일 차','2일 차'], horizontal=True)
day1 = ['감천문화마을','자갈치시장','BIFF 광장','흰여울문화마을']
day2 = ['해운대해수욕장','동백섬','청사포','광안리해수욕장']
visible = [p for p in places if selected_day == '전체' or p['name'] in (day1 if selected_day == '1일 차' else day2)]
m = folium.Map(location=[35.135,129.095], zoom_start=11, tiles='OpenStreetMap')
for p in visible:
    idx = places.index(p) + 1
    folium.Marker([p['lat'],p['lon']], tooltip=f'{idx}. {p["name"]}', popup=folium.Popup(f'<b>{p["name"]}</b><p>{p["desc"]}</p>', max_width=260), icon=folium.Icon(color='blue' if p['name'] in day1 else 'green', icon='info-sign')).add_to(m)
st_folium(m, height=480, use_container_width=True, returned_objects=[])
st.caption('마커를 누르면 관광지 설명을 볼 수 있어요. 지도는 인터넷 연결이 필요합니다.')

st.subheader('📅 부산 1박 2일 추천 일정')
st.caption('시간은 예시입니다. 실제 교통·운영시간과 이동 출발지를 확인해 조정하세요.')
schedule = {
    '1일 차 · 부산의 골목과 먹거리': [
        ('10:00–11:30','감천문화마을','골목길 산책과 사진 촬영'),
        ('12:00–13:30','자갈치시장','해산물 점심 식사와 시장 구경'),
        ('13:40–15:00','BIFF 광장','영화의 거리와 길거리 간식 체험'),
        ('15:40–17:30','흰여울문화마을','바다 전망과 골목길 산책'),
        ('18:00 이후','숙소 체크인 및 저녁','남포동 또는 영도 인근에서 자유시간'),
    ],
    '2일 차 · 바다와 야경': [
        ('09:30–11:00','해운대해수욕장','아침 바다 산책'),
        ('11:10–12:10','동백섬','해안 산책로 걷기'),
        ('12:20–13:30','점심 식사','해운대 주변 음식점 방문'),
        ('14:00–15:30','청사포','등대와 포구 풍경 감상'),
        ('17:00–19:00','광안리해수욕장','저녁 식사와 광안대교 야경 감상'),
    ]
}
tab1, tab2 = st.tabs(list(schedule))
for tab, (day, items) in zip((tab1,tab2), schedule.items()):
    with tab:
        for time, name, activity in items:
            with st.container(border=True):
                st.markdown(f'**🕒 {time} | 📍 {name}**')
                st.write(activity)
st.info('🏨 숙박 추천: 남포동·영도 주변(1일 차 동선 기준). 2일 차 해운대까지는 대중교통 이동시간을 충분히 확보하세요.')

st.subheader('📍 주요 관광지 소개')
for p in places:
    with st.expander(f'{places.index(p)+1}. {p["name"]} · {p["category"]}'):
        st.write(p['desc'])
        st.link_button('구글 지도에서 위치 보기', f'https://www.google.com/maps/search/?api=1&query={p["lat"]},{p["lon"]}')

st.divider()
st.write('✨ 부산 여행에서는 전통시장 먹거리, 골목문화, 바다 풍경을 모두 경험하고 싶습니다.')
