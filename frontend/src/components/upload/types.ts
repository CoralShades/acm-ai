// Document type classification
export type DocumentType = 'acm' | 'general' | 'media' | 'other';

export interface UploadFile {
  id: string;
  file: File;
  name: string;
  title?: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  documentType?: DocumentType;
}

export const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
};

export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const MAX_FILES = 50;
