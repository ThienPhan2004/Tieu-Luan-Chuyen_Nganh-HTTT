import streamlit as st
from src.auth import change_password

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

st.title("🔑 Đổi mật khẩu")

old_password = st.text_input("Mật khẩu hiện tại", type="password")
new_password = st.text_input("Mật khẩu mới", type="password")
confirm_password = st.text_input("Xác nhận mật khẩu mới", type="password")

if st.button("Đổi mật khẩu"):
    if new_password != confirm_password:
        st.error("Mật khẩu xác nhận không khớp!")
    elif change_password(st.session_state.username, old_password, new_password):
        st.success("Đổi mật khẩu thành công!")
    else:
        st.error("Mật khẩu hiện tại không đúng!")