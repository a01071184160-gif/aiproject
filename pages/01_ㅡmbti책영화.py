import streamlit as st

st.set_page_config(page_title='MBTI 취향 탐험대', page_icon='🎬', layout='centered')

BOOKS = {
 'mystery': [('셜록 홈즈의 모험','아서 코난 도일','날카로운 추리와 반전이 이어지는 단편 미스터리!'),('그리고 아무도 없었다','애거사 크리스티','외딴 섬에서 벌어지는 긴장감 넘치는 추리극.')],
 'fantasy': [('해리 포터와 마법사의 돌','J. K. 롤링','마법 학교에서 펼쳐지는 우정과 비밀의 모험.'),('퍼시 잭슨과 번개 도둑','릭 라이어던','그리스 신화가 현실로 뛰어나오는 유쾌한 모험!')],
 'scifi': [('마션','앤디 위어','화성에 홀로 남은 우주비행사의 기발한 생존기.'),('프로젝트 헤일메리','앤디 위어','기억을 잃은 채 우주에서 깨어난 주인공의 수수께끼.')],
 'growth': [('완득이','김려령','엉뚱하고 따뜻한 관계 속에서 성장하는 이야기.'),('아몬드','손원평','감정을 이해해 가는 소년의 특별한 성장 이야기.')],
 'adventure': [('모모','미하엘 엔데','시간을 훔치는 존재에 맞서는 소녀의 신비한 이야기.'),('호빗','J. R. R. 톨킨','평범한 호빗이 떠나는 뜻밖의 대모험.')],
 'creativity': [('이상한 나라의 앨리스','루이스 캐럴','상상력을 뒤집는 기묘하고 유쾌한 세계.'),('찰리와 초콜릿 공장','로알드 달','상상 초월 초콜릿 공장에서 벌어지는 사건들.')],
 'heart': [('긴긴밤','루리','서로 다른 존재들이 함께 길을 떠나는 뭉클한 모험.'),('불편한 편의점','김호연','편의점에서 만난 사람들의 웃기고 따뜻한 사연.')],
 'action': [('헝거 게임','수잔 콜린스','생존 게임 속에서 시작되는 숨 막히는 저항.'),('메이즈 러너','제임스 대시너','기억을 잃은 소년들이 거대한 미로의 비밀을 푸는 이야기.')],
}
MOVIES = {
 'mystery': [('나이브스 아웃','수상한 가족과 날카로운 탐정이 등장하는 반전 추리극.'),('에놀라 홈즈','셜록의 동생이 직접 사건을 해결하는 통쾌한 모험.')],
 'fantasy': [('해리 포터와 마법사의 돌','마법 학교의 비밀과 우정에 빠져드는 첫 모험.'),('스파이더맨: 뉴 유니버스','다양한 세계의 스파이더맨들이 만나는 눈부신 애니메이션.')],
 'scifi': [('인터스텔라','우주를 넘나드는 탐험과 가족 이야기가 만나는 SF.'),('빅 히어로','로봇 친구와 함께 펼치는 따뜻하고 짜릿한 히어로 모험.')],
 'growth': [('인사이드 아웃','머릿속 감정들이 펼치는 웃기고 뭉클한 모험.'),('코코','음악과 가족의 의미를 찾아가는 화려한 애니메이션.')],
 'adventure': [('쥬만지: 새로운 세계','게임 속 세계에서 벌어지는 예측 불가 팀플레이.'),('모아나','바다를 향해 나아가는 소녀의 신나는 항해.')],
 'creativity': [('웡카','상상력 가득한 초콜릿과 마법 같은 도전.'),('레고 무비','평범한 주인공이 창의력으로 세상을 바꾸는 이야기.')],
 'heart': [('패딩턴 2','친절한 곰이 만들어 내는 유쾌하고 따뜻한 소동.'),('주토피아','서로 다른 동물들이 편견을 넘어 사건을 해결하는 이야기.')],
 'action': [('스파이더맨: 홈커밍','학교생활과 히어로 임무 사이에서 벌어지는 소동.'),('인크레더블','특별한 능력을 가진 가족의 박진감 넘치는 팀플레이.')],
}

