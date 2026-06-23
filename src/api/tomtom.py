import os
import requests
import json
from datetime import datetime

# ================== CẤU HÌNH ==================
API_KEY = "wZqXIYyYQvOiaYlBN0TmmZG3NNXPKQ5N"  # Thay bằng key của bạn

# Bounding box (minLon, minLat, maxLon, maxLat)
BBOX = "105.825,20.985,105.878,21.028"

# Các tham số khác
LANGUAGE = "en-GB"
FIELDS = "{incidents{type,geometry{type,coordinates},properties{iconCategory,magnitudeOfDelay,events{description,code}}}}" 
TIME_VALIDITY = "present"

# Tên file output
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "tomtom_traffic_incidents.json")
# =============================================

class TomTom:
    def get_traffic_incidents():
        url = "https://api.tomtom.com/traffic/services/5/incidentDetails"
        
        params = {
            "key": API_KEY,
            "bbox": BBOX,
            "fields": FIELDS,
            "language": LANGUAGE,
            "timeValidityFilter": TIME_VALIDITY,
            #"categoryFilter": "1,6,8,9",  # Uncomment để lọc loại sự cố (Accident, Jam, RoadClosed, RoadWorks...)
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            
            # Kiểm tra lỗi
            if response.status_code != 200:
                print(f"Lỗi {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            data = {
                "timestamp": datetime.now().timestamp(),
                "incidents": data.get('incidents', [])
            }
            
            # Lưu vào file JSON
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Đã lưu {len(data.get('incidents', []))} sự cố giao thông vào file:")
            print(f"   {OUTPUT_FILE}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối: {e}")
            return None

if __name__ == "__main__":
    get_traffic_incidents()