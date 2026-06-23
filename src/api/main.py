import os
import sys
import pickle
import traceback
import time
import json
from datetime import datetime  
import heapq
from collections import defaultdict
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
from src.utils.benchmark import run_routing_benchmark

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
TOMTOM_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "tomtom_traffic_incidents.json")

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
    visualize: bool = False 
    algorithm: str = "astar"

class TrafficPathUpdate(BaseModel):
    path_coordinates: List[Any] 
    congestion: float = 1.0
    flood: float = 0.0

class BenchmarkRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    algorithm: str = "astar" 
    num_runs: int = 100  

# --- ENDPOINTS ---
@app.post("/find-path")
def find_path(request: RouteRequest):
    if spatial_index is None or solver is None or dijkstra_solver is None:
        return {"status": "error", "message": "Hệ thống chưa sẵn sàng."}

    try:
        u_start = spatial_index.find_nearest_node(request.start_lat, request.start_lon, max_distance_km=99999.0)
        v_end = spatial_index.find_nearest_node(request.end_lat, request.end_lon, max_distance_km=99999.0)

        # Thông báo lỗi khi đồ thị bị hỏng hoàn toàn (không có Node nào)
        if u_start is None or v_end is None:
            return {"status": "error", "message": "Lỗi dữ liệu: Không tìm thấy đỉnh nào trên đồ thị."}

        # Bật cờ return_history=True và hứng 2 biến trả về (path_ids, visited_count)
        if request.algorithm == "dijkstra":
            path_ids, visited_count, visited_order_ids = dijkstra_solver.solve(
                start_node=u_start, goal_node=v_end, cost_fn=cost_calc.dynamic_cost, return_history=True
            )
        else:
            path_ids, visited_count, visited_order_ids = solver.solve(
                start_node=u_start, goal_node=v_end, cost_fn=cost_calc.dynamic_cost, return_history=True
            )
        if not request.visualize:
            visited_order_ids = []
        # Xử lý trường hợp không tìm thấy đường
        if not path_ids:
            return {"status": "error", "message": "Khu vực bị cô lập."}

        # Map ID thành tọa độ để vẽ trên UI
        path_coords = [{"lat": graph_data['nodes'][node_id][0], "lng": graph_data['nodes'][node_id][1]} for node_id in path_ids]
        visited_order = [{"lat": graph_data['nodes'][node_id][0], "lng": graph_data['nodes'][node_id][1]} for node_id in visited_order_ids]

        # Đẩy biến visited_count vào file JSON 
        return {
            "status": "success",
            "path": path_coords,
            "visited_count": visited_count,  # <-- Cột mốc quan trọng để giao diện bắt được
            "visited_order": visited_order,
            "metadata": {"algorithm": request.algorithm}
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
        
        #print(f"{lat1} {lon1}")
        #print(f"{lat2} {lon2}")

        u_start = spatial_index.find_nearest_node(lat1, lon1, max_distance_km=0.7)
        v_end = spatial_index.find_nearest_node(lat2, lon2, max_distance_km=0.7)
        
        #print(f"{u_start} {v_end}")
        
        if u_start is None or v_end is None:
            return {"status": "error", "message": "Lỗi dữ liệu: Không tìm thấy đỉnh nào trên đồ thị."}

        #  TÌM ĐƯỜNG VÔ HƯỚNG (BỎ QUA LUẬT 1 CHIỀU) DÀNH RIÊNG CHO ADMIN
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
        
@app.get("/tomtom-update-traffic")
def tomtom_update_traffic():
    if not os.path.exists(TOMTOM_DATA_PATH):
        print(f"❌ CRITICAL ERROR: Không tìm thấy file dữ liệu tại {TOMTOM_DATA_PATH}")
        data = TomTom.get_traffic_incidents()
        if not data:
            print("❌ Khởi tạo thất bại do lỗi API.")
            return
    try:
        with open(TOMTOM_DATA_PATH, "r", encoding="utf-8") as f:
            # Nạp dữ liệu từ file vào biến
            data = json.load(f)
        print("✅ Nạp file thành công!")
        timestamp = data.get("timestamp")
        current_time = datetime.now().timestamp()
        if current_time - timestamp >= 600:
            incidents_list = data.get("incidents", [])
            for incident in incidents_list:
                geometry = incident.get("geometry", {})
                if geometry.get("type") != "LineString":
                    continue
                
                raw_coords = geometry.get("coordinates", [])
                full_path = [(coord[1], coord[0]) for coord in raw_coords]
                
                if len(full_path) < 2:
                    continue
                
                segment_coords = [full_path[0], full_path[-1]]

                # Tạo một object TrafficPathUpdate riêng cho phân đoạn nhỏ này
                segment_update = TrafficPathUpdate(
                    path_coordinates=segment_coords,
                    congestion=1.0,
                    flood=0.0
                )
                update_traffic(segment_update)
                
            new_data = TomTom.get_traffic_incidents()
            if not new_data:
                print("❌ Khởi tạo thất bại do lỗi API, đang sử dụng dữ liệu cũ để cập nhật tình trạng giao thông...")
            else:
                data = new_data
        
        incidents_list = data.get("incidents", [])
        for incident in incidents_list:
            geometry = incident.get("geometry", {})
            if geometry.get("type") != "LineString":
                continue
            
            raw_coords = geometry.get("coordinates", [])
            full_path = [(coord[1], coord[0]) for coord in raw_coords]
            
            if len(full_path) < 2:
                continue
            
            properties = incident.get("properties", {})
            magnitude = properties.get("magnitudeOfDelay", 0)
            events = properties.get("events", [])
            is_closed = any(event.get("code") == 401 for event in events)

            if is_closed:
                congestion_weight = 999.0
            else:
                congestion_weight = 1.0 + (magnitude * 2)

            flood_weight = 0.0
            
            segment_coords = [full_path[0], full_path[-1]]
            # Tạo một object TrafficPathUpdate riêng cho phân đoạn nhỏ này
            segment_update = TrafficPathUpdate(
                path_coordinates=segment_coords,
                congestion=congestion_weight,
                flood=flood_weight
            )
            update_traffic(segment_update)
            
        return {"status": "success", "message": "Gọi TomTom API thành công!"}
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

@app.post("/benchmark")
def run_benchmark(request: BenchmarkRequest):
    if spatial_index is None or solver is None or dijkstra_solver is None:
        return {"status": "error", "message": "Hệ thống chưa sẵn sàng."}

    try:
        u_start = spatial_index.find_nearest_node(request.start_lat, request.start_lon, max_distance_km=99999.0)
        v_end = spatial_index.find_nearest_node(request.end_lat, request.end_lon, max_distance_km=99999.0)

        if u_start is None or v_end is None:
            return {"status": "error", "message": "Vị trí nằm ngoài phạm vi hỗ trợ."}

        # Chọn thuật toán
        current_solver = dijkstra_solver if request.algorithm == "dijkstra" else solver

        # 🚀 GỌI HÀM TỪ FILE BENCHMARK.PY 
        benchmark_result = run_routing_benchmark(
            solver_instance=current_solver,
            start_node=u_start,
            goal_node=v_end,
            cost_fn=cost_calc.dynamic_cost,
            num_runs=request.num_runs
        )
        
        if not benchmark_result:
            return {"status": "error", "message": "Không tìm thấy đường đi để đo benchmark."}

        # Ánh xạ ID ra tọa độ để gửi về Frontend vẽ đồ thị
        path_coords = [{"lat": graph_data['nodes'][node_id][0], "lng": graph_data['nodes'][node_id][1]} for node_id in benchmark_result["path_ids"]]

        # Trộn dữ liệu tọa độ với dữ liệu thống kê
        return {
            "status": "success",
            "path": path_coords,
            "metrics": {
                "algorithm": request.algorithm,
                "num_runs": benchmark_result["metrics"]["num_runs"],
                "min_ms": benchmark_result["metrics"]["min_ms"],
                "max_ms": benchmark_result["metrics"]["max_ms"],
                "avg_ms": benchmark_result["metrics"]["avg_ms"],
                "visited_nodes": benchmark_result["visited_nodes"],
                "path_nodes": len(path_coords)
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Lỗi nội bộ Benchmark: {str(e)}"}
