import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/api', // Use Vite proxy
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
    // If the backend returns the structure { data: ..., page: ..., ... } directly
    // we just return the body.
    return response.data
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
