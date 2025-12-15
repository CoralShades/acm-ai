/**
 * Centralized branding configuration for ACM-AI
 *
 * This file contains all branding-related constants used throughout the application.
 * Update values here to change branding across the entire app.
 */

export const BRANDING = {
  /** Short application name */
  name: 'ACM-AI',

  /** Full application name with description */
  fullName: 'ACM-AI - Asbestos Register Management',

  /** Brief tagline for the application */
  tagline: 'AI-powered compliance document analysis',

  /** Longer description for metadata and marketing */
  description: 'Analyze and manage Asbestos Containing Material registers with AI assistance',

  /** SEO keywords */
  keywords: ['ACM', 'asbestos', 'SAMP', 'compliance', 'AI', 'register', 'management'],

  /** API information */
  api: {
    title: 'ACM-AI API',
    description: 'API for ACM-AI - Asbestos Containing Material Register Analysis',
    version: '1.0.0',
  },
} as const

/** Type for the branding configuration */
export type BrandingConfig = typeof BRANDING
