import xml.etree.ElementTree as ET
import pickle
import os
import sys
import networkx as nx

# --- CẤU HÌNH ĐƯỜNG DẪN HỆ THỐNG ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.utils.geo_utils import haversine_distance
from src.data_processing.spatial_index import SpatialIndex

class OSMParser:
    def __init__(self, osm_path):
        self.osm_path = osm_path
        self.nodes = {}  # {node_id (str): (lat, lon)}
        self.graph = {}  # {node_id (str): {neighbor_id (str): {weight, type}}}
        
        self.accepted_highways = {
            'primary', 'secondary', 'tertiary', 'residential', 
            'trunk', 'service', 'unclassified', 'motorway',
            'primary_link', 'secondary_link', 'tertiary_link'
        }

    def parse(self):
        if not os.path.exists(self.osm_path):
            return None, None

        try:
            tree = ET.parse(self.osm_path)
            root = tree.getroot()
        except Exception as e:
            return None, None

        # Bước 1: Thu thập Nodes - Ép kiểu ID về String
        for node in root.findall('node'):
            node_id = str(node.get('id')) # Ép kiểu String
            lat = float(node.get('lat'))
            lon = float(node.get('lon'))
            self.nodes[node_id] = (lat, lon)

        # Bước 2: Thu thập Ways (Xử lý dữ liệu đường 1 chiều, 2 chiều)
        way_count = 0
        for way in root.findall('way'):
            tags = {tag.get('k'): tag.get('v') for tag in way.findall('tag')}
            highway_type = tags.get('highway')
            
            if highway_type in self.accepted_highways:
                # Xử lý Oneway kỹ hơn (yes, 1, -1)
                oneway_tag = tags.get('oneway', 'no').lower()
                is_oneway = oneway_tag in ['yes', '1']
                is_reverse = oneway_tag == '-1'
                
                way_nodes = [str(nd.get('ref')) for nd in way.findall('nd')]
                
                for i in range(len(way_nodes) - 1):
                    u, v = way_nodes[i], way_nodes[i+1]
                    
                    if is_reverse:
                        self._add_edge(v, u, highway_type,True) # Đi ngược
                    else:
                        self._add_edge(u, v, highway_type,is_oneway) # Đi xuôi
                        if not is_oneway:
                            self._add_edge(v, u, highway_type,False) # Đường 2 chiều
                
                way_count += 1

        
        # Bước 3: Lọc cụm liên thông (SCC) - Đảm bảo đồ thị luôn tìm thấy đường
        self._filter_largest_component()
        self._reindex_nodes()
        return self.graph, self.nodes

    def _add_edge(self, u, v, road_type, oneway_status=False):
        if u not in self.nodes or v not in self.nodes:
            return
            
        dist = haversine_distance(self.nodes[u][0], self.nodes[u][1], 
                                  self.nodes[v][0], self.nodes[v][1])

        if u not in self.graph: 
            self.graph[u] = {}
            
        self.graph[u][v] = {'weight': dist, 'type': road_type, 'oneway':oneway_status}

    def _filter_largest_component(self):
        """Dùng NetworkX để lọc bỏ các vùng bị cô lập"""
        
        nx_graph = nx.DiGraph()
        for u, neighbors in self.graph.items():
            for v, data in neighbors.items():
                nx_graph.add_edge(u, v)

        # Tìm cụm liên thông mạnh (Strongly Connected Components)
        sccs = list(nx.strongly_connected_components(nx_graph))
        if not sccs: return
        
        largest_scc = max(sccs, key=len)
        
        new_graph = {}
        new_nodes = {}
        for u in largest_scc:
            if u in self.graph:
                new_graph[u] = {v: data for v, data in self.graph[u].items() if v in largest_scc}
                new_nodes[u] = self.nodes[u]
        
        self.graph = new_graph
        self.nodes = new_nodes

    def _reindex_nodes(self):
       
        new_nodes = {}
        new_graph = {}
        mapping = {} 
        
        for new_id, old_id in enumerate(self.nodes.keys()):
            mapping[old_id] = new_id
            new_nodes[new_id] = self.nodes[old_id]
            
        for old_u, neighbors in self.graph.items():
            new_u = mapping[old_u]
            new_graph[new_u] = {}
            for old_v, data in neighbors.items():
                new_v = mapping[old_v]
                new_graph[new_u][new_v] = data
                
        self.nodes = new_nodes
        self.graph = new_graph
         

    def save(self, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        data = {'graph': self.graph, 'nodes': self.nodes}
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        
        index_path = output_path.replace("hbt_graph.pkl", "spatial_index.pkl")
        si = SpatialIndex(self.nodes)
        si.save_index(index_path)

if __name__ == "__main__":
    osm_file = os.path.join(BASE_DIR, "data", "raw", "map.osm")
    pkl_file = os.path.join(BASE_DIR, "data", "processed", "hbt_graph.pkl")
    
    parser = OSMParser(osm_file)
    g, n = parser.parse()
    if g:
        parser.save(pkl_file)