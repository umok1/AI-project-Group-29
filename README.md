# 📍 HBT Routing System - Hệ Thống Tìm Đường Thông Minh Quận Hai Bà Trưng trong trường hợp bất lợi

## 🏗 Cấu Trúc Dự Án (Project Structure)

```text
hbt-routing-system/
├── data/                       # Quản lý dữ liệu bản đồ
│   ├── raw/                    # Chứa file .osm gốc 
│   └── processed/              # Dữ liệu đồ thị sau khi parse và dữ liệu tắc đường lấy từ Tom Tom API
│
├── src/                        # Mã nguồn Backend
│   ├── data_processing/        # Lớp xử lý dữ liệu 
│   │   ├── osm_parser.py       # Chuyển đổi dữ liệu XML sang cấu trúc đồ thị (Graph)
│   │   ├── spatial_index.py    # Xử lý chỉ mục không gian (KD-Tree) để truy vấn tọa độ
│   │   └── traffic_manager.py  # Quản lý trạng thái giao thông động (Tắc đường, Ngập lụt)
│   │
│   ├── algorithms/             # Lớp thuật toán cốt lõi
│   │   ├── astar.py            # Thuật toán A* tối ưu hóa với hàm Heuristic (Haversine)
│   │   ├── dijkstra.py         # Thuật toán Dijkstra 
│   │   └── cost_functions.py   # Các hàm tính toán trọng số cạnh dựa trên tình trạng giao thông
│   │
│   ├── api/                    # Cổng giao tiếp API (FastAPI)
│   │   ├── main.py             # Khởi tạo server, nạp dữ liệu và xử lý các endpoint
│   │   └── tomtom.py           # Tom Tom API cập nhật dữ liệu tắc đường theo thời gian thực
│   │
│   └── utils/                  # Các hàm tiện ích hỗ trợ
│       └── geo_utils.py        # Chứa công cụ tính toán địa lý (haversine_distance)
│
├── frontend/                   # Giao diện người dùng 
│   ├── src/
│   │   ├── components/         # Các thành phần UI độc lập
│   │   │   ├── MapView.js      # Component hiển thị bản đồ và vẽ route
│   │   │   ├── SearchPanel.js  # Thanh tìm kiếm địa điểm tích hợp Nominatim API
│   │   │   └── TrafficLegend.js# Chú giải bản đồ
│   │   ├── api.js              # Cấu hình Axios gọi API xuống Backend
│   │   └── App.js              # Khung giao diện chính và logic điều khiển trạng thái
│   └── package.json            # Danh sách thư viện Node.js
├── get_data.py                 # Lấy file dữ liệu CSV
├── .gitignore                  # Bỏ qua các file môi trường
├── requirements.txt            # Danh sách thư viện Python cần thiết (FastAPI, Uvicorn, v.v.)
└── README.md                   # Tài liệu hướng dẫn dự án

Hướng dẫn chạy dự án:\
B1 :Cài đặt môi trường ảo: python -m venv venv
   :Kích hoạt môi trường: venv\Scripts\activate
 +) Nếu có lỗi không cho phép kích hoạt venv trên Windows PowerShell:
   Mở PowerShell bằng quyền Admin (Run as Administrator) và chạy lệnh sau để cấp quyền thực thi script:
              Set-ExecutionPolicy Unrestricted -Scope CurrentUser
B2: Cài đặt thư viện : pip install -r requirements.txt; npm install
B3: Chuẩn bị tài nguyên và tiền xử lý dữ 
+) Mở new terminal\
+) Gõ lệnh python -m src.data_processing.osm_parser (Chỉ chạy một lần để xử lý dữ liệu)\
+) Gõ lệnh python -m uvicorn src.api.main:app --app-dir . --reload\ ( Khởi động backend)
+) New terminal khác -> chuyển sang command prompt ->
  gõ lần lượt 2 lệnh : cd frontend; npm start   (Khởi động frontend)
