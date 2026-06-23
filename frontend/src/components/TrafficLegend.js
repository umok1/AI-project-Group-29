import React from 'react';

const TrafficLegend = () => {
    const legendItems = [
        { color: '#2ecc71', label: 'Điểm xuất phát', icon: '🟢' },
        { color: '#e74c3c', label: 'Điểm đích', icon: '🔴' },
		{ color: '#c44cf77a', label: 'Các nút đã duyệt', icon: '🟣' },
        { color: '#3498db', label: 'Lộ trình tối ưu (A*)', icon: '🔵' },
        { color: '#f39c12', label: 'Cảnh báo ùn tắc', icon: '🟠' },
        { color: '#e74c3c', label: 'Khu vực ngập lụt', icon: '⚠️' },
    ];

    return (
        <div style={{
            marginTop: '20px',
            padding: '14px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #edf2f7',
            boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
        }}>
            <h4 style={{ 
                margin: '0 0 14px 0', 
                fontSize: '13px', 
                color: '#2d3748',
                textTransform: 'uppercase',
                letterSpacing: '1px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
            }}>
                📊 Chú giải thực tế
            </h4>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {legendItems.map((item, index) => (
                    <div key={index} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        padding: '2px 0'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span style={{ fontSize: '14px', width: '18px', textAlign: 'center' }}>
                                {item.icon}
                            </span>
                            <span style={{ 
                                fontSize: '12.5px', 
                                color: '#4a5568', 
                                fontWeight: '500' 
                            }}>
                                {item.label}
                            </span>
                        </div>
                        
                        {/* Vạch màu mô phỏng đường Polyline trên Map */}
                        <div style={{ 
                            width: '24px', 
                            height: (item.label.includes('ngập') || item.label.includes('tắc')) ? '6px' : '4px', 
                            backgroundColor: item.color,
                            borderRadius: '3px',
                            boxShadow: `0 0 4px ${item.color}44` // Hiệu ứng đổ bóng nhẹ theo màu đường
                        }}></div>
                    </div>
                ))}
            </div>

            <div style={{ 
                marginTop: '16px', 
                paddingTop: '12px', 
                borderTop: '1px dashed #e2e8f0',
                fontSize: '11px',
                color: '#718096',
                lineHeight: '1.5',
                fontStyle: 'italic'
            }}>
                <strong style={{color: '#4a5568'}}>Cơ chế tối ưu:</strong> Chi phí ($Cost$) được tính toán động. Thuật toán A* ưu tiên các cung đường có tổng trọng số thấp nhất để đảm bảo tiêu chí: <b>Nhanh nhất - An toàn nhất.</b>
            </div>
        </div>
    );
};

export default TrafficLegend;