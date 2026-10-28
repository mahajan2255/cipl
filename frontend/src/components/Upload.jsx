import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, FileSpreadsheet, Loader2, AlertCircle } from 'lucide-react';
import { uploadFile } from '../api';
import { clsx } from 'clsx';

const Upload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const result = await uploadFile(file);
      onUploadSuccess(result);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  return (
    <div className="w-full max-w-2xl mx-auto mt-8">
      <div
        {...getRootProps()}
        className={clsx(
          "border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center text-center cursor-pointer transition-colors duration-200",
          isDragActive ? "border-blue-500 bg-blue-500/10" : "border-zinc-700 hover:border-zinc-500 bg-zinc-900/50 hover:bg-zinc-900",
          uploading && "opacity-50 pointer-events-none"
        )}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
        ) : (
          <div className="p-4 bg-zinc-800 rounded-full mb-4">
             <UploadIcon className="w-8 h-8 text-zinc-400" />
          </div>
        )}

        <h3 className="text-lg font-semibold text-zinc-200 mb-2">
          {uploading ? "Uploading..." : "Upload Dataset"}
        </h3>
        <p className="text-sm text-zinc-400 max-w-sm">
          Drag and drop your CSV or Excel file here, or click to browse.
        </p>
        
        <div className="mt-6 flex gap-4 text-xs text-zinc-500">
           <span className="flex items-center gap-1">
             <FileSpreadsheet className="w-4 h-4" /> CSV, Excel
           </span>
        </div>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      )}
    </div>
  );
};

export default Upload;
