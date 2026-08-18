import { apiFetch } from './client'

export interface HealthStatus {
  status: 'ok'
  service: string
  version: string
}

export const getApiHealth = () => apiFetch<HealthStatus>('/health')
