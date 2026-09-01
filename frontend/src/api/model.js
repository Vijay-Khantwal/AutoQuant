import client from './client'
export const getModelRuns   = (params={}) => client.get('/model/runs/', { params })
export const getModelRun    = (id, params={}) => client.get(`/model/runs/${id}/`, { params })
export const getModelLogs   = (id, params={}) => client.get(`/model/runs/${id}/logs/`, { params })
export const triggerRetrain = (payload)   => client.post('/model/runs/retrain/', payload)
export const createStrategy = (payload)   => client.post('/model/strategies/', payload)
