import pickle
import pandas as pd
import os

# 1. Cấu hình đường dẫn tuyệt đối (Tuyệt đối không bị lưu nhầm chỗ)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_PATH = os.path.join(CURRENT_DIR, "data", "processed", "hbt_graph.pkl")
NODES_CSV_PATH = os.path.join(CURRENT_DIR, "data", "processed", "hbt_nodes.csv")
EDGES_CSV_PATH = os.path.join(CURRENT_DIR, "data", "processed", "hbt_edges.csv")

def convert_to_csv():
    print(f"🔍 Đang tìm file dữ liệu tại: {GRAPH_PATH}")
    
    if not os.path.exists(GRAPH_PATH):
        return
    with open(GRAPH_PATH, 'rb') as f:
        data = pickle.load(f)

    nodes_data = data.get('nodes', {})
    graph_data = data.get('graph', {})

    # ==========================================
    # XỬ LÝ ĐỈNH (NODES)
    # ==========================================
    nodes_list = [{"Node_ID": node_id, "Latitude": coords[0], "Longitude": coords[1]} 
                  for node_id, coords in nodes_data.items()]
    
    df_nodes = pd.DataFrame(nodes_list)
    df_nodes.to_csv(NODES_CSV_PATH, index=False, encoding='utf-8')
    
    # ==========================================
    # XỬ LÝ CẠNH (EDGES)
    # ==========================================
    
    edges_list = []
    for u, neighbors in graph_data.items():
        for v, properties in neighbors.items():
            edges_list.append({
                "Source_Node_u": u,
                "Target_Node_v": v,
                "Weight_Distance_km": properties.get('weight', 0),
                "Highway_Type": properties.get('type', 'unknown'),
                "Is_Oneway": properties.get('oneway', False)
            })

    df_edges = pd.DataFrame(edges_list)
    df_edges["Source_Node_u"] = pd.to_numeric(df_edges["Source_Node_u"])
    df_edges["Target_Node_v"] = pd.to_numeric(df_edges["Target_Node_v"])
    df_edges = df_edges.sort_values(by=["Source_Node_u", "Target_Node_v"])
    df_edges.to_csv(EDGES_CSV_PATH, index=False, encoding='utf-8')

if __name__ == "__main__":
    convert_to_csv()