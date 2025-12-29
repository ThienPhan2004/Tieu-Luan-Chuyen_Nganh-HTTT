import streamlit as st
from src.database import get_db
from src.data_processing import get_weather_data
from src.openweather_api import fetch_weather_data
import time
import base64
from datetime import datetime

# KIỂM TRA QUYỀN
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.switch_page("app.py")

elif st.session_state.role != "user":
    st.error("❌ Chỉ người dùng thông thường mới được truy cập trang này!")
    st.stop()

# HÌNH NỀN
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        h1 {{
            text-align: center;
            color: white;
            margin-bottom: 2rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_from_local("images/pexels-brett-sayles-912364.jpg")

# KHỞI TẠO
st.title("⭐ Địa điểm yêu thích")

db = get_db()
favorites_col = db["favorites"]
weather_collection = db["weather_data"]

fav_doc = favorites_col.find_one({"username": st.session_state.username})
favorites = fav_doc.get("favorites", []) if fav_doc else []

# Trạng thái xác nhận xóa
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

# NÚT CẬP NHẬT TOÀN BỘ
if favorites:
    if st.button("🔄 Cập nhật tất cả địa điểm", use_container_width=True):
        progress = st.progress(0)
        total = len(favorites)
        updated, failed = 0, 0

        for i, city in enumerate(favorites):
            result = fetch_weather_data(city, save=True)
            if "error" in result:
                failed += 1
                st.warning(f"⚠️ {city}: {result['error']}")
            else:
                updated += 1
                st.success(
                    f"✅ {city} cập nhật lúc {result['timestamp'].strftime('%H:%M')}"
                )

            progress.progress((i + 1) / total)
            time.sleep(0.3)

        st.info(f"Hoàn tất: {updated} thành công, {failed} thất bại")
        st.rerun()

st.divider()

# DANH SÁCH ĐỊA ĐIỂM YÊU THÍCH
if not favorites:
    st.info("⭐ Bạn chưa có địa điểm yêu thích nào.")
else:
    for location in favorites:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            weather_data = get_weather_data(location)
            if not weather_data:
                st.warning(f"Không tìm thấy dữ liệu cho {location}")
                continue

            # THÔNG TIN THỜI TIẾT
            with col1:
                st.write(f"### 🌇 {weather_data['city']}")
                st.write(f"**{weather_data['weather_desc'].capitalize()}**")
                st.write(
                    f"🌡️ {weather_data['temperature']}°C — "
                    f"💧 {weather_data['humidity']}% — "
                    f"🌬️ {weather_data['wind_speed']} m/s"
                )
                st.write(f"🌫️ AQI: {weather_data['aqi']}")

            # NÚT CẬP NHẬT
            with col2:
                if st.button("🔁 Cập nhật", key=f"update_{location}"):
                    new_data = fetch_weather_data(location, save=True)
                    if "error" in new_data:
                        st.error(f"Lỗi cập nhật {location}: {new_data['error']}")
                    else:
                        st.success(f"Đã cập nhật {location}")
                        st.rerun()

            # NÚT CHI TIẾT (ĐI SANG TRANG CHỦ)
            with col3:
                if st.button("📊 Chi tiết", key=f"detail_{location}"):
                    st.session_state["selected_city"] = location
                    st.switch_page("pages/Trang chủ.py")  # đổi path nếu khác

            # NÚT XÓA
            with col4:
                if st.button("❌ Xóa", key=f"del_{location}"):
                    st.session_state.confirm_delete = location

        st.divider()

# HỘP XÁC NHẬN XÓA
if st.session_state.confirm_delete:
    location_to_delete = st.session_state.confirm_delete

    st.warning(
        f"⚠️ Bạn có chắc chắn muốn xóa '{location_to_delete}' khỏi danh sách yêu thích không?"
    )

    col_yes, col_no = st.columns(2)

    with col_yes:
        if st.button("✅ Có, xóa"):
            favorites_col.update_one(
                {"username": st.session_state.username},
                {"$pull": {"favorites": location_to_delete}}
            )
            st.success(f"Đã xóa {location_to_delete} khỏi danh sách yêu thích!")
            st.session_state.confirm_delete = None
            st.rerun()

    with col_no:
        if st.button("❌ Không"):
            st.session_state.confirm_delete = None
            st.info("Đã hủy thao tác.")
            st.rerun()
