/**
 * Bounding box for table provenance linking.
 */
export type TableBoundingBox = {
    /**
     * Height
     */
    height?: number | null;
    /**
     * Page number
     */
    page?: number | null;
    /**
     * Width
     */
    width?: number | null;
    /**
     * X coordinate
     */
    x?: number | null;
    /**
     * Y coordinate
     */
    y?: number | null;
    [property: string]: any;
}
