'use client';

import { useDropzone } from 'react-dropzone';

export default function JDUploader({ setFile }) {
  const onDrop = (acceptedFiles) => {
    setFile(acceptedFiles[0]);
  };

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
    onDrop,
  });

  return (
    <div
      {...getRootProps()}
      className="border-2 border-dashed p-4 rounded cursor-pointer text-center hover:border-blue-500 transition-colors"
      aria-label="Upload job description file"
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the job description here...</p>
      ) : (
        <p>Drag & drop JD here (TXT / PDF / DOC / DOCX), or click to select one file</p>
      )}
      {acceptedFiles.length > 0 && (
        <p className="mt-2 text-sm text-gray-600">{acceptedFiles.length} file(s) selected</p>
      )}
    </div>
  );
}