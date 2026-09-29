import { apiClient } from './client'
import type { LoginRequest, User } from '../types/models'

export function login(payload: LoginRequest) {
  return apiClient.post<User>('/auth/login', payload).then((r) => r.data)
}

export function logout() {
  return apiClient.post('/auth/logout').then(() => undefined)
}

export function fetchMe() {
  return apiClient.get<User>('/auth/me').then((r) => r.data)
}
