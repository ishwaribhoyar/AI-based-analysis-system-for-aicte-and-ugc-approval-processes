'use client';

import { useState, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { documentApi, processingApi } from '@/lib/api';
import toast from 'react-hot-toast';
import { Upload, FileText, X, Check, CloudUpload, File, ArrowRight, Home } from 'lucide-react';

function UploadPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const batchId = searchParams.get('batch_id') || '';

  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
      'text/csv',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
    ];
    const allowedExtensions = ['.pdf', '.xlsx', '.xls', '.csv', '.docx'];
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (file) => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        return allowedTypes.includes(file.type) || allowedExtensions.includes(ext);
      }
    );
    if (droppedFiles.length === 0) {
      toast.error('Please upload PDF, Excel, CSV, or Word files only');
      return;
    }
    setFiles((prev) => [...prev, ...droppedFiles]);
  }, []);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
      'text/csv',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // .docx
    ];
    const allowedExtensions = ['.pdf', '.xlsx', '.xls', '.csv', '.docx'];
    const selectedFiles = Array.from(e.target.files || []).filter(
      (file) => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        return allowedTypes.includes(file.type) || allowedExtensions.includes(ext);
      }
    );
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!batchId) {
      toast.error('Batch ID missing');
      return;
    }

    if (files.length === 0) {
      toast.error('Please select at least one file');
      return;
    }

    setUploading(true);
    try {
      for (const file of files) {
        await documentApi.upload(batchId, file);
        setUploadedFiles((prev) => [...prev, file.name]);
        toast.success(`Uploaded: ${file.name}`);
      }

      // Start processing
      await processingApi.start(batchId);
      toast.success('Processing started!');
      router.push(`/processing?batch_id=${batchId}`);
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  if (!batchId) {
    return (
      <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
        <div className="text-center bg-white rounded-3xl shadow-soft-lg p-12 max-w-md">
          <div className="w-16 h-16 bg-accent-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Home className="w-8 h-8 text-accent" />
          </div>
          <p className="text-gray-600 mb-6">Batch ID missing. Please select a mode first.</p>
          <button
            onClick={() => router.push('/')}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Home className="w-4 h-4" />
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-soft py-12 relative overflow-hidden">
      {/* Decorative Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="shape-blob w-80 h-80 bg-primary-100 top-20 right-0 translate-x-1/2" />
        <div className="shape-blob w-64 h-64 bg-secondary-50 bottom-20 left-0 -translate-x-1/2" />
      </div>

      <div className="container mx-auto px-4 max-w-4xl relative z-10">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-full shadow-soft mb-4 border border-primary-100">
            <CloudUpload className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-primary-dark">Step 2 of 3</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-3">
            Upload Documents
          </h1>
          <p className="text-gray-600">
            Upload institutional documents (PDF, Excel, CSV, Word) for analysis
          </p>
        </div>

        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`relative bg-white rounded-3xl shadow-soft-lg p-12 text-center mb-8 transition-all duration-300 border-2 border-dashed ${dragActive
            ? 'border-primary bg-primary-50 scale-[1.02]'
            : 'border-gray-200 hover:border-primary-light hover:bg-primary-50/30'
            }`}
        >
          <div className={`w-20 h-20 mx-auto mb-6 rounded-3xl flex items-center justify-center transition-all duration-300 ${dragActive ? 'bg-primary scale-110' : 'bg-gradient-to-br from-primary-50 to-primary-100'
            }`}>
            <Upload className={`w-10 h-10 transition-colors ${dragActive ? 'text-white' : 'text-primary'}`} />
          </div>

          <p className="text-xl font-medium text-gray-800 mb-2">
            {dragActive ? 'Drop files here' : 'Drag & drop files here'}
          </p>
          <p className="text-gray-500 mb-6">or</p>
          <p className="text-gray-500 mb-6">or</p>

          <label className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary to-primary-light text-white rounded-xl cursor-pointer hover:shadow-glow-teal transition-all duration-300 font-medium">
            <File className="w-5 h-5" />
            Browse Files
            <input
              type="file"
              multiple
              accept=".pdf,.xlsx,.xls,.csv,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>

          <p className="text-sm text-gray-400 mt-6">
            Supports PDF, Excel (.xlsx, .xls), CSV, Word (.docx) • Max: 50MB
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="bg-white rounded-3xl shadow-soft-lg p-8 mb-8 animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-800">
                Selected Files
              </h2>
              <span className="px-3 py-1 bg-primary-50 rounded-full text-sm font-medium text-primary">
                {files.length} file{files.length > 1 ? 's' : ''}
              </span>
            </div>

            <div className="space-y-3">
              {files.map((file, index) => (
                <div
                  key={index}
                  className={`flex items-center justify-between p-4 rounded-2xl transition-all duration-300 ${uploadedFiles.includes(file.name)
                    ? 'bg-secondary-50 border border-secondary-light'
                    : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${uploadedFiles.includes(file.name) ? 'bg-secondary' : 'bg-primary-100'
                      }`}>
                      <FileText className={`w-6 h-6 ${uploadedFiles.includes(file.name) ? 'text-white' : 'text-primary'
                        }`} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  {uploadedFiles.includes(file.name) ? (
                    <div className="flex items-center gap-2 text-secondary font-medium">
                      <Check className="w-5 h-5" />
                      Uploaded
                    </div>
                  ) : (
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Button */}
        {files.length > 0 && (
          <div className="text-center animate-fade-in">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="inline-flex items-center gap-3 px-10 py-4 bg-gradient-to-r from-primary to-secondary-light text-white text-lg font-semibold rounded-2xl hover:shadow-glow-teal disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                  Uploading...
                </>
              ) : (
                <>
                  Upload & Process
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
            <p className="text-sm text-gray-500 mt-4">
              Files will be processed automatically after upload
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function UploadPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-soft flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-3 border-primary border-t-transparent" />
      </div>
    }>
      <UploadPageContent />
    </Suspense>
  );
}
