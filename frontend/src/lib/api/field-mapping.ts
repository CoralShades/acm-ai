import { apiClient } from './client'
import type { FieldMapping } from '@/lib/types/field-mapping'

export const fieldMappingApi = {
  async get(): Promise<FieldMapping> {
    const { data } = await apiClient.get('/acm/field-mapping')
    return data
  },

  async update(mapping: Partial<FieldMapping>): Promise<FieldMapping> {
    const { data } = await apiClient.put('/acm/field-mapping', mapping)
    return data
  },

  async reset(): Promise<FieldMapping> {
    const { data } = await apiClient.post('/acm/field-mapping/reset')
    return data
  },
}
