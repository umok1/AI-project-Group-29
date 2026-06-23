import time
import gc

def run_routing_benchmark(solver_instance, start_node, goal_node, cost_fn, num_runs=100):
    """
    Hàm benchmark độc lập giúp đo hiệu năng thuật toán tìm đường.
    Trả về: Dict chứa mảng node_ids và các chỉ số thống kê, hoặc None nếu không có đường.
    """
    # 1. Khởi động
    for _ in range(5):
        solver_instance.solve(start_node, goal_node, cost_fn=cost_fn, return_history=False)

    # 2. Tắt trình dọn rác (Cách ly nhiễu)
    gc.disable()
    
    cpu_times = []
    visited_nodes_count = 0
    path_ids = None

    try:
        # 3. Chạy vòng lặp đo đạc
        for i in range(num_runs):
            is_last_run = (i == num_runs - 1)
            
            t_start = time.process_time()
            result = solver_instance.solve(
                start_node=start_node, 
                goal_node=goal_node, 
                cost_fn=cost_fn, 
                return_history=is_last_run  # Chỉ lấy lịch sử ở vòng cuối để tiết kiệm RAM
            )
            t_end = time.process_time()
            
            cpu_times.append((t_end - t_start) * 1000)

            # Bóc tách kết quả ở lần chạy cuối
            if is_last_run:
                path_ids = result[0]
                visited_nodes_count = result[1] if isinstance(result, tuple) and len(result) > 1 else 0

    finally:
        # 4. Bật lại trình dọn rác
        gc.enable()

    if not path_ids:
        return None

    # 5. Đóng gói kết quả trả về
    return {
        "path_ids": path_ids,
        "visited_nodes": visited_nodes_count,
        "metrics": {
            "num_runs": num_runs,
            "min_ms": round(min(cpu_times), 3),
            "max_ms": round(max(cpu_times), 3),
            "avg_ms": round(sum(cpu_times) / len(cpu_times), 3),
        }
    }