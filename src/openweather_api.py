import requests
import datetime
from src.database import get_db
from src.data_processing import preprocess_weather_data

API_KEY = "3cdce5dd0846a9d6860c957b6d7d3f8f"

db = get_db()
weather_collection = db["weather_data"]

# WEATHER + AIR QUALITY
def fetch_weather_data(city: str, save=True):
    """Lấy dữ liệu thời tiết hiện tại & không khí"""
    try:
        url_weather = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=vi"
        weather_res = requests.get(url_weather).json()

        if weather_res.get("cod") != 200:
            return {"error": f"Không tìm thấy dữ liệu cho {city}"}

        lat, lon = weather_res["coord"]["lat"], weather_res["coord"]["lon"]
        url_air = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_res = requests.get(url_air).json()

        raw_data = {
            "city": weather_res["name"],
            "lat": lat,
            "lon": lon,
            "timestamp": datetime.datetime.fromtimestamp(weather_res["dt"]),
            "temperature": weather_res["main"]["temp"],
            "humidity": weather_res["main"]["humidity"],
            "pressure": weather_res["main"]["pressure"],
            "wind_speed": weather_res["wind"]["speed"],
            "weather_desc": weather_res["weather"][0]["description"],
            "aqi": air_res["list"][0]["main"]["aqi"],
            "components": air_res["list"][0]["components"]
        }

        processed = preprocess_weather_data(raw_data)
        if not processed:
            return {"error": "Lỗi xử lý dữ liệu"}

        if save:
            weather_collection.insert_one(processed)

        return processed

    except Exception as e:
        return {"error": str(e)}
    

# === LẤY DỰ BÁO 7 NGÀY ===
def fetch_forecast_7days(city: str, cnt: int = 7):
    """Lấy dữ liệu dự báo 7 ngày từ OpenWeather API"""
    try:
        # B1: Lấy tọa độ từ tên thành phố
        coord_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        coord_res = requests.get(coord_url).json()
        if coord_res.get("cod") != 200:
            return {"error": f"Không tìm thấy thành phố {city}"}

        lat = coord_res["coord"]["lat"]
        lon = coord_res["coord"]["lon"]

        # B2: Lấy dữ liệu dự báo 7 ngày
        url = f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={cnt}&appid={API_KEY}&units=metric&lang=vi"
        res = requests.get(url).json()

        if str(res.get("cod")) not in ["200", 200]:
            return {"error": f"Không có dữ liệu dự báo cho {city}"}

        # B3: Chuẩn hóa dữ liệu
        forecast_list = []
        for item in res["list"]:
            forecast_list.append({
                "timestamp": datetime.datetime.fromtimestamp(item["dt"]),
                "temp_min": item["temp"]["min"],
                "temp_max": item["temp"]["max"],
                "humidity": item["humidity"],
                "pressure": item["pressure"],
                "wind_speed": item["speed"],
                "weather_desc": item["weather"][0]["description"],
                "rain": item.get("rain", 0),
                "clouds": item.get("clouds", 0)
            })

        return forecast_list

    except Exception as e:
        return {"error": str(e)}