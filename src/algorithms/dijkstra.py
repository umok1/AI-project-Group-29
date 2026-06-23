import heapq
import os
import sys
from collections import defaultdict

# Thêm đường dẫn gốc của project để import dễ dàng (nếu cần test độc lập)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

class DijkstraSolver:
    def __init__(self, graph, nodes):
        """
        Khởi tạo thuật toán Dijkstra.
        - graph: Danh sách kề {u: {v: edge_data}}
        - nodes: Tọa độ các đỉnh {node_id: (lat, lon)}
        """
        self.graph = graph
        self.nodes = nodes
        # Ngưỡng vô cực dùng để chặn các đường bị ngập lụt (flood)
        self.INF_THRESHOLD = 999999.0

    def solve(self, start_node, goal_node, cost_fn=None, return_history=False):
        """
        Tìm đường đi ngắn nhất bằng thuật toán Dijkstra.
        """
        # Kiểm tra tính hợp lệ của điểm đầu/cuối
        if start_node not in self.nodes or goal_node not in self.nodes:
            print(f"❌ Dijkstra Lỗi: Node {start_node} hoặc {goal_node} không tồn tại trong đồ thị.")
            return (None, 0, []) if return_history else None

        # Priority Queue lưu trữ (chi_phí_g, node_hiện_tại)
        # Dijkstra luôn ưu tiên mở rộng đỉnh có chi phí từ điểm bắt đầu là nhỏ nhất
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        
        # came_from dùng để truy vết đường đi sau khi tìm thấy đích
        came_from = {}
        
        # g_score: Khoảng cách thực tế tích lũy từ điểm xuất phát đến các đỉnh
        g_score = defaultdict(lambda: float('inf'))
        g_score[start_node] = 0
        
        # Tập hợp các đỉnh đã chốt (không cần duyệt lại)
        closed_set = set()
        
        # Biến đếm số lượng đỉnh ĐÃ RÚT RA khỏi hàng đợi để xử lý
        visited_count = 0 
        visited_order = [] # Nhật ký loang màu

        while open_set:
            # Lấy ra đỉnh có chi phí nhỏ nhất hiện tại
            current_g, current = heapq.heappop(open_set)

            # Nếu đỉnh này đã được xử lý xong từ trước thì bỏ qua (Lazy deletion)
            if current in closed_set:
                continue
                
            # ĐÃ SỬA: Dùng đúng cờ return_history
            if return_history:
                visited_count += 1
                visited_order.append(current)

            # ĐIỀU KIỆN DỪNG: Đã đến đích
            if current == goal_node:
                path = self._reconstruct_path(came_from, current)
                return (path, visited_count, visited_order) if return_history else path

            # Đánh dấu đỉnh này đã xử lý xong
            closed_set.add(current)
            
            # Quét các đỉnh kề (hàng xóm)
            neighbors = self.graph.get(current, {})
            u_coord = self.nodes[current]

            for neighbor, edge_data in neighbors.items():
                # Bỏ qua nếu hàng xóm đã được chốt
                if neighbor in closed_set:
                    continue

                v_coord = self.nodes[neighbor]

                # 🚥 Tính toán trọng số (Khoảng cách + Tắc đường/Ngập lụt)
                if cost_fn:
                    weight = cost_fn(current, neighbor, u_coord, v_coord, edge_data)
                else:
                    weight = edge_data.get('weight', 1.0) # Trọng số mặc định nếu không có

                # Nếu gặp ngập lụt nặng (weight = vô cực), không đi đường này
                if weight >= self.INF_THRESHOLD:
                    continue

                # Tính chi phí tạm thời từ Start -> Current -> Neighbor
                tentative_g_score = g_score[current] + weight

                # Nếu tìm thấy con đường ngắn hơn để đến Neighbor này
                if tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    
                    # Đẩy Neighbor vào hàng đợi ưu tiên để duyệt tiếp
                    heapq.heappush(open_set, (tentative_g_score, neighbor))

        # Nếu vòng lặp kết thúc mà không tìm thấy đích (Bị cô lập do ngập lụt tứ phía)
        if return_history:
            return None, visited_count, visited_order
        return None

    def _reconstruct_path(self, came_from, current):
        """
        Truy vết lại đường đi từ đích về điểm xuất phát.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1] # Đảo ngược lại mảng để có đường đi từ Start -> Goal