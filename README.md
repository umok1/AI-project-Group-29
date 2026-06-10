# 📍 HBT Routing System - Hệ Thống Tìm Đường Thông Minh Quận Hai Bà Trưng

## 🏗 Cấu Trúc Dự Án (Project Structure)

```text
hbt-routing-system/
├── data/                       # Quản lý dữ liệu bản đồ
│   ├── raw/                    # Chứa file .osm gốc (ví dụ: haibatrung.osm)
│   └── processed/              # Dữ liệu đồ thị sau khi parse (hbt_graph.pkl, spatial_index.pkl)
│
├── src/                        # Mã nguồn Backend (Core Logic & API)
│   ├── data_processing/        # Lớp xử lý dữ liệu (ETL Pipeline)
│   │   ├── osm_parser.py       # Chuyển đổi dữ liệu XML sang cấu trúc đồ thị (Graph)
│   │   ├── spatial_index.py    # Xử lý chỉ mục không gian (KD-Tree) để truy vấn tọa độ
│   │   └── traffic_manager.py  # Quản lý trạng thái giao thông động (Tắc đường, Ngập lụt)
│   │
│   ├── algorithms/             # Lớp thuật toán cốt lõi
│   │   ├── astar.py            # Thuật toán A* tối ưu hóa với hàm Heuristic (Haversine)
│   │   ├── dijkstra.py         # Thuật toán Dijkstra dùng để đối chiếu và so sánh tốc độ
│   │   └── cost_functions.py   # Các hàm tính toán trọng số cạnh dựa trên tình trạng giao thông
│   │
│   ├── api/                    # Cổng giao tiếp API (FastAPI)
│   │   └── main.py             # Khởi tạo server, nạp dữ liệu và xử lý các endpoint
│   │
│   └── utils/                  # Các hàm tiện ích hỗ trợ
│       └── geo_utils.py        # Chứa công cụ tính toán địa lý (vd: haversine_distance)
│
├── frontend/                   # Giao diện người dùng (ReactJS & Leaflet)
│   ├── src/
│   │   ├── components/         # Các thành phần UI độc lập
│   │   │   ├── MapView.js      # Component hiển thị bản đồ và vẽ route
│   │   │   ├── SearchPanel.js  # Thanh tìm kiếm địa điểm tích hợp Nominatim API
│   │   │   └── TrafficLegend.js# Chú giải bản đồ
│   │   ├── api.js              # Cấu hình Axios gọi API xuống Backend
│   │   └── App.js              # Khung giao diện chính và logic điều khiển trạng thái
│   └── package.json            # Danh sách thư viện Node.js
│
├── .gitignore                  # Bỏ qua các file môi trường (venv, node_modules) khi push Git
├── requirements.txt            # Danh sách thư viện Python cần thiết (FastAPI, Uvicorn, v.v.)
└── README.md                   # Tài liệu hướng dẫn dự án