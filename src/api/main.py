import os
import sys
import pickle
import traceback
import time  # ⏱️ Thêm thư viện time để đo thời gian chạy
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Tuple

# Thêm đường dẫn để FastAPI tìm thấy các module trong src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data_processing.spatial_index import SpatialIndex
from src.data_processing.traffic_manager import TrafficManager
from src.algorithms.astar import AStarSolver
from src.algorithms.dijkstra import DijkstraSolver  # 🧠 Import thêm DijkstraSolver
from src.algorithms.cost_functions import CostCalculator

app = FastAPI(title="HBT Routing System API - Hai Ba Trung District")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "hbt_graph.pkl")
INDEX_PATH = os.path.join(BASE_DIR, "data", "processed", "spatial_index.pkl")

# Global variables
graph_data = None
spatial_index = None
traffic_mgr = None
cost_calc = None
solver = None
dijkstra_solver = None  # Biến toàn cục cho Dijkstra

@app.on_event("startup")
async def startup_event():
    global graph_data, spatial_index, traffic_mgr, cost_calc, solver, dijkstra_solver
    
    print("\n--- 🚀 Đang khởi động hệ thống Backend ---")
    
    if not os.path.exists(DATA_PATH) or not os.path.exists(INDEX_PATH):
        print(f"❌ CRITICAL ERROR: Không tìm thấy file dữ liệu tại {DATA_PATH}")
        return

    try:
        # 1. Load đồ thị
        with open(DATA_PATH, 'rb') as f:
            raw_data = pickle.load(f)
            
        # 2. Đồng bộ hóa ID sang String (Tránh lỗi so sánh String-Int)
        clean_graph = {}
        for u, neighbors in raw_data['graph'].items():
            clean_neighbors = {str(v): data for v, data in neighbors.items()}
            clean_graph[str(u)] = clean_neighbors
            
        clean_nodes = {str(node_id): coords for node_id, coords in raw_data['nodes'].items()}
        
        graph_data = {
            'graph': clean_graph,
            'nodes': clean_nodes
        }

        # 3. Khởi tạo Logic Bus và CÁC THUẬT TOÁN
        traffic_mgr = TrafficManager()
        cost_calc = CostCalculator(traffic_manager=traffic_mgr)
        solver = AStarSolver(graph_data['graph'], graph_data['nodes'])
        dijkstra_solver = DijkstraSolver(graph_data['graph'], graph_data['nodes'])  # Nạp Dijkstra
        
        # 4. Tải Spatial Index
        spatial_index = SpatialIndex.load_index(INDEX_PATH)

        if spatial_index:
            print("--- ✅ Hệ thống HBT Routing Backend đã đồng bộ và sẵn sàng ---")
        else:
            print("❌ Lỗi: Không thể khôi phục Spatial Index từ file .pkl")
        
    except Exception as e:
        print(f"❌ Lỗi khởi tạo nghiêm trọng: {e}")
        traceback.print_exc()

# --- SCHEMAS ---

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    algorithm: str = "astar"  # ⚙️ Thêm trường algorithm, mặc định là A*

class TrafficPathUpdate(BaseModel):
    path_coordinates: List[Tuple[float, float]]
    congestion: float = 1.0
    flood: float = 0.0

# --- ENDPOINTS ---

