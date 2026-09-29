import { apiClient } from './client'
import type { User } from '../types/models'

export function listUsers() {
  return apiClient.get<User[]>('/users').then((r) => r.data)
}
