import React, { useState, useEffect, useCallback } from 'react';
import MapView from './components/MapView';
import SearchPanel from './components/SearchPanel'; 
import TrafficLegend from './components/TrafficLegend'; 
import { findPath, updateTraffic, tomtomUpdateTraffic, resetTraffic, getActiveTraffic, runBenchmark } from './api';
import './App.css';

function App() {
  const [start, setStart] = useState(null);
  const [end, setEnd] = useState(null);
  const [path, setPath] = useState([]);
  const [loading, setLoading] = useState(false);
  const [trafficSegments, setTrafficSegments] = useState([]);
  const pathIntervalRef = React.useRef(null);
  
  // --- STATE CHỌN THUẬT TOÁN VÀ THỐNG KÊ ---
  const [visualMode, setVisualMode] = useState(false); 
  const [isVisualizing, setIsVisualizing] = useState(false); 
  const [algorithm, setAlgorithm] = useState('astar'); 
  const [routeStats, setRouteStats] = useState(null);  
  const [visitedNodes, setVisitedNodes] = useState([]); 

  // --- TRẠNG THÁI ADMIN PANEL ---
  const [isAdmin, setIsAdmin] = useState(false); 
  const [adminType, setAdminType] = useState('congestion'); 
  const [penalty, setPenalty] = useState(5.0); 

  // 💡 STATE MỚI CHO TÍNH NĂNG BENCHMARK
  const [numRuns, setNumRuns] = useState(100);
  const [benchmarkResults, setBenchmarkResults] = useState(null);
  
  // TOMTOM API
  const [autoTomTom, setAutoTomTom] = useState(false);

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
    const speed = 15; // Tốc độ vẽ

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
  
  const animateSearchProcess = (historyCoords, finalPath) => {
    setIsVisualizing(true);
    setVisitedNodes([]); 
	setPath([]); 
	let currentIndex = 0;
	const CHUNK_SIZE = 30; 
	const timer = setInterval(() => {
      if (currentIndex >= historyCoords.length) {
        clearInterval(timer);
        animatePath(finalPath);
        setIsVisualizing(false);
        return;
      }

      const chunk = historyCoords.slice(currentIndex, currentIndex + CHUNK_SIZE);
      setVisitedNodes(prev => [...prev, ...chunk]);
      
      currentIndex += CHUNK_SIZE;
    }, 20); 
  };

  // --- LOGIC TÌM ĐƯỜNG BÌNH THƯỜNG ---
  const performRouting = async (s, e, currentAlgo = algorithm) => {
    if (!s || !e) return;
	if (isVisualizing) return; 
    setLoading(true);
    setRouteStats(null);
    setBenchmarkResults(null); // Reset benchmark cũ nếu có
    
    try {
      const data = await findPath({
        start_lat: parseFloat(s.lat),
        start_lon: parseFloat(s.lng),
        end_lat: parseFloat(e.lat),
        end_lon: parseFloat(e.lng),
		visualize: visualMode,
        algorithm: currentAlgo 
      });

      if (data.status === "outside_bounds") {
        alert(data.message); 
        setEnd(null); 
        setPath([]);
		setVisitedNodes([]);
        return;
      }
		
	  
      if (data.status === "success" && data.path && data.path.length > 0) {
		if (visualMode && data.visited_order && data.visited_order.length > 0) {
		  animateSearchProcess(data.visited_order, data.path);
	    } else {
	      setPath(data.path);
	      setVisitedNodes([]); 
	    }
        if(!visualMode) animatePath(data.path); 
        
        setRouteStats({
          visited_count: data.visited_count || data.visited_nodes || "N/A"
        });

        const actualStart = data.path[0];
        const actualEnd = data.path[data.path.length - 1];

        setStart({ lat: actualStart.lat, lng: actualStart.lng });
        setEnd({ lat: actualEnd.lat, lng: actualEnd.lng });
		

      } else {
        alert(data.message || "Không tìm thấy lộ trình khả dụng.");
        setPath([]);
        setEnd(null);
		setVisitedNodes([]);
      }
    } catch (err) {
      alert("Lỗi kết nối Server: " + err.message);
      setPath([]);
    } finally {
      setLoading(false);
    }
  };

  // LOGIC GỌI API BENCHMARK CHO ADMIN
  const handleRunBenchmark = async () => {
    if (!start || !end) {
      alert("⚠️ Vui lòng chọn điểm xuất phát và điểm đến trên bản đồ trước!");
      return;
    }

    setLoading(true);
    setBenchmarkResults(null);

    try {
      // Gọi qua axios (từ file api.js)
      const data = await runBenchmark({
        start_lat: start.lat,
        start_lon: start.lng,
        end_lat: end.lat,
        end_lon: end.lng,
        algorithm: algorithm,
        num_runs: parseInt(numRuns)
      });

      if (data.status === "success") {
        setBenchmarkResults(data.metrics);
        if (data.path && data.path.length > 0) {
          animatePath(data.path); // Vẽ đường lên bản đồ để kiểm chứng
        }
      } else {
        alert("Lỗi Benchmark: " + data.message);
      }
    } catch (error) {
      console.error("Lỗi khi chạy benchmark:", error);
      alert(error.message || "Không thể kết nối đến máy chủ để chạy Benchmark.");
    } finally {
      setLoading(false);
    }
  };

  // --- XỬ LÝ CLICK BẢN ĐỒ ---
  const handleMapSelection = async (latlng) => {
    if (isAdmin || isVisualizing) return; 

    if (!start || (start && end)) {
      setStart(latlng);
      setEnd(null);
      setPath([]);
      setRouteStats(null);
      setBenchmarkResults(null); // Xóa kết quả benchmark cũ
	  setVisitedNodes([]); 
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

  // --- TOMTOM API ---
  const handleTomTomUpdate = useCallback(async() => {
	setLoading(true);
	try {
	  const response = await tomtomUpdateTraffic();
	  if (response.status === "success") {
        await refreshTrafficData(); 
	  } else {
          alert("Lỗi API: " + response.message);
	  }
	}
	catch (err) {
      alert("Lỗi hệ thống: " + err.message);
    } finally {
      setLoading(false);
    }
  }, [refreshTrafficData]);
  useEffect(() => {
    let tomtomInterval = null;

    if (autoTomTom) {
      // Chạy ngay lần đầu tiên khi vừa tích chọn
      handleTomTomUpdate(); 

      // Thiết lập chu kỳ chạy lại sau mỗi 10 phút (600,000 ms)
      // Bạn có thể sửa 600000 thành 60000 (1 phút) nếu muốn test nhanh
      tomtomInterval = setInterval(() => {
        console.log("🕒 Đến chu kỳ 10 phút: Tự động gọi TomTom API...");
        handleTomTomUpdate();
      }, 600000); 
    }

    // Hàm dọn dẹp khi người dùng bỏ tích hoặc tắt ứng dụng
    return () => {
      if (tomtomInterval) {
        clearInterval(tomtomInterval);
        console.log("🛑 Đã dừng chế độ tự động đồng bộ TomTom.");
      }
    };
  }, [autoTomTom]);
  
  // --- RESET TOÀN BỘ HỆ THỐNG ---
  const handleResetTraffic = async () => {
    if (window.confirm("Xác nhận xóa toàn bộ dữ liệu sự cố và khôi phục giao thông bình thường?")) {
      try {
        const response = await resetTraffic();
        if (response.status === "success") {
          setTrafficSegments([]);
          setPath([]);
          setRouteStats(null);
          setBenchmarkResults(null);
		  setVisitedNodes([]);
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

        {/* 🛠 BẢNG ĐIỀU KHIỂN ADMIN */}
        <div style={{ background: '#fff3e0', padding: '15px', borderRadius: '10px', marginBottom: '15px', border: '1px solid #ffe0b2' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold', fontSize: '14px', color: '#e67e22' }}>🛠 Chế độ Admin</span>
                <input 
                    type="checkbox" 
                    checked={isAdmin} 
                    onChange={(e) => {
                      setIsAdmin(e.target.checked);
                      setBenchmarkResults(null); // Tắt admin thì ẩn luôn bảng benchmark
                    }}
					disabled={isVisualizing}
                    style={{ cursor: 'pointer', width: '20px', height: '20px' }}
                />
            </div>
            
            {isAdmin && (
                <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {/* KHU VỰC VẼ SỰ CỐ */}
                    <select 
                        value={adminType} 
                        onChange={(e) => setAdminType(e.target.value)}
                        style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
                    >
                        <option value="congestion">Báo Tắc đường (x Hệ số)</option>
                        <option value="flood">Báo Ngập lụt (Chặn đường)</option>
                    </select>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Hệ số phạt:</label>
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

                    <hr style={{ margin: '10px 0', border: 'none', borderTop: '1px solid #f39c12' }} />

                    {/* 🚀 KHU VỰC CHẠY BENCHMARK */}
                    <span style={{ fontWeight: 'bold', fontSize: '13px', color: '#c0392b' }}>🚀 Ép xung Benchmark</span>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Số vòng chạy:</label>
                        <input 
                            type="number" 
                            value={numRuns} 
                            onChange={(e) => setNumRuns(e.target.value)}
                            min="10" 
                            max="5000"
                            style={{ width: '100%', padding: '5px', borderRadius: '4px', border: '1px solid #ddd' }}
                        />
                    </div>

                    <button 
                      onClick={handleRunBenchmark}
                      disabled={loading || !start || !end}
                      style={{
                        marginTop: '5px', padding: '10px', background: (!start || !end) ? '#bdc3c7' : '#c0392b', color: 'white',
                        border: 'none', borderRadius: '4px', cursor: (!start || !end) ? 'not-allowed' : 'pointer', fontSize: '13px', fontWeight: 'bold'
                      }}
                    >
                      {loading ? "Đang chạy ép xung..." : "Bắt đầu Benchmark"}
                    </button>
                </div>
            )}
        </div>
		{/* --- TOM TOM API --- */}
		<div style={{ background: '#ebf5fb', padding: '15px', borderRadius: '10px', marginBottom: '15px', border: '1px solid #2980b9' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold', fontSize: '14px', color: '#1a5276' }}>TOM TOM API</span>
                <input 
                    type="checkbox" 
                    checked={autoTomTom} 
                    onChange={(e) => {
                      setAutoTomTom(e.target.checked);
                    }}
					disabled={isVisualizing || loading}
                    style={{ cursor: 'pointer', width: '20px', height: '20px' }}
                />
            </div>
		</div>

        {/* --- KHU VỰC TÌM ĐƯỜNG --- */}
        <SearchPanel 
            label="📍 ĐIỂM XUẤT PHÁT"
            placeholder="Nhập địa điểm..." 
            selectedCoord={start}
            onLocationSelect={(coords) => { setStart(coords); setPath([]); setRouteStats(null); setBenchmarkResults(null); }} 
        />
        
        <SearchPanel 
            label="🏁 ĐIỂM ĐẾN"
            placeholder="Nhập địa điểm ..." 
            selectedCoord={end}
            onLocationSelect={(coords) => { setEnd(coords); if(start) performRouting(start, coords); }} 
        />

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
                        if (start && end && !isAdmin) performRouting(start, end, newAlgo);
                    }}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #bdc3c7', outline: 'none' }}
                >
                    <option value="astar">A* Algorithm </option>
                    <option value="dijkstra">Dijkstra Algorithm </option>
                </select>
            </div>

            {/* BẢNG KẾT QUẢ BENCHMARK CỦA ADMIN */}
            {isAdmin && benchmarkResults && (
                <div style={{ marginTop: '15px', background: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #c0392b', borderLeft: '4px solid #c0392b' }}>
                    <h4 style={{ margin: '0 0 10px 0', color: '#c0392b', fontSize: '14px' }}>📊 Báo cáo đo đạc ({benchmarkResults.num_runs} vòng)</h4>
                    <p style={{ margin: '5px 0', fontSize: '13px' }}>⏱️ Nhanh nhất (Min): <strong style={{color: 'green'}}>{benchmarkResults.min_ms} ms</strong></p>
                    <p style={{ margin: '5px 0', fontSize: '13px' }}>📉 Trung bình (Avg): <strong style={{color: 'blue'}}>{benchmarkResults.avg_ms} ms</strong></p>
                    <p style={{ margin: '5px 0', fontSize: '13px' }}>🔴 Chậm nhất (Max): <strong style={{color: '#c0392b'}}>{benchmarkResults.max_ms} ms</strong></p>
                    <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px dashed #ccc' }}/>
                    <p style={{ margin: '5px 0', fontSize: '13px' }}>🔍 Số đỉnh quét: <strong>{benchmarkResults.visited_nodes} nodes</strong></p>
                    <p style={{ margin: '5px 0', fontSize: '13px' }}>🗺️ Độ dài lộ trình: <strong>{benchmarkResults.path_nodes} nodes</strong></p>
                </div>
            )}

            {/* BẢNG KẾT QUẢ TÌM ĐƯỜNG BÌNH THƯỜNG */}
            {!isAdmin && routeStats && (
                <div style={{ marginTop: '10px' }}>
                    <div style={{ background: 'white', padding: '12px', borderRadius: '6px', border: '1px solid #eee', textAlign: 'center', borderLeft: '4px solid #e74c3c' }}>
                        <div style={{ fontSize: '13px', color: '#7f8c8d', marginBottom: '4px' }}>
                            📊 Số đỉnh thuật toán đã duyệt
                        </div>
                        <div style={{ fontSize: '22px', fontWeight: 'bold', color: '#e74c3c' }}>
                            {routeStats.visited_count} <span style={{ fontSize: '14px', color: '#2c3e50' }}>đỉnh</span>
                        </div>
                    </div>
                </div>
            )}
			<div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
				<input 
				  type="checkbox" 
				  id="visualToggle"
				  checked={visualMode}
			      onChange={(e) => setVisualMode(e.target.checked)}
				  disabled={isVisualizing} 
				  style={{ cursor: 'pointer', width: '16px', height: '16px' }}
				/>
				<label htmlFor="visualToggle" style={{ fontSize: '13px', fontWeight: 'bold', color: '#2980b9', cursor: 'pointer', margin: 0 }}>
				  Hiển thị các đỉnh thuật toán đã duyệt qua
				</label>
          </div>
        </div>

        <div className="status-box" style={{ 
            marginTop: '15px', padding: '10px', background: '#f8f9fa', borderRadius: '8px',
            borderLeft: `4px solid ${isVisualizing ? '#9b59b6' : loading ? '#3498db' : '#2ecc71'}`
        }}>
          <p style={{ fontSize: '13px', color: '#34495e', margin: 0 }}>
            {isVisualizing ? "Loading..." :
			 isAdmin ? "✏️ Admin: Kéo thả để vẽ tắc đường, hoặc bấm Benchmark." :
             !start ? "👉 Bước 1: Chọn điểm xuất phát" : 
             !end ? "👉 Bước 2: Chọn điểm đến" : 
             loading ? "⏳ Đang tính toán..." : "✅ Hoàn tất"}
          </p>
        </div>

        {(start || end) && !isAdmin && (
          <button 
            onClick={() => { setStart(null); setEnd(null); setPath([]); setRouteStats(null); setBenchmarkResults(null);}}
			disabled={isVisualizing}
            style={{
              marginTop: '15px', width: '100%', padding: '10px', background: isVisualizing ? '#bdc3c7' : '#e74c3c', 
              color: 'white', border: 'none', borderRadius: '6px', cursor: isVisualizing ? 'not-allowed' : 'pointer', fontWeight: 'bold'
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
		visitedNodes={visitedNodes}
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
