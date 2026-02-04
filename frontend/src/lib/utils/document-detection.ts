import { UploadFile, DocumentType } from '@/components/upload/types';

// Re-export for convenience
export type { DocumentType } from '@/components/upload/types';

export interface DetectionResult {
  type: DocumentType;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

// Filename patterns that indicate ACM/SAMP documents
// Note: Patterns are ordered by specificity - more specific patterns first
const ACM_PATTERNS = [
  /asbestos/i,
  /\bacm\b/i, // Word boundary to avoid matching "acme", etc.
  /\bsamp\b/i, // Word boundary to avoid matching "sample", etc.
  /acm.?register/i, // ACM register specifically
  /asbestos.?register/i, // Asbestos register specifically
  /survey/i,
  /management\s*plan/i,
];

// File type to document type mapping
const MEDIA_TYPES = ['image/', 'audio/', 'video/'];

export function detectDocumentType(file: UploadFile): DetectionResult {
  const { name, type } = file;
  const nameLower = name.toLowerCase();

  // Check for media files first
  if (MEDIA_TYPES.some((t) => type.startsWith(t))) {
    return {
      type: 'media',
      confidence: 'high',
      reason: 'Media file detected',
    };
  }

  // Check for ACM/SAMP patterns in filename
  for (const pattern of ACM_PATTERNS) {
    if (pattern.test(nameLower)) {
      // Clean up pattern for display (remove regex escapes and word boundaries)
      const cleanPattern = pattern.source
        .replace(/\\b/g, '') // Remove word boundaries
        .replace(/\\s\*/g, ' ') // Replace \s* with space
        .replace(/\.\?/g, ' ') // Replace .? with space
        .replace(/[\\()]/g, ''); // Remove backslashes and parentheses
      return {
        type: 'acm',
        confidence: 'high',
        reason: `Filename contains "${cleanPattern}"`,
      };
    }
  }

  // PDF files without ACM patterns
  if (type === 'application/pdf') {
    return {
      type: 'general',
      confidence: 'medium',
      reason: 'PDF document',
    };
  }

  // Word documents
  if (type.includes('word') || type.includes('document')) {
    return {
      type: 'general',
      confidence: 'medium',
      reason: 'Word document',
    };
  }

  // Excel spreadsheets
  if (
    type.includes('spreadsheet') ||
    type.includes('excel') ||
    name.toLowerCase().endsWith('.xlsx') ||
    name.toLowerCase().endsWith('.xls')
  ) {
    return {
      type: 'general',
      confidence: 'medium',
      reason: 'Excel spreadsheet',
    };
  }

  // Default
  return {
    type: 'other',
    confidence: 'low',
    reason: 'Unknown file type',
  };
}

export function detectAllDocumentTypes(
  files: UploadFile[]
): Map<string, DetectionResult> {
  const results = new Map<string, DetectionResult>();
  files.forEach((file) => {
    results.set(file.id, detectDocumentType(file));
  });
  return results;
}

export const DOCUMENT_TYPE_CONFIG: Record<DocumentType, {
  label: string;
  description: string;
  color: string;
  bgColor: string;
}> = {
  acm: {
    label: 'ACM/SAMP Document',
    description: 'Asbestos register or management plan',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  general: {
    label: 'General Document',
    description: 'Standard document for text extraction',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
  media: {
    label: 'Media File',
    description: 'Image, audio, or video file',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  other: {
    label: 'Other',
    description: 'Unclassified file type',
    color: 'text-orange-600',
    bgColor: 'bg-orange-100',
  },
};
