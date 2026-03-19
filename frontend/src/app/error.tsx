"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global Application Error:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-base text-text-primary p-6">
      <div className="bg-bg-surface border border-border-subtle rounded-3xl p-8 sm:p-12 max-w-lg w-full text-center shadow-2xl relative overflow-hidden">
        <div className="w-20 h-20 rounded-full bg-red/10 border border-red/20 flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-10 h-10 text-red" />
        </div>
        
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-3">
          Something went wrong
        </h1>
        
        <p className="text-text-secondary text-sm sm:text-base leading-relaxed mb-8">
          The Council encountered an unexpected error. This has been logged and we will investigate shortly. 
          <br /><br />
          <span className="text-xs opacity-70 break-words font-mono bg-bg-base p-2 rounded-lg block border border-border-default/30">
            {error.message || "Unknown Application Error"}
          </span>
        </p>

        <button
          onClick={() => reset()}
          className="w-full bg-primary text-black font-bold rounded-xl py-4 flex items-center justify-center gap-2 hover:bg-primary-hover transition-colors shadow-lg"
        >
          <RefreshCcw className="w-5 h-5" />
          Try Again
        </button>
      </div>
      
      {/* Decorative background blur */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-red-dim blur-[120px] rounded-full pointer-events-none -z-10" />
    </div>
  );
}
