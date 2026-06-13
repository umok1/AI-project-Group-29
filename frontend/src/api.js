import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Tìm đường đi tối ưu (Hỗ trợ nhiều thuật toán: A*, Dijkstra)
 * @param {Object} routeData - {start_lat, start_lon, end_lat, end_lon, algorithm}
 */
export const findPath = async (routeData) => {
  try {
    const response = await api.post('/find-path', routeData);
    return response.data; 
  } catch (error) {
    console.error("Lỗi API findPath:", error);
    throw new Error(error.response?.data?.detail || "Lỗi server khi tìm đường");
  }
};

// ... (Giữ nguyên toàn bộ các hàm updateTraffic, getActiveTraffic, resetTraffic... bên dưới)

/**
 * Cập nhật tình trạng giao thông dựa trên dải tọa độ vẽ (Vẽ nét đứt)
 * @param {Object} pathData - {path_coordinates, congestion, flood}
 * path_coordinates: [[lat, lng], [lat, lng], ...]
 */
export const updateTraffic = async (pathData) => {
  try {
    // Gửi yêu cầu lên endpoint mới nhận danh sách tọa độ
    const response = await api.post('/update-traffic', pathData);
    return response.data;
  } catch (error) {
    console.error("Lỗi API updateTraffic:", error);
    // In ra chi tiết lỗi từ FastAPI để dễ debug
    const detail = error.response?.data?.detail;
    throw new Error(detail || "Không thể cập nhật đoạn đường vẽ");
  }
};

/**
 * Lấy danh sách các đoạn đường sự cố để hiển thị lên bản đồ
 */
export const getActiveTraffic = async () => {
  try {
    const response = await api.get('/active-traffic');
    // Trả về mảng [{from, to, type, penalty}, ...]
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error("Lỗi API getActiveTraffic:", error);
    return []; 
  }
};

/**
 * Xóa bỏ tất cả các đánh dấu sự cố (Reset)
 */
export const resetTraffic = async () => {
  try {
    const response = await api.post('/reset-traffic');
    return response.data;
  } catch (error) {
    console.error("Lỗi khi reset traffic:", error);
    throw error;
  }
};

/**
 * Lấy trạng thái tổng quát (Nếu backend có endpoint này)
 */
export const getTrafficStatus = async () => {
  try {
    const response = await api.get('/traffic-status');
    return response.data;
  } catch (error) {
    console.error("Lỗi API getTrafficStatus:", error);
    return null;
  }
};

// Gom nhóm để export default nếu cần
const apiService = { 
    findPath, 
    updateTraffic, 
    getTrafficStatus, 
    getActiveTraffic, 
    resetTraffic 
};

export default apiService;
