import streamlit as st
st.title('동욱이 다이어트 1일차!')
st.text_input('이름을 입력하세요')
st.selectbox('얼마나 오래 갈까요?',['1분','10분','30분'])
st.button('인사말 생성')
