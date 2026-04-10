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

import AgentPipeline from "./AgentPipeline";
import DraftPreview from "./DraftPreview";
import VerifierFlags from "./VerifierFlags";
import FilingAssistant from "./FilingAssistant";
import PDFDownload from "./PDFDownload";

export default function ResultsPage({
  agentStatuses,
  events,
  draft,
  verification,
  filingData,
  sessionId,
  isComplete,
  onReset,
}) {
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
      {filingData && <FilingAssistant data={filingData} />}

      {/* PDF download */}
      <PDFDownload sessionId={sessionId} isReady={isComplete} />
    </div>
  );
}
