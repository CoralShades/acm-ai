import { create } from 'zustand';
import { UploadFile, MAX_FILES } from '@/components/upload/types';
import { nanoid } from 'nanoid';

export interface ProcessingOptions {
  enableAcmExtraction: boolean;
  enableEmbeddings: boolean;
  transformations: string[];
  notebookIds: string[];
  processingMode: 'sync' | 'async';
}

const DEFAULT_OPTIONS: ProcessingOptions = {
  enableAcmExtraction: true,
  enableEmbeddings: true,
  transformations: [],
  notebookIds: [],
  processingMode: 'async',
};

interface UploadStore {
  files: UploadFile[];
  options: ProcessingOptions;
  addFiles: (files: File[]) => void;
  removeFile: (id: string) => void;
  updateFile: (id: string, updates: Partial<UploadFile>) => void;
  clearFiles: () => void;
  setDocumentType: (id: string, type: UploadFile['documentType']) => void;
  setTitle: (id: string, title: string) => void;
  setOptions: (updates: Partial<ProcessingOptions>) => void;
  resetOptions: () => void;
}

export const useUploadStore = create<UploadStore>((set) => ({
  files: [],
  options: DEFAULT_OPTIONS,

  addFiles: (newFiles) => {
    const uploadFiles: UploadFile[] = newFiles.map((file) => ({
      id: nanoid(),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
    }));

    set((state) => ({
      files: [...state.files, ...uploadFiles].slice(0, MAX_FILES),
    }));
  },

  removeFile: (id) => {
    set((state) => ({
      files: state.files.filter((f) => f.id !== id),
    }));
  },

  updateFile: (id, updates) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id ? { ...f, ...updates } : f
      ),
    }));
  },

  clearFiles: () => set({ files: [] }),

  setDocumentType: (id, type) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id ? { ...f, documentType: type } : f
      ),
    }));
  },

  setTitle: (id, title) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id ? { ...f, title } : f
      ),
    }));
  },

  setOptions: (updates) => {
    set((state) => ({
      options: { ...state.options, ...updates },
    }));
  },

  resetOptions: () => {
    set({ options: DEFAULT_OPTIONS });
  },
}));
