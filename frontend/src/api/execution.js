import client from './client'
export const getExecutionRuns  = (params={}) => client.get('/execution/runs/', { params })
export const getOrders         = (params={}) => client.get('/execution/orders/', { params })
export const getLiveOrders     = (params={}) => client.get('/execution/orders/live/', { params })
export const triggerExecution  = (data)      => client.post('/execution/runs/trigger/', data)
