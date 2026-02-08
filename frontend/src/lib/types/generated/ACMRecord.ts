/**
 * Domain model for ACM (Asbestos Containing Material) records.
 *
 * Represents a single ACM item extracted from a SAMP (Site Asbestos
 * Management Plan) or ACM Register document.
 */
export type ACMRecord = {
    /**
     * Details about the ACM labeling (e.g., label type, date)
     */
    acm_label_details?: null | string;
    /**
     * Whether the ACM has been labeled on-site
     */
    acm_labelled?: boolean | null;
    /**
     * BAR taxonomy product group (e.g., 'T3 Vinyl products')
     */
    acm_product_group?: null | string;
    /**
     * BAR taxonomy product type (e.g., 'Vinyl Tiles')
     */
    acm_product_type?:      null | string;
    area_type?:             null | string;
    building_construction?: null | string;
    building_id:            string;
    building_name?:         null | string;
    building_year?:         number | null;
    /**
     * Confidence score for the classification (0.0-1.0)
     */
    classification_confidence?: number | null;
    /**
     * Classification method: 'pattern', 'llm', or 'manual'
     */
    classification_method?: null | string;
    /**
     * Whether the classification was manually overridden
     */
    classification_override?: boolean | null;
    created?:                 Date | null;
    /**
     * List of data quality issues identified during extraction
     */
    data_issues?: string[] | null;
    /**
     * Date when the material was removed (if applicable)
     */
    date_of_removal?: null | string;
    /**
     * Likelihood of material disturbance (e.g., 'Low', 'Medium', 'High')
     */
    disturbance_potential?: null | string;
    /**
     * Timestamp when embedding was generated
     */
    embedded_at?: Date | null;
    /**
     * Vector embedding for semantic search
     */
    embedding?: number[] | null;
    /**
     * Model ID used to generate the embedding
     */
    embedding_model?: null | string;
    /**
     * Combined text used to generate the embedding
     */
    embedding_text?: null | string;
    extent?:         null | string;
    /**
     * Confidence level of the extraction: 'high', 'medium', or 'low'
     */
    extraction_confidence?: null | string;
    friable?:               null | string;
    /**
     * Recommendations from the hygienist for this material
     */
    hygienist_recommendations?: null | string;
    id?:                        null | string;
    /**
     * Hygiene consulting company that performed the inspection
     */
    identifying_company?: null | string;
    location?:            null | string;
    material_condition?:  null | string;
    material_description: string;
    page_number?:         number | null;
    product:              string;
    /**
     * Unique identifier supplied by PSB (if applicable)
     */
    psb_supplied_acm_id?: null | string;
    /**
     * Amount or extent of the material (e.g., '10 m²', '5 linear meters')
     */
    quantity?: null | string;
    /**
     * Removal status (e.g., 'N/A', 'Pending', 'Complete', 'Encapsulated')
     */
    removal_status?: null | string;
    result:          string;
    risk_status?:    null | string;
    room_area?:      number | null;
    room_id?:        null | string;
    room_name?:      null | string;
    /**
     * Sample identification number from lab testing
     */
    sample_no?: null | string;
    /**
     * Laboratory analysis result for the sample
     */
    sample_result?: null | string;
    school_code?:   null | string;
    school_name:    string;
    source_id:      string;
    /**
     * Table bounding box coordinates: {x, y, width, height, page}
     */
    table_bbox?: { [key: string]: any } | null;
    updated?:    Date | null;
    [property: string]: any;
}
