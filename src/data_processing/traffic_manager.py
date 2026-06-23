import json
import os

class TrafficManager:
    def __init__(self, config_path=None):
        self.config_path = config_path
        # live_updates lưu trữ: {(u, v): {'congestion': float, 'flood': float}}
        self.live_updates = {} 

    def _normalize_id(self, node_id):
        """Đồng bộ hóa kiểu dữ liệu ID (nên để str cho OSM)"""
        return str(node_id)

    def update_live_traffic(self, u, v, congestion_level=1.0, flood_level=0.0):
        """
        Cập nhật tình trạng từ Admin Panel.
        """
        u_id = self._normalize_id(u)
        v_id = self._normalize_id(v)
        
        key = (u_id, v_id)
        
        #Xóa đoạn đường cần cập nhật nếu chỉ số tắc đường và ngập lụt là mặc định
        if congestion_level == 1.0 and flood_level == 0.0:
            self.live_updates.pop(key, None)
            #print(key)
        else:
            self.live_updates[key] = {
                'congestion': max(1.0, float(congestion_level)),
                'flood': max(0.0, float(flood_level))
            }

    def get_traffic_coefficient(self, u, v):
        """
        Trả về hệ số nhân chi phí dựa trên tình trạng giao thông thực tế.
        Kiểm tra cả hai chiều để tránh việc A* đi lách luật.
        """
        u_id = self._normalize_id(u)
        v_id = self._normalize_id(v)
        
        # 1. Kiểm tra cặp (u, v) - Chiều thuận
        key_forward = (u_id, v_id)
        # 2. Kiểm tra cặp (v, u) - Chiều ngược
        key_backward = (v_id, u_id)
        
        # Lấy dữ liệu từ bộ nhớ live_updates (thử cả 2 chiều)
        status = self.live_updates.get(key_forward) or self.live_updates.get(key_backward)
        
        if status:
            # XỬ LÝ CHẶN ĐƯỜNG (NGẬP NẶNG/CẤM ĐƯỜNG)
            if status.get('flood', 0) >= 500:
                return 1000000.0 # Một triệu (Đủ lớn để A* rẽ hướng)

            # TÍNH TOÁN HỆ SỐ TỔNG HỢP
            congestion = float(status.get('congestion', 1.0))
            flood = float(status.get('flood', 0.0))
            
            # Công thức: Congestion * (1 + Flood)
            combined_factor = congestion * (1.0 + flood)
            
            return max(1.0, combined_factor)

        # Nếu không có dữ liệu sự cố, trả về hệ số mặc định
        return 1.0

    def clear_all_updates(self):
        """Xóa sạch dữ liệu cập nhật"""
        self.live_updates.clear()
        print("Mạng lưới giao thông đã được khôi phục trạng thái mặc định.")