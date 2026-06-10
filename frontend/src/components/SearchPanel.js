import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const SearchPanel = ({ onLocationSelect, placeholder, label, selectedCoord }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);

    // Sử dụng useRef để quản lý thời gian chờ (Debounce)
    const timeoutRef = useRef(null);

    // Đồng bộ hóa: Nếu người dùng click trực tiếp trên Map, cập nhật lại ô input
    useEffect(() => {
        if (selectedCoord) {
            setQuery(`${selectedCoord.lat.toFixed(5)}, ${selectedCoord.lng.toFixed(5)}`);
            setShowDropdown(false);
        } else {
            setQuery(''); // Xóa text nếu bị reset
        }
    }, [selectedCoord]);

    const fetchLocations = async (searchText) => {
        if (searchText.trim().length < 2) {
            setResults([]);
            setShowDropdown(false);
            return;
        }
        
        setLoading(true);
        try {
            // Giữ nguyên viewbox của bạn nhưng thêm limit=5 để kết quả gọn gàng
            const response = await axios.get(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchText)}&viewbox=105.80,21.05,105.90,20.95&bounded=1&limit=5`
            );
            setResults(response.data);
            setShowDropdown(true);
        } catch (error) {
            console.error("Lỗi tìm kiếm địa điểm:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        const value = e.target.value;
        setQuery(value);

        // Kỹ thuật Debounce: Xóa bộ đếm cũ nếu người dùng vẫn đang gõ
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        
        // Chỉ gọi API sau khi người dùng dừng gõ 500ms
        timeoutRef.current = setTimeout(() => {
            fetchLocations(value);
        }, 500);
    };

    const selectLocation = (item) => {
        const coords = {
            lat: parseFloat(item.lat),
            lng: parseFloat(item.lon) // OSM trả về 'lon', cần chuyển thành 'lng' cho Leaflet
        };
        onLocationSelect(coords); 
        
        // Cắt lấy phần tên ngắn gọn trước dấu phẩy (Ví dụ: "Đại học Bách Khoa Hà Nội")
        const shortName = item.display_name.split(',')[0];
        setQuery(shortName); 
        setResults([]); 
        setShowDropdown(false);
    };

    return (
        <div style={{ marginBottom: '15px', position: 'relative' }}>
            <label style={{ fontSize: '12px', fontWeight: 'bold', color: '#e67e22', display: 'block' }}>
                {label}
            </label>
            <input
                type="text"
                value={query}
                onChange={handleSearch}
                onFocus={() => { if (results.length > 0) setShowDropdown(true); }}
                placeholder={placeholder}
                style={{
                    width: '100%',
                    padding: '10px 12px',
                    marginTop: '5px',
                    borderRadius: '6px',
                    border: '1px solid #bdc3c7',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                    outline: 'none',
                    transition: 'border-color 0.3s'
                }}
            />
            
            {loading && <div style={{ fontSize: '11px', color: '#3498db', marginTop: '4px', fontStyle: 'italic' }}>⏳ Đang quét dữ liệu...</div>}

            {/* DANH SÁCH DROPDOWN */}
            {showDropdown && results.length > 0 && (
                <ul style={{
                    position: 'absolute',
                    top: '65px',
                    left: 0,
                    right: 0,
                    backgroundColor: 'white',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    maxHeight: '250px',
                    overflowY: 'auto',
                    zIndex: 1001,
                    padding: 0,
                    margin: 0,
                    listStyle: 'none',
                    boxShadow: '0 8px 16px rgba(0,0,0,0.15)'
                }}>
                    {results.map((item, index) => (
                        <li
                            key={index}
                            onClick={() => selectLocation(item)}
                            style={{
                                padding: '10px 15px',
                                borderBottom: '1px solid #f1f2f6',
                                cursor: 'pointer',
                                transition: 'background 0.2s'
                            }}
                            onMouseEnter={(e) => e.target.style.backgroundColor = '#f8f9fa'}
                            onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                        >
                            <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#2c3e50' }}>
                                {item.display_name.split(',')[0]}
                            </div>
                            <div style={{ fontSize: '11px', color: '#7f8c8d', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {item.display_name}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default SearchPanel;