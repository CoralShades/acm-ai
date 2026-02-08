/**
 * Centralized branding configuration for ACM-AI
 *
 * VAEA (Victorian Asbestos Eradication Agency) branding
 */

export const BRANDING = {
  /** Organization name */
  organization: 'VAEA',

  /** Full organization name */
  organizationFull: 'Victorian Asbestos Eradication Agency',

  /** Short application name */
  name: 'ACM-AI',

  /** Full application name with description */
  fullName: 'VAEA ACM-AI - Asbestos Register Management',

  /** Brief tagline for the application */
  tagline: 'AI-powered compliance document analysis',

  /** Longer description for metadata and marketing */
  description: 'Victorian government platform for managing Asbestos Containing Material registers with AI assistance',

  /** SEO keywords */
  keywords: ['VAEA', 'ACM', 'asbestos', 'SAMP', 'compliance', 'AI', 'register', 'management', 'Victorian government'],

  /** API information */
  api: {
    title: 'VAEA ACM-AI API',
    description: 'API for VAEA ACM-AI - Asbestos Containing Material Register Analysis',
    version: '1.0.0',
  },

  /** Footer text */
  footer: {
    acknowledgment: 'VAEA acknowledges the Traditional Owners of Country throughout Victoria and recognises their continuing connection to land, waters and culture. We pay our respects to their Elders past, present and emerging.',
    vendor: 'Powered by CoralShades',
  },
} as const

/** Type for the branding configuration */
export type BrandingConfig = typeof BRANDING
