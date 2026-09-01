import client from './client'
export const getSignalRuns  = (params={}) => client.get('/signals/runs/', { params })
export const getSignalRun   = (id, params={}) => client.get(`/signals/runs/${id}/`, { params })
export const getRunSignals  = (id, params={}) => client.get(`/signals/runs/${id}/signals/`, { params })
export const triggerPredict = (payload)   => client.post('/signals/runs/trigger/', payload)
export const getTaskStatus  = (id, params={}) => client.get(`/signals/runs/task-status/${id}/`, { params })
