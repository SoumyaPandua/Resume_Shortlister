'use client';

import { useDropzone } from 'react-dropzone';

export default function ResumeUploader({ setFiles }) {
  const onDrop = (acceptedFiles) => {
    setFiles(acceptedFiles);
  };

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
    onDrop,
  });

  return (
    <div
      {...getRootProps()}
      className="border-2 border-dashed p-4 rounded cursor-pointer text-center hover:border-blue-500 transition-colors"
      aria-label="Upload resume files"
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the resumes here...</p>
      ) : (
        <p>Drag & drop resumes (PDF / DOC / DOCX), or click to select multiple files</p>
      )}
      {acceptedFiles.length > 0 && (
        <p className="mt-2 text-sm text-gray-600">{acceptedFiles.length} file(s) selected</p>
      )}
    </div>
  );
}
