# 📍 HBT Routing System - Hệ Thống Tìm Đường Thông Minh Quận Hai Bà Trưng

## 🏗 Cấu Trúc Dự Án (Project Structure)

```text
hbt-routing-system/
├── data/                       # Quản lý dữ liệu bản đồ
│   ├── raw/                    # Chứa file .osm gốc (ví dụ: haibatrung.osm)
│   └── processed/              # Dữ liệu đồ thị sau khi đã parser (JSON/Pickle)
├── src/                        # Mã nguồn chính (Core Logic)
│   ├── data_processing/        # Lớp xử lý dữ liệu (ETL Pipeline)
│   │   ├── osm_parser.py       # Chuyển đổi dữ liệu XML sang đồ thị (Graph)
│   │   └── spatial_index.py    # Xử lý chỉ mục không gian (R-Tree/KD-Tree)
│   ├── core/                   # Lớp thuật toán cốt lõi
│   │   ├── a_star.py           # Thuật toán A* với Heuristic Haversine
│   │   └── weights.py          # Tính toán trọng số cạnh (khoảng cách + traffic)
│   ├── api/                    # Giao tiếp giữa Backend và Frontend
│   │   └── main.py             # FastAPI/Flask khởi tạo các endpoint
│   └── utils/                  # Các hàm hỗ trợ tính toán tọa độ
├── frontend/                   # Giao diện hiển thị bản đồ (React/Leaflet)
│   └── ...                     # Các component UI/UX
├── .gitignore                  # Loại bỏ venv, node_modules và file rác
├── requirements.txt            # Danh sách thư viện Python cần thiết
└── main.py                     # Entry point để khởi chạy ứng dụng

