/**
 * Output from the ACM extraction command.
 */
export type ACMExtractionOutput = {
    /**
     * Number of chunks used for extraction (1 = no chunking needed) (E1-S23)
     */
    chunk_count?: number;
    /**
     * Count of records by confidence level
     */
    confidence_distribution?: ConfidenceDistribution;
    /**
     * Corrective RAG stats: {auto_corrected, llm_corrected, failed, total_validated}
     */
    correction_stats?: { [key: string]: any } | null;
    /**
     * Error message if extraction failed
     */
    error?: null | string;
    /**
     * Time taken for extraction in milliseconds
     */
    extraction_time_ms?: number | null;
    /**
     * Orchestrator stats: per-building extraction plan, strategy distribution, timing
     */
    orchestrator_stats?: { [key: string]: any } | null;
    /**
     * Pipeline run state: stage timings, metrics, models used (E1-S21)
     */
    pipeline_run?: { [key: string]: any } | null;
    /**
     * Number of records excluded during validation (missing fields or intentional filter)
     */
    records_filtered?: number;
    /**
     * ID of the source document
     */
    source_id: string;
    /**
     * Extraction status: 'success', 'failed', 'no_data'
     */
    status: string;
    /**
     * Whether input exceeded model context window (E1-S23)
     */
    token_limit_exceeded?: boolean;
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
