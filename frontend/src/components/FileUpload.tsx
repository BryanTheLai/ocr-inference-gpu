'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, FileText, Image } from 'lucide-react';
import { formatFileSize, cn } from '@/lib/utils';

interface UploadedFile {
  id: string;
  file: File;
  preview?: string;
}

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  accept?: Record<string, string[]>;
  maxFiles?: number;
  multiple?: boolean;
}

export default function FileUpload({ 
  onFilesSelected, 
  accept = {
    'application/pdf': ['.pdf'],
    'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
  },
  maxFiles = 10,
  multiple = true
}: FileUploadProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
    }));

    setUploadedFiles(prev => [...prev, ...newFiles].slice(0, maxFiles));
    onFilesSelected(acceptedFiles);
  }, [maxFiles, onFilesSelected]);

  const removeFile = (id: string) => {
    setUploadedFiles(prev => {
      const filtered = prev.filter(f => f.id !== id);
      onFilesSelected(filtered.map(f => f.file));
      return filtered;
    });
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple,
    maxFiles
  });

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') return <FileText className="w-8 h-8 text-red-500" />;
    if (file.type.startsWith('image/')) return <Image className="w-8 h-8 text-blue-500" />;
    return <File className="w-8 h-8 text-gray-500" />;
  };

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all",
          isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-lg font-medium text-blue-600">Drop the files here...</p>
        ) : (
          <>
            <p className="text-lg font-medium text-gray-700">
              Drag & drop files here, or click to select
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports PDF and image files (max {maxFiles} files)
            </p>
          </>
        )}
      </div>

      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Uploaded Files</h3>
          <div className="space-y-2">
            {uploadedFiles.map(({ id, file, preview }) => (
              <div
                key={id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {preview ? (
                    <img src={preview} alt={file.name} className="w-10 h-10 object-cover rounded" />
                  ) : (
                    getFileIcon(file)
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(id)}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
