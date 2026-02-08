/**
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
