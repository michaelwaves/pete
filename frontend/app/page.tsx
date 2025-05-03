import Image from "next/image";
import WebScraperForm from "@/components/WebScraperForm";

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center w-full max-w-2xl">
        <div className="flex items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Podcastify</h1>
        </div>
        
        <div className="w-full">
          <WebScraperForm />
          <p className="text-sm text-gray-700 text-center mt-4">
            Enter any URL to create an AI-generated podcast with Orion's voice
          </p>
        </div>
      </main>
      
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <p className="text-xs text-gray-700">
          Built with Next.js and Temporal Workflows
        </p>
      </footer>
    </div>
  );
}
