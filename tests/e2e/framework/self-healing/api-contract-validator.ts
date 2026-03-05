/**
 * API Contract Validator
 *
 * Validates API responses against expected field contracts to detect
 * schema drift between the backend and frontend expectations.
 */

export interface ContractValidation {
  valid: boolean;
  endpoint: string;
  missingFields: string[];
  extraFields: string[];
  typeMismatches: Array<{
    field: string;
    expected: string;
    actual: string;
  }>;
}

export interface DriftReport {
  endpoint: string;
  validations: ContractValidation[];
  hasDrift: boolean;
}

/**
 * Known API contracts — maps endpoint paths to their expected
 * top-level field names and types. Array fields use `[].field` notation.
 */
export const KEY_CONTRACTS: Record<string, Record<string, string>> = {
  '/health': { status: 'string' },
  '/notebooks/': { '[].id': 'string', '[].name': 'string' },
  '/sources/': { '[].id': 'string', '[].title': 'string' },
  '/models/': { '[].name': 'string', '[].provider': 'string' },
  '/models/defaults': { chat_model: 'string' },
  '/acm/field-schema': { item_fields: 'object', building_fields: 'object' },
};

export class APIContractValidator {
  /**
   * Validate a parsed response object against expected field definitions.
   */
  validate(
    response: Record<string, unknown>,
    expectedFields: Record<string, string>,
    endpoint: string
  ): ContractValidation {
    const missingFields: string[] = [];
    const extraFields: string[] = [];
    const typeMismatches: Array<{ field: string; expected: string; actual: string }> = [];

    // Separate array-notation fields from plain fields
    const arrayFields: Record<string, string> = {};
    const plainFields: Record<string, string> = {};

    for (const [field, expectedType] of Object.entries(expectedFields)) {
      if (field.startsWith('[].')) {
        arrayFields[field] = expectedType;
      } else {
        plainFields[field] = expectedType;
      }
    }

    // Validate plain (top-level) fields
    for (const [field, expectedType] of Object.entries(plainFields)) {
      if (!(field in response)) {
        missingFields.push(field);
      } else {
        const actualType = this.getType(response[field]);
        if (actualType !== expectedType) {
          typeMismatches.push({ field, expected: expectedType, actual: actualType });
        }
      }
    }

    // Validate array-notation fields (e.g., "[].id" means the response is
    // an array and each item should have an "id" of the given type)
    if (Object.keys(arrayFields).length > 0) {
      if (Array.isArray(response)) {
        const items = response as unknown as Record<string, unknown>[];
        if (items.length > 0) {
          const firstItem = items[0];
          for (const [fieldPath, expectedType] of Object.entries(arrayFields)) {
            const fieldName = fieldPath.replace('[].', '');
            if (!(fieldName in firstItem)) {
              missingFields.push(fieldPath);
            } else {
              const actualType = this.getType(firstItem[fieldName]);
              if (actualType !== expectedType) {
                typeMismatches.push({
                  field: fieldPath,
                  expected: expectedType,
                  actual: actualType,
                });
              }
            }
          }
        }
      } else {
        // Response should be an array but isn't
        for (const fieldPath of Object.keys(arrayFields)) {
          missingFields.push(fieldPath);
        }
      }
    }

    // Check for unexpected top-level fields (only for plain-field contracts)
    if (Object.keys(plainFields).length > 0 && !Array.isArray(response)) {
      const expectedKeys = new Set(Object.keys(plainFields));
      for (const key of Object.keys(response)) {
        if (!expectedKeys.has(key)) {
          extraFields.push(key);
        }
      }
    }

    const valid =
      missingFields.length === 0 && typeMismatches.length === 0;

    return { valid, endpoint, missingFields, extraFields, typeMismatches };
  }

  /**
   * Fetch an endpoint and validate its response against expected fields.
   */
  async validateEndpoint(
    apiBase: string,
    endpoint: string,
    expectedFields: Record<string, string>,
    fetchFn: (url: string) => Promise<unknown>
  ): Promise<ContractValidation> {
    const url = `${apiBase}${endpoint}`;
    try {
      const response = await fetchFn(url);
      return this.validate(
        response as Record<string, unknown>,
        expectedFields,
        endpoint
      );
    } catch (error) {
      return {
        valid: false,
        endpoint,
        missingFields: Object.keys(expectedFields),
        extraFields: [],
        typeMismatches: [],
      };
    }
  }

  /**
   * Get the JavaScript type as a string, distinguishing arrays and null.
   */
  private getType(value: unknown): string {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (Array.isArray(value)) return 'array';
    return typeof value;
  }
}
