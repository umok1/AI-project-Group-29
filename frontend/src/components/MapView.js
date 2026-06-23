import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Rectangle, useMapEvents, useMap, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix lỗi hiển thị icon mặc định của Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Custom Icons cho Start và End
const StartIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: iconShadow,
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
});

const EndIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: iconShadow,
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
});

// Component điều khiển View khi có đường đi mới
function ChangeView({ bounds }) {
    const map = useMap();
    useEffect(() => {
        if (bounds) map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    }, [bounds, map]);
    return null;
}

const MapView = ({ 
    startCoord, 
    endCoord, 
    path,
	visitedNodes,
    onMapClick, 
    onMapRightClick, 
    isAdminMode,
    adminConfig,
    trafficSegments 
}) => {
    const hbtCenter = [21.012, 105.850];
    const [mapBounds, setMapBounds] = useState(null);
    
    // Tọa độ bao quanh quận Hai Bà Trưng (Bounding Box)
    const boundsHBT = [
        [20.985, 105.825], // Góc Tây Nam
        [21.028, 105.878]  // Góc Đông Bắc
    ];
    
    // --- STATE CHO LOGIC VẼ ĐƯỜNG ADMIN ---
    const [adminStartPoint, setAdminStartPoint] = useState(null); 
    const [previewPath, setPreviewPath] = useState([]); 

    const MapEvents = () => {
        useMapEvents({
            click(e) {
                if (isAdminMode) {
                    if (!adminStartPoint) {
                        setAdminStartPoint(e.latlng);
                        setPreviewPath([[e.latlng.lat, e.latlng.lng], [e.latlng.lat, e.latlng.lng]]);
                    } else {
                        const finalPath = [
                            [adminStartPoint.lat, adminStartPoint.lng],
                            [e.latlng.lat, e.latlng.lng]
                        ];
                        onMapRightClick(finalPath, adminConfig.type, adminConfig.penalty);
                        setAdminStartPoint(null);
                        setPreviewPath([]);
                    }
                } else {
                    onMapClick(e.latlng);
                }
            },
            mousemove(e) {
                if (isAdminMode && adminStartPoint) {
                    setPreviewPath([
                        [adminStartPoint.lat, adminStartPoint.lng],
                        [e.latlng.lat, e.latlng.lng]
                    ]);
                }
            },
            contextmenu(e) {
                if (adminStartPoint) {
                    setAdminStartPoint(null);
                    setPreviewPath([]);
                }
            }
        });
        return null;
    };

    // Tự động căn chỉnh khung hình khi có đường đi A*
    useEffect(() => {
        if (path && path.length > 0) {
            const b = L.latLngBounds(path.map(p => [p.lat, p.lng]));
            setMapBounds(b);
        }
    }, [path]);

    return (
        <div style={{ height: '100%', width: '100%', position: 'relative' }}>
            <div style={{ cursor: isAdminMode ? 'crosshair' : 'grab' }}>
                <MapContainer center={hbtCenter} zoom={15} style={{ height: '100vh', width: '100%' }}>
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    
                    {/* HÀNG RÀO ĐỊA LÝ (BOUNDING BOX) */}
                    <Rectangle 
                        bounds={boundsHBT} 
                        pathOptions={{ 
                            color: '#3498db', 
                            weight: 2, 
                            fillOpacity: 0.03, 
                            dashArray: '10, 10',
                            interactive: false 
                        }} 
                    />

                    <MapEvents />
                    <ChangeView bounds={mapBounds} />

                    {/* VẼ ĐƯỜNG PREVIEW CỦA ADMIN */}
                    {isAdminMode && previewPath.length > 0 && (
                        <Polyline 
                            positions={previewPath}
                            pathOptions={{ 
                                color: adminConfig.type === 'flood' ? '#e74c3c' : '#f39c12', 
                                weight: 3, 
                                opacity: 0.6,
                                dashArray: '10, 10',
                                interactive: false 
                            }}
                        />
                    )}

                    {/* MARKER TẠM THỜI KHI ADMIN ĐANG VẼ */}
                    {isAdminMode && adminStartPoint && (
                        <Marker 
                            position={adminStartPoint} 
                            icon={L.icon({
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
                                iconSize: [25, 41], iconAnchor: [12, 41]
                            })} 
                        />
                    )}

                    {/* VẼ CÁC ĐOẠN ĐƯỜNG SỰ CỐ TỪ BACKEND */}
                    {trafficSegments && trafficSegments.map((seg, idx) => {
                        const isFlood = seg.type === 'flood';
                        return (
                            <Polyline 
                                key={`traffic-${idx}`}
                                positions={[[seg.from.lat, seg.from.lng], [seg.to.lat, seg.to.lng]]}
                                pathOptions={{ 
                                    color: isFlood ? '#e74c3c' : '#f39c12', 
                                    weight: 6, 
                                    opacity: 0.8,
                                    dashArray: isFlood ? null : '5, 10',
                                    interactive: false 
                                }}
                            />
                        );
                    })}
					
					{/* VẼ HIỆU ỨNG AI ĐANG QUÉT (VISUAL MODE) */}
                    {visitedNodes && visitedNodes.length > 0 && visitedNodes.map((node, idx) => (
                        <CircleMarker 
                            key={`visited-${idx}`}
                            center={[node.lat, node.lng]}
                            radius={5} // Độ to của chấm tròn
                            pathOptions={{
                                color: '#9b59b6', // Màu tím công nghệ
                                fillColor: '#9b59b6',
                                fillOpacity: 0.4,
                                stroke: false, // Bỏ viền cho mượt
                                interactive: false // Không cho click vào chấm tròn
                            }}
                        />
                    ))}
					
                    {/* LỘ TRÌNH A* CHÍNH */}
                    {path && path.length > 0 && (
                        <Polyline 
                            positions={path.map(p => [p.lat, p.lng])} 
                            pathOptions={{
                                color: "#2980b9", 
                                weight: 7, 
                                opacity: 1,
                                lineJoin: "round"
                            }}
                        />
                    )}

                    {/* MARKERS ĐẦU VÀ CUỐI CỦA USER */}
                    {startCoord && <Marker position={[startCoord.lat, startCoord.lng]} icon={StartIcon} />}
                    {endCoord && <Marker position={[endCoord.lat, endCoord.lng]} icon={EndIcon} />}

                </MapContainer>
            </div>

            {/* UI CHỈ DẪN TRẠNG THÁI VẼ */}
            {isAdminMode && (
                <div style={{
                    position: 'absolute', bottom: 30, left: '50%', transform: 'translateX(-50%)',
                    zIndex: 1000, background: 'rgba(44, 62, 80, 0.9)', color: 'white', 
                    padding: '12px 25px', borderRadius: '30px', fontWeight: 'bold', 
                    boxShadow: '0 6px 15px rgba(0,0,0,0.3)', border: '2px solid #e67e22',
                    fontSize: '13px', pointerEvents: 'none'
                }}>
                    {adminStartPoint 
                        ? "📏 Kéo chuột & Click điểm thứ 2 để chốt đoạn đường (Phải chuột để hủy)" 
                        : `✏️ ADMIN: Click chọn điểm đầu để đánh dấu đường ${adminConfig.type === 'flood' ? 'NGẬP' : 'TẮC'}`}
                </div>
            )}
        </div>
    );
};

export default MapView;
