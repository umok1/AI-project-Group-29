import heapq
import os
import sys
from collections import defaultdict

# Thêm đường dẫn gốc của project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.geo_utils import haversine_distance

class AStarSolver:
    def __init__(self, graph, nodes):
        """
        graph: Adjacency list {u: {v: edge_data}}
        nodes: Tọa độ {node_id: (lat, lon)}
        """
        self.graph = graph
        self.nodes = nodes
        # Ngưỡng chặn đường đồng bộ với TrafficManager/CostCalculator
        self.INF_THRESHOLD = 999999.0

    def heuristic(self, u, v):
        """Hàm h(n): Khoảng cách chim bay"""
        try:
            lat1, lon1 = self.nodes[u]
            lat2, lon2 = self.nodes[v]
            return haversine_distance(lat1, lon1, lat2, lon2)
        except (KeyError, TypeError):
            return self.INF_THRESHOLD

    def solve(self, start_node, goal_node, cost_fn=None, return_history=False):
        """
        Tìm đường đi tối ưu A* với chi phí động.
        """
        # Kiểm tra node đầu cuối có tồn tại không
        if start_node not in self.nodes or goal_node not in self.nodes:
            print(f"Lỗi: Node {start_node} hoặc {goal_node} không tồn tại trong dữ liệu.")
            return (None, 0) if return_history else None

        # Priority Queue: (f_score, current_node)
        open_set = []
        heapq.heappush(open_set, (0, start_node))

        came_from = {}
        
        # g_score: Chi phí thực tế từ điểm xuất phát
        g_score = defaultdict(lambda: float('inf'))
        g_score[start_node] = 0

        # f_score[n] = g_score[n] + h_score[n]
        f_score = defaultdict(lambda: float('inf'))
        f_score[start_node] = self.heuristic(start_node, goal_node)

        # Tập hợp các node đã xử lý xong
        closed_set = set()
        
        # Biến đếm số lượng đỉnh ĐÃ RÚT RA khỏi hàng đợi để xử lý
        visited_count = 0
        visited_order = [] # Nhật ký loang màu

        while open_set:
            # Lấy node có f_score thấp nhất
            current_f, current = heapq.heappop(open_set)

            # Bỏ qua nếu đã duyệt
            if current in closed_set:
                continue
                
            # Ghi nhận đỉnh đang được quét
            if return_history:
                visited_count += 1
                visited_order.append(current)

            # Nếu đã đến đích
            if current == goal_node:
                path = self._reconstruct_path(came_from, current)
                return (path, visited_count, visited_order) if return_history else path
            
            closed_set.add(current)

            # Lấy danh sách láng giềng
            neighbors = self.graph.get(current, {})
            u_coord = self.nodes[current]

            for neighbor, edge_data in neighbors.items():
                if neighbor in closed_set:
                    continue

                v_coord = self.nodes[neighbor]

                # 1. Tính trọng số cạnh (weight) từ CostCalculator
                if cost_fn:
                    weight = cost_fn(current, neighbor, u_coord, v_coord, edge_data)
                else:
                    weight = edge_data.get('weight', self.heuristic(current, neighbor))

                # 2. KIỂM TRA CHẶN ĐƯỜNG: Nếu ngập lụt nặng hoặc bị chặn
                if weight >= self.INF_THRESHOLD:
                    continue

                # 3. Tính toán g_score mới
                tentative_g_score = g_score[current] + weight

                if tentative_g_score < g_score[neighbor]:
                    # Đây là con đường tốt nhất được tìm thấy tính đến thời điểm này
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    
                    # f(n) = g(n) + h(n)
                    h_n = self.heuristic(neighbor, goal_node)
                    f_score[neighbor] = tentative_g_score + h_n
                    
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Không tìm thấy đường đi
        if return_history:
            return None, visited_count, visited_order
        return None

    def _reconstruct_path(self, came_from, current):
        """Tái cấu trúc lại mảng ID node từ đích về nguồn"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]