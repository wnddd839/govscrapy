import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api', // 从环境变量读取，默认使用Vite proxy
  timeout: 10000
})

// Request interceptor
service.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  response => {
    // Adapter for new backend structure { code: 200, message: "...", data: ... }
    const res = response.data
    
    // Log for debugging
    console.log(`[API Response] ${response.config.url}`, res)

    // Check if it matches the standard response structure
    if (res && typeof res.code === 'number') {
      if (res.code === 200 || res.code === 0) {
        return res.data
      } else {
        ElMessage({
          message: res.message || res.msg || 'Error',
          type: 'error',
          duration: 5 * 1000
        })
        return Promise.reject(new Error(res.message || res.msg || 'Error'))
      }
    }
    
    // Fallback for direct data return or other formats
    return res
  },
  error => {
    console.error('API Error:', error)
    let message = error.message
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      
      if (data && data.message) {
          message = data.message
      } else {
          switch (status) {
            case 403:
              message = '无权访问 (403): 请检查来源域名是否在白名单中'
              break
            case 429:
              message = '请求过于频繁 (429): 请稍后再试'
              break
            case 404:
              message = '未找到资源 (404)'
              break
            case 500:
              message = '服务器内部错误 (500)'
              break
            default:
              message = `请求错误 (${status})`
          }
      }
    }
    ElMessage({
      message: message,
      type: 'error',
      duration: 5 * 1000
    })
    return Promise.reject(error)
  }
)

export default service
