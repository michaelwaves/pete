import PdfUploadForm from '@/components/PdfUploadForm';

export default function UploadPage() {
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold text-center mb-8">PDF Upload</h1>
      <PdfUploadForm />
    </div>
  );
}