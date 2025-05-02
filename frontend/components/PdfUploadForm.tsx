"use client";

import { useState, ChangeEvent, FormEvent } from 'react';

const PdfUploadForm = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    
    // Reset states
    setMessage('');
    setError('');
    
    // Validate file
    if (!selectedFile) {
      return;
    }
    
    // Check if file is PDF
    if (selectedFile.type !== 'application/pdf') {
      setError('Please select a PDF file');
      return;
    }
    
    setFile(selectedFile);
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }
    
    setIsUploading(true);
    setError('');
    setMessage('');
    
    try {
      // Create form data
      const formData = new FormData();
      formData.append('pdf', file);
      
      // Replace with your actual API endpoint
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      const data = await response.json();
      setMessage(data.message || 'PDF uploaded successfully!');
      setFile(null);
      
      // Reset file input
      const fileInput = document.getElementById('pdf-upload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (err) {
      setError('Failed to upload PDF. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">Upload PDF</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label 
            htmlFor="pdf-upload" 
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Select PDF file
          </label>
          
          <input
            id="pdf-upload"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-md file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-50 file:text-blue-700
                      hover:file:bg-blue-100"
            disabled={isUploading}
          />
        </div>
        
        {file && (
          <div className="mb-4 p-2 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">
              Selected file: <span className="font-medium">{file.name}</span> ({(file.size / 1024).toFixed(2)} KB)
            </p>
          </div>
        )}
        
        {error && (
          <div className="mb-4 p-2 bg-red-50 text-red-500 rounded">
            {error}
          </div>
        )}
        
        {message && (
          <div className="mb-4 p-2 bg-green-50 text-green-500 rounded">
            {message}
          </div>
        )}
        
        <button
          type="submit"
          disabled={!file || isUploading}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 
                    text-white font-medium rounded-md
                    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                    disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? 'Uploading...' : 'Upload PDF'}
        </button>
      </form>
    </div>
  );
};

export default PdfUploadForm;