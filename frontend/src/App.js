import React, { useState, useEffect, useCallback } from 'react';
import MapView from './components/MapView';
import SearchPanel from './components/SearchPanel'; 
import TrafficLegend from './components/TrafficLegend'; 
import { findPath, updateTraffic, resetTraffic, getActiveTraffic } from './api'; 
import './App.css';

function App() {
  const [start, setStart] = useState(null);
  const [end, setEnd] = useState(null);
  const [path, setPath] = useState([]);
  const [loading, setLoading] = useState(false);
  const [trafficSegments, setTrafficSegments] = useState([]);
  const pathIntervalRef = React.useRef(null);
  
  // --- STATE CHỌN THUẬT TOÁN VÀ THỐNG KÊ ---
  const [algorithm, setAlgorithm] = useState('astar'); 
  const [routeStats, setRouteStats] = useState(null);  

  // --- TRẠNG THÁI ADMIN PANEL ---
  const [isAdmin, setIsAdmin] = useState(false); 
  const [adminType, setAdminType] = useState('congestion'); 
  const [penalty, setPenalty] = useState(5.0); 

  // --- HÀM LẤY DỮ LIỆU GIAO THÔNG (REFRESH) ---
  const refreshTrafficData = useCallback(async () => {
    try {
      const data = await getActiveTraffic();
      if (data && Array.isArray(data)) {
        setTrafficSegments(data);
      }
    } catch (error) {
      console.error("Lỗi khi lấy dữ liệu traffic:", error);
    }
  }, []);
  
  useEffect(() => {
    return () => {
        if (pathIntervalRef.current) clearInterval(pathIntervalRef.current);
    };
  }, []); 

  useEffect(() => {
    refreshTrafficData();
  }, [refreshTrafficData]);
  
  // --- HIỆU ỨNG VẼ ĐƯỜNG TỪ TỪ ---
  const animatePath = (fullPath) => {
    if (pathIntervalRef.current) {
        clearInterval(pathIntervalRef.current);
    }
    setPath([]); 
    
    let currentIndex = 0;
    const speed = 30; // Tốc độ vẽ

    pathIntervalRef.current = setInterval(() => {
        if (currentIndex < fullPath.length) {
            setPath(fullPath.slice(0, currentIndex + 1));
            currentIndex++;
        } else {
            clearInterval(pathIntervalRef.current);
            pathIntervalRef.current = null;
        }
    }, speed);
  }; 

  // --- LOGIC TÌM ĐƯỜNG ĐỒNG BỘ VỚI BACKEND ---
  // Nhận thêm currentAlgo để đổi thuật toán là tìm đường lại ngay lập tức
  const performRouting = async (s, e, currentAlgo = algorithm) => {
    if (!s || !e) return;
    setLoading(true);
    setRouteStats(null); // Reset thống kê cũ
    
    try {
      const data = await findPath({
        start_lat: parseFloat(s.lat),
        start_lon: parseFloat(s.lng),
        end_lat: parseFloat(e.lat),
        end_lon: parseFloat(e.lng),
        algorithm: currentAlgo // Gửi thuật toán đang chọn xuống Backend
      });

      console.log("Dữ liệu nhận được:", data);

      if (data.status === "outside_bounds") {
        alert(data.message); 
        setEnd(null); 
        setPath([]);
        return;
      }

      if (data.status === "success" && data.path && data.path.length > 0) {
        animatePath(data.path); 
        
        // Lưu metadata thống kê để hiển thị
        setRouteStats(data.metadata);

        // Snap Marker về đúng điểm đầu/cuối của đường đi thực tế
        const actualStart = data.path[0];
        const actualEnd = data.path[data.path.length - 1];

        setStart({ lat: actualStart.lat, lng: actualStart.lng });
        setEnd({ lat: actualEnd.lat, lng: actualEnd.lng });

      } else {
        alert(data.message || "Không tìm thấy lộ trình khả dụng.");
        setPath([]);
        setEnd(null);
      }
    } catch (err) {
      alert("Lỗi kết nối Server: " + err.message);
      setPath([]);
    } finally {
      setLoading(false);
    }
  };

  // --- XỬ LÝ CLICK BẢN ĐỒ ---
  const handleMapSelection = async (latlng) => {
    if (isAdmin) return; 

    if (!start || (start && end)) {
      setStart(latlng);
      setEnd(null);
      setPath([]);
      setRouteStats(null);
    } else {
      setEnd(latlng);
      await performRouting(start, latlng);
    }
  };

  // --- LOGIC BÁO CÁO SỰ CỐ (ADMIN) ---
  const handleReportAdminPath = async (pathCoords, type, pValue) => {
    if (!pathCoords || pathCoords.length < 2) return;

    setLoading(true);
    try {
      const response = await updateTraffic({
        path_coordinates: pathCoords, 
        flood: type === 'flood' ? pValue : 0.0,
        congestion: type === 'congestion' ? pValue : 1.0
      });

      if (response.status === "success") {
        await refreshTrafficData(); 
        
        if (start && end) {
          await performRouting(start, end);
        }
      } else {
        alert("Lỗi Admin: " + response.message);
      }
    } catch (err) {
      alert("Lỗi hệ thống Admin: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // --- RESET TOÀN BỘ HỆ THỐNG ---
  const handleResetTraffic = async () => {
    if (window.confirm("Xác nhận xóa toàn bộ dữ liệu sự cố và khôi phục giao thông bình thường?")) {
      try {
        const response = await resetTraffic();
        if (response.status === "success") {
          setTrafficSegments([]);
          setPath([]);
          setRouteStats(null);
          if (start && end) await performRouting(start, end);
          alert(response.message);
        }
      } catch (err) {
        alert("Không thể reset: " + err.message);
      }
    }
  };

  return (
    <div className="app-container" style={{ position: 'relative', height: '100vh', overflow: 'hidden' }}>
      
      {/* SIDEBAR NAVIGATION */}
      <div className="sidebar" style={{
        position: 'absolute', top: 20, left: 20, zIndex: 1000,
        background: 'white', padding: '20px', borderRadius: '12px',
        boxShadow: '0 4px 15px rgba(0,0,0,0.2)', width: '320px',
        maxHeight: '90vh', overflowY: 'auto'
      }}>
        <h2 style={{ margin: '0 0 10px 0', color: '#2c3e50', fontSize: '22px', textAlign: 'center' }}>
            HBT Routing AI 🤖
        </h2>

        {/* BẢNG ĐIỀU KHIỂN ADMIN */}
        <div style={{ background: '#fff3e0', padding: '15px', borderRadius: '10px', marginBottom: '15px', border: '1px solid #ffe0b2' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold', fontSize: '14px', color: '#e67e22' }}>🛠 Chế độ Admin</span>
                <input 
                    type="checkbox" 
                    checked={isAdmin} 
                    onChange={(e) => setIsAdmin(e.target.checked)}
                    style={{ cursor: 'pointer', width: '20px', height: '20px' }}
                />
            </div>
            
            {isAdmin && (
                <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <select 
                        value={adminType} 
                        onChange={(e) => setAdminType(e.target.value)}
                        style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                    >
                        <option value="congestion">Báo Tắc đường (x Hệ số)</option>
                        <option value="flood">Báo Ngập lụt (Chặn đường)</option>
                    </select>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Hệ số:</label>
                        <input 
                            type="number" 
                            value={penalty} 
                            onChange={(e) => setPenalty(parseFloat(e.target.value))}
                            style={{ width: '100%', padding: '5px', borderRadius: '4px', border: '1px solid #ddd' }}
                        />
                    </div>
                    <button 
                      onClick={handleResetTraffic}
                      style={{
                        marginTop: '5px', padding: '8px', background: '#e67e22', color: 'white',
                        border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold'
                      }}
                    >
                      Xóa toàn bộ sự cố
                    </button>
                </div>
            )}
        </div>

        {/* --- CẢI TIẾN SEARCH PANEL --- */}
        <SearchPanel 
            label="📍 ĐIỂM XUẤT PHÁT"
            placeholder="Nhập địa điểm..." 
            selectedCoord={start}
            onLocationSelect={(coords) => { setStart(coords); setPath([]); setRouteStats(null); }} 
        />
        
        <SearchPanel 
            label="🏁 ĐIỂM ĐẾN"
            placeholder="Nhập địa điểm ..." 
            selectedCoord={end}
            onLocationSelect={(coords) => { setEnd(coords); if(start) performRouting(start, coords); }} 
        />
        {/* ----------------------------- */}

        {/* --- KHU VỰC CHỌN THUẬT TOÁN VÀ HIỂN THỊ THỐNG KÊ --- */}
        <div style={{ margin: '15px 0', padding: '15px', background: '#f8f9fa', borderRadius: '10px', border: '1px solid #e9ecef' }}>
            <div style={{ marginBottom: '10px' }}>
                <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#2c3e50', display: 'block', marginBottom: '5px' }}>
                    ⚙️ THUẬT TOÁN TÌM ĐƯỜNG
                </label>
                <select 
                    value={algorithm} 
                    onChange={(e) => {
                        const newAlgo = e.target.value;
                        setAlgorithm(newAlgo);
                        if (start && end) performRouting(start, end, newAlgo);
                    }}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #bdc3c7', outline: 'none' }}
                >
                    <option value="astar">A* Algorithm </option>
                    <option value="dijkstra">Dijkstra Algorithm </option>
                </select>
            </div>

            {/* BẢNG KẾT QUẢ THỐNG KÊ (Chỉ đo thời gian) */}
            {routeStats && (
                <div style={{ marginTop: '10px' }}>
                    <div style={{ background: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #eee', textAlign: 'center' }}>
                        <div style={{ fontSize: '12px', color: '#7f8c8d', marginBottom: '4px' }}>⏱️ Thời gian chạy thuật toán</div>
                        <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#e74c3c' }}>
                            {routeStats.execution_time_ms} ms
                        </div>
                    </div>
                </div>
            )}
        </div>
        {/* ----------------------------- */}

        <div className="status-box" style={{ 
            marginTop: '15px', padding: '10px', background: '#f8f9fa', borderRadius: '8px',
            borderLeft: `4px solid ${loading ? '#3498db' : '#2ecc71'}`
        }}>
          <p style={{ fontSize: '13px', color: '#34495e', margin: 0 }}>
            {isAdmin ? "✏️ Admin: Click điểm đầu, kéo chuột vẽ đoạn tắc" :
             !start ? "👉 Bước 1: Chọn điểm xuất phát" : 
             !end ? "👉 Bước 2: Chọn điểm đến" : 
             loading ? "⏳ Đang tính toán lộ trình tối ưu..." : "✅ Đường đi đã được cập nhật"}
          </p>
        </div>

        {(start || end) && !isAdmin && (
          <button 
            onClick={() => { setStart(null); setEnd(null); setPath([]); setRouteStats(null); }}
            style={{
              marginTop: '15px', width: '100%', padding: '10px', background: '#e74c3c', 
              color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold'
            }}
          >
            Xóa lộ trình & Chọn lại
          </button>
        )}

        <TrafficLegend />
      </div>

      {/* MAP VIEW COMPONENT */}
      <MapView 
        startCoord={start} 
        endCoord={end} 
        path={path} 
        onMapClick={handleMapSelection} 
        onMapRightClick={handleReportAdminPath} 
        isAdminMode={isAdmin}
        adminConfig={{ type: adminType, penalty: penalty }}
        trafficSegments={trafficSegments}
      />
    </div>
  );
}

export default App;