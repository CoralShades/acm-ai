/**
 * Shared utility: maps a Salesforce api_name to the corresponding ACMRecord property key.
 *
 * Extracted from ItemGrid.tsx (E33-S3) so it can be shared by:
 *   - ItemGrid.tsx (column defs)
 *   - useDependentPicklist.ts (cascade filtering)
 *   - DependentPicklistEditor.tsx (form mode)
 *
 * The SF taxonomy uses names like "Building_Code__c" or "Risk_Status__c".
 * The ACMRecord interface uses snake_case backend names (building_id, risk_status, etc.).
 */
export function fieldApiToRecordKey(apiName: string): string {
  // Strip Salesforce __c suffix and lowercase
  const stripped = apiName.replace(/__c$/i, '').toLowerCase()

  // Explicit overrides for known mapping differences
  const overrides: Record<string, string> = {
    building_code: 'building_id',
    acm_name: 'product',
    acm_description: 'material_description',
    condition: 'material_condition',
    // Friability field: both short and full SF name forms
    friability: 'friable',
    friability_of_material: 'friable',
    risk: 'risk_status',
    internal_external: 'area_type',
    // ACM classification chain
    acm_classification: 'acm_product_group',
    acm_sub_classification: 'acm_product_type',
    // Building chain: Building_Category__c -> building_construction
    building_category: 'building_construction',
  }

  return overrides[stripped] ?? stripped
}
