'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileSpreadsheet } from 'lucide-react'
import { toast } from 'sonner'
import { barTemplatesApi } from '@/lib/api/bar-templates'

interface BARTemplateUploaderProps {
  onUploaded: () => void
}

export function BARTemplateUploader({ onUploaded }: BARTemplateUploaderProps) {
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return
      const file = acceptedFiles[0]

      setUploading(true)
      try {
        const result = await barTemplatesApi.upload(file)
        toast.success(`Uploaded ${result.filename} — ${result.column_count} columns detected`)
        onUploaded()
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed'
        toast.error(msg)
      } finally {
        setUploading(false)
      }
    },
    [onUploaded]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel.sheet.macroEnabled.12': ['.xlsm'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-muted-foreground/25 hover:border-primary/50'
      } ${uploading ? 'opacity-50 pointer-events-none' : ''}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-2">
        {uploading ? (
          <FileSpreadsheet className="h-8 w-8 text-muted-foreground animate-pulse" />
        ) : (
          <Upload className="h-8 w-8 text-muted-foreground" />
        )}
        <p className="text-sm font-medium">
          {uploading
            ? 'Parsing template...'
            : isDragActive
              ? 'Drop BAR template here'
              : 'Drag & drop a BAR template (.xlsx / .xlsm)'}
        </p>
        <p className="text-xs text-muted-foreground">
          Upload the official Victorian Government BAR Excel template
        </p>
      </div>
    </div>
  )
}
