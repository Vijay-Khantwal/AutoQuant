import client from './client'
export const getResearchRuns  = (params={}) => client.get('/research/runs/', { params })
export const getResearchRun   = (id, params={}) => client.get(`/research/runs/${id}/`, { params })
export const getRunDecisions  = (id, params={}) => client.get(`/research/runs/${id}/decisions/`, { params })
export const triggerResearch  = (data)      => client.post('/research/runs/trigger/', data)
export const createBlankRun   = ()          => client.post('/research/runs/create-blank/')
export const rerunDecision    = (id)        => client.post(`/research/decisions/${id}/rerun/`)
