/**
 * BAR Template Management API client.
 * Story: E5-S3
 */

import api from './client'

export interface BARTemplateColumn {
  column_letter: string
  column_name: string
  field_type: string | null
  is_required: boolean
}

export interface BARTemplate {
  id: string | null
  filename: string
  version_label: string
  uploaded_at: string | null
  is_active: boolean
  column_count: number
  columns: BARTemplateColumn[]
  raw_header_row: string[]
  notes: string | null
}

export const barTemplatesApi = {
  /** List all uploaded BAR templates. */
  async list(): Promise<BARTemplate[]> {
    const { data } = await api.get<BARTemplate[]>('/api/bar-templates')
    return data
  },

  /** Upload a new BAR template file (.xlsx/.xlsm). */
  async upload(file: File): Promise<BARTemplate> {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<BARTemplate>('/api/bar-templates/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /** Get a specific template by ID. */
  async get(templateId: string): Promise<BARTemplate> {
    const { data } = await api.get<BARTemplate>(`/api/bar-templates/${templateId}`)
    return data
  },

  /** Set a template as active. */
  async activate(templateId: string): Promise<BARTemplate> {
    const { data } = await api.put<BARTemplate>(`/api/bar-templates/${templateId}/activate`)
    return data
  },

  /** Delete a non-active template. */
  async delete(templateId: string): Promise<void> {
    await api.delete(`/api/bar-templates/${templateId}`)
  },
}
