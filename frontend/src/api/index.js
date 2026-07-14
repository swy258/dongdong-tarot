import axios from 'axios'

const BASE = import.meta.env.VITE_API_BASE_URL || ''
const api = axios.create({
  baseURL: BASE + '/api',
  timeout: 120000,
})

// 请求拦截器：自动添加JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
    return Promise.reject(error)
  }
)

export default api

// ===== 认证 API =====
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
}

// ===== 卡牌 API =====
export const cardsAPI = {
  getAll: (params) => api.get('/cards/', { params }),
  getOne: (id) => api.get(`/cards/${id}`),
}

// ===== 牌阵 API =====
export const spreadsAPI = {
  getAll: () => api.get('/spreads/'),
  getPresets: () => api.get('/spreads/presets'),
  getOne: (id) => api.get(`/spreads/${id}`),
  create: (data) => api.post('/spreads/', data),
}

// ===== 占卜 API =====
export const readingsAPI = {
  create: (data) => api.post('/readings/', data),
  getOne: (id) => api.get(`/readings/${id}`),
  interpret: (id) => {
    // 返回fetch的ReadableStream用于流式读取
    const token = localStorage.getItem('token')
    return fetch(`${BASE}/api/readings/${id}/interpret`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
  },
  getHistory: (params) => api.get('/readings/', { params }),
  getShared: (shareCode) => api.get(`/readings/share/${shareCode}`),
  getShareSummary: (id) => api.post(`/readings/${id}/share-summary`),
}
