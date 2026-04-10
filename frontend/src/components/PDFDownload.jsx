/**
 * PDFDownload.jsx
 *
 * Download button for the generated PDF.
 * - Fetches as a Blob and triggers a browser download via a temporary anchor
 * - Disabled while pipeline is still running (isReady = false)
 * - Shows a spinner while downloading
 *
 * Props:
 *   sessionId (string)  — pipeline session identifier
 *   isReady   (boolean) — true when all 4 agents have completed successfully
 */

import { useState } from "react";
import { downloadPDF } from "../lib/api";

export default function PDFDownload({ sessionId, isReady = false }) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  async function handleDownload() {
    if (!isReady || isDownloading) return;

    setIsDownloading(true);
    setDownloadError(null);

    try {
      const blob = await downloadPDF(sessionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `nyayamitra-document-${sessionId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError(err.message ?? "Download failed. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="space-y-3">
      <button
        onClick={handleDownload}
        disabled={!isReady || isDownloading}
        className={[
          "w-full flex items-center justify-center gap-2 rounded-xl py-4 font-bold text-lg transition-all duration-200",
          isReady && !isDownloading
            ? "bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white cursor-pointer"
            : "bg-zinc-800 text-zinc-500 cursor-not-allowed opacity-60",
        ].join(" ")}
      >
        {isDownloading ? (
          <>
            <svg
              className="h-5 w-5 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
            Generating PDF...
          </>
        ) : isReady ? (
          <>
            <span>&#11015;</span>
            Download PDF
          </>
        ) : (
          <>
            <span>&#11015;</span>
            PDF not ready yet
          </>
        )}
      </button>

      {downloadError && (
        <p className="text-sm text-red-400 text-center">{downloadError}</p>
      )}

      {!isReady && (
        <p className="text-xs text-zinc-500 text-center font-mono">
          The download button will activate once all agents have completed.
        </p>
      )}
    </div>
  );
}
