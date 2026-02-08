/**
 * A single ACM record extracted by the LLM.
 * This is the schema used for structured output extraction.
 */
export type ACMExtractionRecord = {
    /**
     * Label details if labeled
     */
    acm_label_details?: null | string;
    /**
     * Whether the ACM is labeled on-site
     */
    acm_labelled?: boolean | null;
    /**
     * Area type: 'Interior', 'Exterior', or 'Grounds'
     */
    area_type?: null | string;
    /**
     * Construction type (e.g., 'Brick', 'Timber Frame')
     */
    building_construction?: null | string;
    /**
     * Building identifier (e.g., 'A1', 'B2'). REQUIRED.
     */
    building_id: string;
    /**
     * Building name (e.g., 'Main Building', 'Administration Block')
     */
    building_name?: null | string;
    /**
     * Year building was constructed
     */
    building_year?: number | null;
    /**
     * List of data quality issues identified during extraction
     */
    data_issues?: string[];
    /**
     * Date of removal if applicable
     */
    date_of_removal?: null | string;
    /**
     * Likelihood of disturbance: 'Low', 'Medium', 'High'
     */
    disturbance_potential?: null | string;
    /**
     * Extent/coverage of the material (e.g., 'Whole ceiling', 'Partial wall')
     */
    extent?: null | string;
    /**
     * Confidence level: 'high', 'medium', 'low'
     */
    extraction_confidence?: string;
    /**
     * Friability: 'Friable' or 'Non Friable'
     */
    friable?: null | string;
    /**
     * Expert recommendations for this material
     */
    hygienist_recommendations?: null | string;
    /**
     * Hygiene consulting company name
     */
    identifying_company?: null | string;
    /**
     * Specific location within room (e.g., 'Ceiling', 'Under stairs')
     */
    location?: null | string;
    /**
     * Condition: 'Good', 'Fair', 'Poor', 'Damaged'
     */
    material_condition?: null | string;
    /**
     * Detailed description of the material (e.g., 'Vinyl floor tiles, grey/white mottled
     * pattern'). REQUIRED.
     */
    material_description: string;
    /**
     * Page number where this record was found
     */
    page_number?: number | null;
    /**
     * Type of product containing asbestos (e.g., 'Ceiling Tiles', 'Pipe Insulation'). REQUIRED.
     */
    product: string;
    /**
     * PSB identifier if applicable
     */
    psb_supplied_acm_id?: null | string;
    /**
     * Amount of material (e.g., '10 m²', '5 linear meters')
     */
    quantity?: null | string;
    /**
     * Removal status: 'N/A', 'Pending', 'Complete', 'Encapsulated'
     */
    removal_status?: null | string;
    /**
     * Asbestos test result: 'Detected', 'Not Detected', 'Presumed', 'Unknown'. REQUIRED.
     */
    result: string;
    /**
     * Risk level: 'Low', 'Medium', 'High'
     */
    risk_status?: null | string;
    /**
     * Room area in square meters
     */
    room_area?: number | null;
    /**
     * Room identifier within the building (e.g., 'A1-R1', '101')
     */
    room_id?: null | string;
    /**
     * Room name (e.g., 'Classroom', 'Storeroom')
     */
    room_name?: null | string;
    /**
     * Sample identification number
     */
    sample_no?: null | string;
    /**
     * Laboratory analysis result
     */
    sample_result?: null | string;
    [property: string]: any;
}
