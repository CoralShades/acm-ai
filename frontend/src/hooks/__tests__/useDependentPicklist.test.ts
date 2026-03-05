import { describe, it, expect } from 'vitest'
import { getFilteredOptions } from '../useDependentPicklist'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

const mockSchema: SFFieldSchemaConfig = {
  version: 'test',
  building_fields: {
    object_name: 'Building__c',
    object_label: 'Building',
    total_fields: 2,
    custom_fields: 2,
    picklist_fields: 2,
    fields: [],
    picklists: {},
    version: 'test',
  },
  item_fields: {
    object_name: 'ACM_Item__c',
    object_label: 'ACM Item',
    total_fields: 3,
    custom_fields: 3,
    picklist_fields: 3,
    fields: [],
    picklists: {},
    version: 'test',
  },
  picklists: {
    'ACM_Classification__c': ['Bonded ACM', 'Friable ACM', 'Non-ACM'],
    'ACM_Sub_Classification__c': ['Boards', 'Cement Sheet', 'Vinyl Tiles'],
    'Building_Category__c': ['Educational', 'Office', 'Industrial'],
    'Friability_of_Material__c': ['Friable', 'Non-friable'],
    'Building_Type__c': ['School', 'Office', 'Hospital'],
  },
  dependencies: [
    {
      controller_api_name: 'Friability_of_Material__c',
      dependent_api_name: 'ACM_Classification__c',
      mapping: {
        'Non-friable': ['Bonded ACM', 'Non-ACM'],
        'Friable': ['Friable ACM'],
      },
    },
    {
      controller_api_name: 'ACM_Classification__c',
      dependent_api_name: 'ACM_Sub_Classification__c',
      mapping: {
        'Bonded ACM': ['Boards', 'Cement Sheet'],
        'Friable ACM': ['Vinyl Tiles'],
      },
    },
    {
      controller_api_name: 'Building_Type__c',
      dependent_api_name: 'Building_Category__c',
      mapping: {
        'School': 'Educational',
        'Office': 'Office',
      },
    },
  ],
  loaded_at: null,
}

describe('getFilteredOptions', () => {
  it('returns all values when no controller value is set (AC2)', () => {
    const result = getFilteredOptions('ACM_Classification__c', {}, mockSchema)
    expect(result.validValues).toEqual(mockSchema.picklists['ACM_Classification__c'])
    expect(result.isDependent).toBe(true)
    expect(result.controllerValue).toBeNull()
  })

  it('filters ACM Classification by Friability — Non-friable (AC2)', () => {
    const result = getFilteredOptions(
      'ACM_Classification__c',
      { friable: 'Non-friable' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Bonded ACM', 'Non-ACM'])
    expect(result.allValues).toEqual(['Bonded ACM', 'Friable ACM', 'Non-ACM'])
    expect(result.controllerValue).toBe('Non-friable')
  })

  it('filters ACM Classification by Friability — Friable (AC2)', () => {
    const result = getFilteredOptions(
      'ACM_Classification__c',
      { friable: 'Friable' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Friable ACM'])
  })

  it('filters ACM Sub-Classification by Classification (AC2)', () => {
    const result = getFilteredOptions(
      'ACM_Sub_Classification__c',
      { acm_product_group: 'Bonded ACM' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Boards', 'Cement Sheet'])
    expect(result.isDependent).toBe(true)
  })

  it('filters ACM Sub-Classification — Friable ACM chain (AC2)', () => {
    const result = getFilteredOptions(
      'ACM_Sub_Classification__c',
      { acm_product_group: 'Friable ACM' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Vinyl Tiles'])
  })

  it('handles Building_Category string mapping (AC3)', () => {
    const result = getFilteredOptions(
      'Building_Category__c',
      { building_type: 'School' },
      mockSchema
    )
    // string value normalised to string[]
    expect(result.validValues).toEqual(['Educational'])
    expect(result.isDependent).toBe(true)
  })

  it('handles Building_Category string mapping — Office (AC3)', () => {
    const result = getFilteredOptions(
      'Building_Category__c',
      { building_type: 'Office' },
      mockSchema
    )
    expect(result.validValues).toEqual(['Office'])
  })

  it('returns all values for non-dependent field (isDependent: false)', () => {
    const result = getFilteredOptions('Friability_of_Material__c', {}, mockSchema)
    expect(result.isDependent).toBe(false)
    expect(result.validValues).toEqual(result.allValues)
    expect(result.controllerValue).toBeNull()
  })

  it('returns empty validValues when controller has unknown value', () => {
    const result = getFilteredOptions(
      'ACM_Classification__c',
      { friable: 'Unknown_Value' },
      mockSchema
    )
    expect(result.validValues).toEqual([])
  })

  it('returns empty arrays for field not in picklists', () => {
    const result = getFilteredOptions('Unknown_Field__c', {}, mockSchema)
    expect(result.allValues).toEqual([])
    expect(result.validValues).toEqual([])
    expect(result.isDependent).toBe(false)
  })

  it('accepts a custom keyMapper override', () => {
    // Use a custom mapper that always returns 'friable'
    const customMapper = () => 'friable'
    const result = getFilteredOptions(
      'ACM_Classification__c',
      { friable: 'Non-friable' },
      mockSchema,
      customMapper
    )
    expect(result.validValues).toEqual(['Bonded ACM', 'Non-ACM'])
  })

  it('returns all values when Building_Category controller not set (AC3)', () => {
    const result = getFilteredOptions('Building_Category__c', {}, mockSchema)
    expect(result.validValues).toEqual(mockSchema.picklists['Building_Category__c'])
    expect(result.controllerValue).toBeNull()
  })
})
