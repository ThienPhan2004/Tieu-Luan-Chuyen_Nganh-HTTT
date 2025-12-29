import datetime
from src.database import get_db

db = get_db()
weather_collection = db["weather_data"]

def preprocess_weather_data(raw_data: dict) -> dict:
    """
    Tiền xử lý dữ liệu thô từ API OpenWeather:
    - Làm sạch, chuẩn hóa kiểu dữ liệu.
    - Thêm timestamp chuẩn ISO.
    """
    try:
        return {
            "city": raw_data.get("city"),
            "lat": float(raw_data.get("lat", 0)),
            "lon": float(raw_data.get("lon", 0)),
            "timestamp": raw_data.get("timestamp", datetime.datetime.now()),
            "temperature": round(float(raw_data.get("temperature", 0)), 2),
            "humidity": int(raw_data.get("humidity", 0)),
            "pressure": int(raw_data.get("pressure", 0)),
            "wind_speed": round(float(raw_data.get("wind_speed", 0)), 2),
            "weather_desc": str(raw_data.get("weather_desc", "")).capitalize(),
            "aqi": int(raw_data.get("aqi", 0)),
            "components": raw_data.get("components", {})
        }
    except Exception as e:
        print(f"[preprocess_weather_data] Lỗi xử lý dữ liệu: {e}")
        return None


def get_weather_data(city: str):
    """Lấy bản ghi mới nhất từ MongoDB cho 1 thành phố"""
    record = (
        weather_collection.find({"city": city})
        .sort("timestamp", -1)
        .limit(1)
    )

    data = list(record)
    if not data:
        return None

    doc = data[0]
    return {
        "city": doc["city"],
        "temperature": doc["temperature"],
        "humidity": doc["humidity"],
        "pressure": doc["pressure"],
        "wind_speed": doc["wind_speed"],
        "aqi": doc["aqi"],
        "weather_desc": doc["weather_desc"],
        "lat": doc["lat"],
        "lon": doc["lon"],
    }
