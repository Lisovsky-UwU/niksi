import { apiClient } from './client'
import type { GreyZoneEntry, GreyZoneLimit, GreyZoneMonth } from '../types/models'

export function getGreyZone(monthId: number) {
  return apiClient.get<GreyZoneMonth>(`/months/${monthId}/grey-zone`).then((r) => r.data)
}

export function setMyGreyZoneLimit(monthId: number, amount: string) {
  return apiClient.put<GreyZoneLimit>(`/months/${monthId}/grey-zone/me`, { amount }).then((r) => r.data)
}

export function takeFromGreyZone(monthId: number, amount: string, takenDate: string) {
  return apiClient
    .post<GreyZoneEntry>(`/months/${monthId}/grey-zone/entries`, { amount, taken_date: takenDate })
    .then((r) => r.data)
}

export function deleteGreyZoneEntry(entryId: number) {
  return apiClient.delete(`/grey-zone/entries/${entryId}`).then(() => undefined)
}