TYPES = {
 'INTJ': ('🧩 전략가','mystery','scifi','복잡한 퍼즐과 거대한 상상에 도전!'),
 'INTP': ('🔬 탐구자','scifi','mystery','끝까지 파고들고 싶은 수수께끼가 딱!'),
 'ENTJ': ('🚀 지휘관','action','scifi','큰 목표와 짜릿한 선택이 기다려!'),
 'ENTP': ('💡 발명가','creativity','mystery','예상 못 한 전개와 번뜩이는 아이디어!'),
 'INFJ': ('🌙 통찰가','heart','growth','여운이 오래 남는 특별한 이야기!'),
 'INFP': ('🌈 몽상가','fantasy','heart','상상력과 따뜻한 감성을 동시에!'),
 'ENFJ': ('🤝 응원단장','growth','heart','함께 성장하는 이야기에 푹 빠져 봐!'),
 'ENFP': ('🎉 활동가','adventure','creativity','지루할 틈 없는 엉뚱한 모험!'),
 'ISTJ': ('📋 현실주의자','mystery','growth','탄탄한 이야기와 숨은 단서를 찾아봐!'),
 'ISFJ': ('🧸 수호자','heart','growth','따뜻한 우정과 마음을 움직이는 순간!'),
 'ESTJ': ('🏆 관리자','action','mystery','속도감 있는 사건과 똑똑한 해결책!'),
 'ESFJ': ('☀️ 친선대사','heart','adventure','사람들과 함께하는 신나는 이야기!'),
 'ISTP': ('🛠️ 장인','action','scifi','기발한 기술과 손에 땀 나는 모험!'),
 'ISFP': ('🎨 예술가','creativity','heart','색다른 세계와 감각적인 장면을 즐겨 봐!'),
 'ESTP': ('⚡ 모험가','action','adventure','시작부터 끝까지 박진감 넘치게!'),
 'ESFP': ('🎤 엔터테이너','adventure','creativity','웃음과 놀라움이 팡팡 터지는 이야기!'),
}

st.markdown('''<style>
.stApp {background:linear-gradient(145deg,#f8f6ff,#f0f8ff 55%,#fff9f1)}
.block-container{max-width:800px;padding-top:2rem}
.hero{background:white;border-radius:24px;padding:24px;text-align:center;box-shadow:0 5px 22px #4f46851a;margin-bottom:20px}
.hero h1{color:#31265c;margin:0 0 8px}
.item{background:white;border:1px solid #e9e3fb;border-radius:18px;padding:18px;margin:12px 0;box-shadow:0 3px 12px #4f468510}
.item h3{margin:0 0 8px;color:#332960}
.item p{margin:6px 0;color:#424052}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>📚🎬 MBTI 취향 탐험대</h1><p>오늘 뭐 읽고, 뭐 볼까? 내 취향 보물찾기! ✨</p></div>',unsafe_allow_html=True)
st.write('MBTI를 골라 봐! 재미있게 몰입할 수 있는 책 2권과 영화 2편을 추천해 줄게. 😎')
choice = st.selectbox('🧠 나의 MBTI', ['선택해 줘!'] + list(TYPES))
if choice == '선택해 줘!':
    st.info('👆 먼저 MBTI를 선택하면 추천 결과가 나타나!')
else:
    nickname, book_key, movie_key, message = TYPES[choice]
    st.success(f'{choice} · {nickname} — {message}')
    st.subheader('📚 책 추천 TOP 2')
    for idx, (title, author, desc) in enumerate(BOOKS[book_key], 1):
        st.markdown(f'<div class="item"><h3>📖 {idx}. {title}</h3><p>✍️ 작가: {author}</p><p>✨ 읽는 재미: {desc}</p></div>', unsafe_allow_html=True)
    st.subheader('🎬 영화 추천 TOP 2')
    for idx, (title, desc) in enumerate(MOVIES[movie_key], 1):
        st.markdown(f'<div class="item"><h3>🍿 {idx}. {title}</h3><p>🎯 관람 포인트: {desc}</p></div>', unsafe_allow_html=True)
    st.caption('🎟️ 영화 관람등급은 국가·서비스에 따라 다를 수 있으니 시청 전에 확인해 줘!')
st.divider()
st.caption('💡 MBTI는 취향을 확정하는 검사가 아니야. 추천은 재미를 위한 큐레이션이니 마음에 드는 작품부터 즐겨 봐!')
