import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="서울 관광지 TOP 10", page_icon="🇰🇷", layout="wide")

PLACES = [
    ("경복궁", "Gyeongbokgung Palace", 37.5796, 126.9770, "역사·문화", "조선 시대의 대표 궁궐로, 한국의 전통 건축과 역사를 경험할 수 있어요."),
    ("N서울타워", "N Seoul Tower", 37.5512, 126.9882, "전망·자연", "남산에 있는 서울의 대표 전망 명소로, 아름다운 도심 풍경을 감상할 수 있어요."),
    ("명동", "Myeongdong", 37.5636, 126.9827, "쇼핑·음식", "K-뷰티 매장과 쇼핑 거리, 다양한 길거리 음식을 만날 수 있어요."),
    ("북촌한옥마을", "Bukchon Hanok Village", 37.5826, 126.9830, "역사·문화", "전통 한옥이 남아 있는 주거 지역이에요. 방문 제한 시간과 주민 생활을 존중해 주세요."),
    ("인사동", "Insadong", 37.5740, 126.9855, "역사·문화", "전통 공예품, 기념품, 찻집을 둘러보기 좋은 문화 거리예요."),
    ("롯데월드타워", "Lotte World Tower", 37.5125, 127.1025, "전망·자연", "서울스카이 전망대와 쇼핑 시설을 갖춘 초고층 랜드마크예요."),
    ("홍대거리", "Hongdae Street", 37.5563, 126.9236, "쇼핑·음식", "버스킹과 개성 있는 카페, 패션 매장 등 젊은 문화를 즐길 수 있어요."),
    ("동대문디자인플라자", "Dongdaemun Design Plaza", 37.5665, 127.0092, "예술·디자인", "독특한 곡선형 건축과 전시·디자인 행사를 만날 수 있는 공간이에요."),
    ("광장시장", "Gwangjang Market", 37.5700, 126.9995, "쇼핑·음식", "빈대떡과 김밥 등 다양한 한국 시장 음식을 맛볼 수 있어요."),
    ("청계천", "Cheonggyecheon Stream", 37.5690, 126.9785, "전망·자연", "서울 도심을 흐르는 하천으로, 산책하며 쉬어 가기 좋아요."),
]

st.title("🇰🇷 외국인에게 추천하는 서울 관광지 TOP 10")
st.write("지도에서 관광지를 눌러 보고, 아래에서 각 명소의 특징을 알아보세요!")
st.caption("※ 공식 외국인 방문객 수 순위가 아닌 대표 관광지 추천 목록입니다. 지도 위치는 대표 지점 기준입니다.")

category = st.selectbox("🧭 관광지 유형", ["전체", "역사·문화", "쇼핑·음식", "전망·자연", "예술·디자인"])
filtered = [(i, p) for i, p in enumerate(PLACES, 1) if category == "전체" or p[4] == category]

m = folium.Map(location=[37.558, 126.992], zoom_start=11, tiles="OpenStreetMap", control_scale=True)
for rank, (name, en, lat, lon, kind, desc) in filtered:
    popup_html = f"<b>{rank}. {name}</b><br>{en}<br>{desc}"
    folium.Marker(
        location=[lat, lon],
        tooltip=f"{rank}. {name}",
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.DivIcon(html=f'''<div style="background:#e84855;color:white;border:2px solid white;border-radius:50%;width:30px;height:30px;line-height:26px;text-align:center;font-weight:bold;box-shadow:0 2px 5px #555;">{rank}</div>''')
    ).add_to(m)

st.subheader("🗺️ 서울 관광 지도")
st_folium(m, height=520, use_container_width=True, returned_objects=[])
st.caption("지도의 번호를 클릭하면 관광지 정보를 볼 수 있어요. 지도를 드래그하거나 확대할 수도 있어요.")

st.subheader("🏙️ 관광지 소개")
for rank, (name, en, lat, lon, kind, desc) in filtered:
    with st.container(border=True):
        st.markdown(f"**{rank}. {name} ({en})**")
        st.caption(kind)
        st.write(desc)
        st.link_button("📍 구글 지도에서 위치 보기", f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")

st.divider()
st.caption("지도 데이터 © OpenStreetMap contributors | 지도 타일 표시에는 인터넷 연결이 필요합니다.")
