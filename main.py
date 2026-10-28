import streamlit as st
st.title('동욱이 다이어트 1일차!')
a=st.text_input('이름을 입력하세요')
b=st.selectbox('얼마나 오래 갈까요?',['1분','5분','10분'])
if st.button('인사말 생성'):
  st.write('반갑습니다!')
  st.info(a+'님, 안녕하세요!')
  st.warning(b+'라니! 정답입니다!')
  st.error('동욱이를 잘 아시네요!')
  st.foods()
