import { apiClient } from './client'
import type { Category, CategoryCreateRequest, CategoryUpdateRequest } from '../types/models'

export function listCategories(monthId: number) {
  return apiClient.get<Category[]>(`/months/${monthId}/categories`).then((r) => r.data)
}

export function createCategory(monthId: number, payload: CategoryCreateRequest) {
  return apiClient.post<Category>(`/months/${monthId}/categories`, payload).then((r) => r.data)
}

export function updateCategory(categoryId: number, payload: CategoryUpdateRequest) {
  return apiClient.put<Category>(`/categories/${categoryId}`, payload).then((r) => r.data)
}

export function deleteCategory(categoryId: number) {
  return apiClient.delete(`/categories/${categoryId}`).then(() => undefined)
}

export function copyCategoriesFromPrevious(monthId: number) {
  return apiClient.post<Category[]>(`/months/${monthId}/categories/copy-from-previous`).then((r) => r.data)
}
