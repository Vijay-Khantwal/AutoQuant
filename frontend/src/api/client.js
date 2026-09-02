import axios from 'axios'

const useAzure = localStorage.getItem('USE_AZURE') === 'true'
const baseURL = useAzure ? `http://${import.meta.env.VITE_AZURE_IP || '20.235.242.149'}:8000/api` : '/api'

const client = axios.create({ baseURL })

// Request interceptor ?" add token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor ?" log errors globally
client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default client
