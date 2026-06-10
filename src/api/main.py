import os
import sys
import pickle
import traceback
import time  
import heapq  # 💡 Thêm thư viện để chạy Dijkstra Vô hướng cho Admin
from collections import defaultdict  # 💡 Thêm thư viện cấu trúc dữ liệu
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Tuple, Any

# Thêm đường dẫn để FastAPI tìm thấy các module trong src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data_processing.spatial_index import SpatialIndex
from src.data_processing.traffic_manager import TrafficManager
from src.algorithms.astar import AStarSolver
from src.algorithms.dijkstra import DijkstraSolver
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
dijkstra_solver = None

@app.on_event("startup")
async def startup_event():
    global graph_data, spatial_index, traffic_mgr, cost_calc, solver, dijkstra_solver
    
    print("\n--- 🚀 Đang khởi động hệ thống Backend ---")
    
    if not os.path.exists(DATA_PATH) or not os.path.exists(INDEX_PATH):
        print(f"❌ CRITICAL ERROR: Không tìm thấy file dữ liệu tại {DATA_PATH}")
        return

    try:
        with open(DATA_PATH, 'rb') as f:
            raw_data = pickle.load(f)
            
        clean_graph = {}
        for u, neighbors in raw_data['graph'].items():
            clean_neighbors = {str(v): data for v, data in neighbors.items()}
            clean_graph[str(u)] = clean_neighbors
            
        clean_nodes = {str(node_id): coords for node_id, coords in raw_data['nodes'].items()}
        
        graph_data = {
            'graph': clean_graph,
            'nodes': clean_nodes
        }

        traffic_mgr = TrafficManager()
        cost_calc = CostCalculator(traffic_manager=traffic_mgr)
        solver = AStarSolver(graph_data['graph'], graph_data['nodes'])
        dijkstra_solver = DijkstraSolver(graph_data['graph'], graph_data['nodes'])
        
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
    algorithm: str = "astar"

class TrafficPathUpdate(BaseModel):
    path_coordinates: List[Any] 
    congestion: float = 1.0
    flood: float = 0.0

# --- ENDPOINTS ---
@app.post("/find-path")
def find_path(request: RouteRequest):
    if spatial_index is None or solver is None or dijkstra_solver is None:
        return {"status": "error", "message": "Hệ thống chưa sẵn sàng."}

    try:
        u_start = spatial_index.find_nearest_node(request.start_lat, request.start_lon, max_distance_km=0.7)
        v_end = spatial_index.find_nearest_node(request.end_lat, request.end_lon, max_distance_km=0.7)

        if u_start is None or v_end is None:
            return {"status": "outside_bounds", "message": "Vị trí nằm ngoài phạm vi."}

        start_time = time.time()

        if request.algorithm == "dijkstra":
            path_ids = dijkstra_solver.solve(start_node=u_start, goal_node=v_end, cost_fn=cost_calc.dynamic_cost)
        else:
            path_ids = solver.solve(start_node=u_start, goal_node=v_end, cost_fn=cost_calc.dynamic_cost)

        exec_time_ms = round((time.time() - start_time) * 1000, 2)

        if not path_ids:
            return {"status": "error", "message": "Khu vực bị cô lập."}

        path_coords = [{"lat": graph_data['nodes'][node_id][0], "lng": graph_data['nodes'][node_id][1]} for node_id in path_ids]

        return {
            "status": "success",
            "path": path_coords,
            "metadata": {"algorithm": request.algorithm, "execution_time_ms": exec_time_ms}
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi nội bộ: {str(e)}"}

@app.post("/update-traffic")
def update_traffic(update: TrafficPathUpdate):
    if not traffic_mgr or not spatial_index or not graph_data:
        return {"status": "error", "message": "Hệ thống chưa sẵn sàng."}

    try:
        if not update.path_coordinates or len(update.path_coordinates) < 2:
            return {"status": "error", "message": "Dữ liệu tọa độ vẽ không đủ."}

        start_pt = update.path_coordinates[0]
        end_pt = update.path_coordinates[-1]

        def extract_lat_lon(pt):
            if isinstance(pt, dict):
                return float(pt.get('lat') or pt.get('0')), float(pt.get('lng') or pt.get('lon') or pt.get('1'))
            return float(pt[0]), float(pt[1])

        lat1, lon1 = extract_lat_lon(start_pt)
        lat2, lon2 = extract_lat_lon(end_pt)

        u_start = spatial_index.find_nearest_node(lat1, lon1, max_distance_km=0.7)
        v_end = spatial_index.find_nearest_node(lat2, lon2, max_distance_km=0.7)

        if u_start is None or v_end is None:
            return {"status": "error", "message": "Điểm vẽ nằm ngoài phạm vi."}

        # 🚀 TÍNH NĂNG MỚI: TÌM ĐƯỜNG VÔ HƯỚNG (BỎ QUA LUẬT 1 CHIỀU) DÀNH RIÊNG CHO ADMIN
        def find_undirected_path(start, goal):
            # Tạo đồ thị vô hướng tạm thời (nhận diện mọi node kề cạnh nhau)
            undirected_adj = defaultdict(set)
            for u, neighbors in graph_data['graph'].items():
                for v in neighbors:
                    undirected_adj[u].add(v)
                    undirected_adj[v].add(u)
                    
            open_set = [(0, start)]
            came_from = {}
            g_score = {start: 0}
            
            while open_set:
                curr_g, current = heapq.heappop(open_set)
                
                if current == goal:
                    path = [current]
                    while current in came_from:
                        current = came_from[current]
                        path.append(current)
                    return path[::-1]
                    
                for neighbor in undirected_adj[current]:
                    # Tính khoảng cách hình học ngắn nhất để nối đường thẳng
                    lat_c, lon_c = graph_data['nodes'][current]
                    lat_n, lon_n = graph_data['nodes'][neighbor]
                    dist = ((lat_c - lat_n)**2 + (lon_c - lon_n)**2)**0.5
                    
                    tentative_g = curr_g + dist
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        g_score[neighbor] = tentative_g
                        came_from[neighbor] = current
                        heapq.heappush(open_set, (tentative_g, neighbor))
            return None

        # Sử dụng thuật toán Vô hướng thay cho A*
        path_nodes = find_undirected_path(u_start, v_end)

        if not path_nodes:
            return {"status": "error", "message": "Không tìm thấy đường vật lý kết nối 2 điểm này."}

        # Áp dụng trọng số kẹt xe/ngập lụt cho cả 2 chiều của đoạn đường vật lý
        updated_count = 0
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i+1]
            traffic_mgr.update_live_traffic(u, v, update.congestion, update.flood)
            traffic_mgr.update_live_traffic(v, u, update.congestion, update.flood)
            updated_count += 1

        return {"status": "success", "message": f"Đã áp dụng hệ số cho {updated_count} đoạn đường."}
    except Exception as e:
        print(f"🔥 Lỗi update-traffic: {e}")
        return {"status": "error", "message": f"Lỗi nội bộ: {str(e)}"}

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