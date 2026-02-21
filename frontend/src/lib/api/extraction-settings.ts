import { apiClient } from './client'
import type { ExtractionSettings } from '@/lib/types/extraction-settings'

export const extractionSettingsApi = {
  async get(): Promise<ExtractionSettings> {
    const { data } = await apiClient.get('/settings/extraction')
    return data
  },

  async update(settings: Partial<ExtractionSettings>): Promise<ExtractionSettings> {
    const { data } = await apiClient.put('/settings/extraction', settings)
    return data
  },

  async reset(): Promise<ExtractionSettings> {
    const { data } = await apiClient.post('/settings/extraction/reset')
    return data
  },
}