@app.post("/find-path")
def find_path(request: RouteRequest):
    print(f"\n[DEBUG] Yêu cầu tìm đường bằng thuật toán: {request.algorithm.upper()}")
    
    if spatial_index is None or solver is None or dijkstra_solver is None:
        return {
            "status": "error",
            "message": "Hệ thống chưa sẵn sàng hoặc dữ liệu chưa được nạp."
        }

    try:
        # Tìm Node gần nhất với ngưỡng 0.7km
        u_start = spatial_index.find_nearest_node(request.start_lat, request.start_lon, max_distance_km=0.7)
        v_end = spatial_index.find_nearest_node(request.end_lat, request.end_lon, max_distance_km=0.7)

        if u_start is None or v_end is None:
            return {
                "status": "outside_bounds",
                "message": f"Vị trí bạn chọn nằm ngoài phạm vi hỗ trợ của quận Hai Bà Trưng!"
            }

        # ⏱️ BẮT ĐẦU BẤM GIỜ
        start_time = time.time()

        # ⚙️ CHẠY THUẬT TOÁN ĐƯỢC CHỌN (Mặc định không lưu history)
        if request.algorithm == "dijkstra":
            path_ids = dijkstra_solver.solve(
                start_node=u_start, 
                goal_node=v_end, 
                cost_fn=cost_calc.dynamic_cost
            )
        else:
            path_ids = solver.solve(
                start_node=u_start, 
                goal_node=v_end, 
                cost_fn=cost_calc.dynamic_cost
            )

        # ⏱️ KẾT THÚC BẤM GIỜ
        exec_time_ms = round((time.time() - start_time) * 1000, 2)

        if not path_ids:
            return {
                "status": "error", 
                "message": "Không tìm thấy lộ trình. Có thể khu vực này đang bị cô lập hoàn toàn do ngập lụt nặng."
            }

        # Chuyển ID Node thành tọa độ Map
        path_coords = [{"lat": graph_data['nodes'][node_id][0], "lng": graph_data['nodes'][node_id][1]} for node_id in path_ids]

        # 📊 TRẢ VỀ METADATA THỐNG KÊ (Chỉ giữ lại thời gian)
        return {
            "status": "success",
            "path": path_coords,
            "metadata": {
                "algorithm": request.algorithm,
                "execution_time_ms": exec_time_ms
            }
        }
    except Exception as e:
        print(f"🔥 Runtime Error: {e}")
        return {"status": "error", "message": f"Lỗi xử lý nội bộ: {str(e)}"}

@app.post("/update-traffic")
def update_traffic(update: TrafficPathUpdate):
    if not traffic_mgr or not spatial_index or not solver:
        return {"status": "error", "message": "Hệ thống chưa sẵn sàng."}

    try:
        start_pt = update.path_coordinates[0]
        end_pt = update.path_coordinates[-1]

        u_start = spatial_index.find_nearest_node(start_pt[0], start_pt[1])
        v_end = spatial_index.find_nearest_node(end_pt[0], end_pt[1])

        if u_start is None or v_end is None:
            return {"status": "error", "message": "Vùng bạn vẽ nằm ngoài phạm vi bản đồ."}

        # Dùng A* để vẽ đoạn đường quản lý sự cố (Mặc định không cần history)
        path_nodes = solver.solve(
            start_node=u_start, 
            goal_node=v_end, 
            cost_fn=cost_calc.simple_distance_cost,
            return_history=False
        )
        
        # Vì A* trả về thẳng list khi return_history=False (do code A* mới trả tuple khi True), ta cần xử lý
        if isinstance(path_nodes, tuple):
            path_nodes = path_nodes[0]

        if not path_nodes:
            return {"status": "error", "message": "Không tìm thấy đường nối thực tế để gán hệ số."}

        updated_count = 0
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i+1]
            traffic_mgr.update_live_traffic(u, v, update.congestion, update.flood)
            traffic_mgr.update_live_traffic(v, u, update.congestion, update.flood)
            updated_count += 1

        return {"status": "success", "message": f"Đã áp dụng hệ số cho {updated_count} đoạn đường."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/reset-traffic")
def reset_traffic():
    if traffic_mgr:
        traffic_mgr.live_updates.clear()
        return {"status": "success", "message": "Đã khôi phục mạng lưới giao thông bình thường."}
    return {"status": "error", "message": "Manager chưa được khởi tạo."}

@app.get("/active-traffic")
def get_active_traffic():
    if not traffic_mgr or not graph_data:
        return []

    active_segments = []
    for (u, v), info in traffic_mgr.live_updates.items():
        if u in graph_data['nodes'] and v in graph_data['nodes']:
            active_segments.append({
                "from": {"lat": graph_data['nodes'][u][0], "lng": graph_data['nodes'][u][1]},
                "to": {"lat": graph_data['nodes'][v][0], "lng": graph_data['nodes'][v][1]},
                "type": "flood" if info.get('flood', 0) > 0 else "congestion",
                "penalty": info.get('flood') if info.get('flood', 0) > 0 else info.get('congestion', 1.0)
            })
    return active_segments