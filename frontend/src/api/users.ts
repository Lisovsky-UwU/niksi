import { apiClient } from './client'
import type { User } from '../types/models'

export function listUsers() {
  return apiClient.get<User[]>('/users').then((r) => r.data)
}

export function updateMyProfile(displayName: string) {
  return apiClient.put<User>('/users/me', { display_name: displayName }).then((r) => r.data)
}

export function changeMyPassword(currentPassword: string, newPassword: string) {
  return apiClient
    .put('/users/me/password', { current_password: currentPassword, new_password: newPassword })
    .then(() => undefined)
}

/** The image goes as the raw body; it is cropped and shrunk in the browser first. */
export function uploadMyAvatar(image: Blob) {
  return apiClient
    .put<User>('/users/me/avatar', image, { headers: { 'Content-Type': image.type } })
    .then((r) => r.data)
}

export function removeMyAvatar() {
  return apiClient.delete<User>('/users/me/avatar').then((r) => r.data)
}

export function avatarUrl(user: Pick<User, 'id' | 'avatar_version'>): string | null {
  return user.avatar_version ? `/api/users/${user.id}/avatar?v=${user.avatar_version}` : null
}
