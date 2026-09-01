import client from './client'
export const getPositions       = (params={}) => client.get('/portfolio/positions/', { params })
export const getTrades          = (params={}) => client.get('/portfolio/trades/', { params })
export const getDailyPnL        = (params={}) => client.get('/portfolio/dailypnl/', { params })
export const getPortfolioSummary= (params={}) => client.get('/portfolio/summary/', { params })
export const triggerMonitor     = ()          => client.post('/portfolio/monitor/')
