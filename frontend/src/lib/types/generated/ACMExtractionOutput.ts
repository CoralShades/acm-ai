/**
 * Output from the ACM extraction command.
 */
export type ACMExtractionOutput = {
    /**
     * Count of records by confidence level
     */
    confidence_distribution?: ConfidenceDistribution;
    /**
     * Error message if extraction failed
     */
    error?: null | string;
    /**
     * Time taken for extraction in milliseconds
     */
    extraction_time_ms?: number | null;
    /**
     * Number of records that failed validation and were rejected
     */
    records_failed?: number;
    /**
     * ID of the source document
     */
    source_id: string;
    /**
     * Extraction status: 'success', 'failed', 'no_data'
     */
    status: string;
    /**
     * Number of records extracted
     */
    total_records?: number;
    [property: string]: any;
}

/**
 * Count of records by confidence level
 *
 * Distribution of extraction confidence levels.
 */
export type ConfidenceDistribution = {
    /**
     * Count of high confidence records
     */
    high?: number;
    /**
     * Count of low confidence records
     */
    low?: number;
    /**
     * Count of medium confidence records
     */
    medium?: number;
    [property: string]: any;
}
