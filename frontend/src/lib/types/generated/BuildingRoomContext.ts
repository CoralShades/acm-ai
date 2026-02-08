/**
 * Context for building and room hierarchy.
 * Persisted across chunks to maintain context during extraction.
 */
export type BuildingRoomContext = {
    /**
     * Area type: 'Interior', 'Exterior', or 'Grounds'
     */
    area_type?: string;
    /**
     * Construction type (e.g., 'Brick', 'Demountable')
     */
    building_construction?: null | string;
    /**
     * Building identifier (e.g., 'A1', 'B2')
     */
    building_id?: null | string;
    /**
     * Building name (e.g., 'Main Building', 'Science Wing')
     */
    building_name?: null | string;
    /**
     * Year building was constructed
     */
    building_year?: number | null;
    /**
     * Current page number being processed
     */
    current_page?: number;
    /**
     * Room area in square meters
     */
    room_area?: number | null;
    /**
     * Room identifier (e.g., 'A1-R1', '101')
     */
    room_id?: null | string;
    /**
     * Room name (e.g., 'Classroom', 'Office')
     */
    room_name?: null | string;
    /**
     * School code/identifier (e.g., 'PS123')
     */
    school_code?: null | string;
    /**
     * Name of the school or facility
     */
    school_name?: string;
    [property: string]: any;
}
