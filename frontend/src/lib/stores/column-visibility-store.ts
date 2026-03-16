import { create } from 'zustand'

export type PresetName = 'essential' | 'full-bar' | 'assessment-focus' | 'removal-tracking' | 'custom'

// Preset column definitions — field keys that should be VISIBLE for each preset
export const PRESET_COLUMNS: Record<Exclude<PresetName, 'custom'>, string[]> = {
  essential: [
    'building_id', 'product', 'friable', 'acm_product_group', 'acm_product_type',
    'material_condition', 'disturbance_potential', 'location', 'room_name',
    'floor_level', 'quantity', 'sample_result', 'identifying_company',
  ],
  'assessment-focus': [
    'building_id', 'room_id', 'product', 'acm_product_type', 'friable', 'result',
    'risk_status', 'material_condition', 'disturbance_potential', 'accessibility',
    'hygienist_recommendations', 'reassessment_date', 'identifying_company',
  ],
  'removal-tracking': [
    'building_id', 'room_id', 'product', 'acm_product_type', 'quantity',
    'unit_of_measure', 'removal_priority', 'removal_date', 'removal_contractor',
    'removal_method', 'disposal_certificate_no', 'verification_date',
  ],
  'full-bar': [], // empty means show ALL columns
}

export const PRESET_LABELS: Record<PresetName, string> = {
  essential: 'Essential',
  'full-bar': 'Full BAR',
  'assessment-focus': 'Assessment Focus',
  'removal-tracking': 'Removal Tracking',
  custom: 'Custom',
}

interface ColumnPresetState {
  activePreset: PresetName
  setActivePreset: (preset: PresetName) => void
}

export const useColumnPresetStore = create<ColumnPresetState>()((set) => ({
  activePreset: 'essential',
  setActivePreset: (preset) => set({ activePreset: preset }),
}))
