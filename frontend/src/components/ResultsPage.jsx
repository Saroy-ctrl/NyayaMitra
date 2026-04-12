/**
 * ResultsPage.jsx — View 5 (VIEW_RESULTS)
 *
 * Full results view: pipeline summary, draft preview, verifier report,
 * filing guide, and PDF download.
 *
 * Props:
 *   agentStatuses (object)      — from useSSE (all complete at this point)
 *   events        (array)       — from useSSE
 *   draft         (string|null) — generated document text
 *   verification  (object|null) — verifier output
 *   filingData    (object|null) — filing assistant output
 *   sessionId     (string)      — pipeline session ID
 *   isComplete    (bool)        — always true when this view is shown
 *   onReset       ()            — navigate back to LANDING
 */

import { useState } from "react";
import AgentPipeline from "./AgentPipeline";
import DraftPreview from "./DraftPreview";
import VerifierFlags from "./VerifierFlags";
import FilingAssistant from "./FilingAssistant";
import PDFDownload from "./PDFDownload";
import PaymentModal from "./PaymentModal";

export default function ResultsPage({
  agentStatuses,
  events,
  draft,
  verification,
  filingData,
  sessionId,
  isComplete,
  onReset,
  lang = "en",
}) {
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  return (
    <div className="space-y-10">
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">
            Results
          </p>
          <h2 className="text-2xl font-semibold text-zinc-100">Your document is ready</h2>
          <p className="font-devanagari text-zinc-400 text-sm mt-1">
            आपका दस्तावेज़ तैयार है
          </p>
        </div>
        <button
          onClick={onReset}
          className="shrink-0 text-sm text-zinc-500 hover:text-zinc-300 transition-colors duration-200 border border-zinc-700 rounded-lg px-3 py-1.5 hover:border-zinc-500"
        >
          &#8592; Start Over
        </button>
      </div>

      {/* Pipeline summary (all steps complete) */}
      <AgentPipeline agentStatuses={agentStatuses} events={events} />

      {/* Document preview */}
      <DraftPreview draft={draft} />

      {/* Verification report */}
      {verification && <VerifierFlags verification={verification} />}

      {/* Filing guide */}
      {filingData && <FilingAssistant data={filingData} lang={lang} />}

      {/* PDF download */}
      <PDFDownload sessionId={sessionId} isReady={isComplete} />

      {/* Expert lawyer verification upsell */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 backdrop-blur-sm p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4 justify-between">
        <div className="space-y-1">
          <p className="font-mono text-xs uppercase tracking-widest text-amber-500/70 mb-1">
            Add-on
          </p>
          <h3 className="text-base font-semibold text-zinc-100">
            Get Verified by an Expert Lawyer
          </h3>
          <p className="text-sm text-zinc-400 leading-relaxed max-w-sm">
            A qualified lawyer will review your document, flag any issues, and issue a signed
            verification certificate — giving your filing stronger legal standing.
          </p>
          <p className="font-devanagari text-xs text-zinc-600">
            एक योग्य वकील आपके दस्तावेज़ की समीक्षा करेगा
          </p>
        </div>
        <button
          onClick={() => setShowPaymentModal(true)}
          className="shrink-0 flex items-center gap-2 rounded-xl bg-amber-500 hover:bg-amber-400 px-5 py-2.5 text-sm font-bold text-zinc-950 transition-colors duration-200"
        >
          <span>&#9998;</span>
          Verify — &#8377;199
        </button>
      </div>

      {showPaymentModal && (
        <PaymentModal onClose={() => setShowPaymentModal(false)} />
      )}
    </div>
  );
}
