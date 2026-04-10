/**
 * ProcessingPage.jsx — View 4 (PROCESSING)
 *
 * Full-screen view shown while the 5-agent pipeline runs.
 * Displays animated AgentPipeline with live SSE status.
 *
 * Props:
 *   agentStatuses (object) — from useSSE
 *   events        (array)  — from useSSE
 *   sseError      (string|null) — from useSSE error
 */

import AgentPipeline from "./AgentPipeline";

export default function ProcessingPage({ agentStatuses, events, sseError }) {
  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <svg
            className="h-5 w-5 animate-spin text-amber-500 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
            Processing Your Case
          </p>
        </div>
        <h2 className="text-2xl font-semibold text-zinc-100">
          AI agents are drafting your document...
        </h2>
        <p className="font-devanagari text-zinc-400 text-sm">
          दस्तावेज़ तैयार हो रहा है — कृपया प्रतीक्षा करें
        </p>
      </div>

      {/* Live pipeline */}
      <AgentPipeline agentStatuses={agentStatuses} events={events} />

      {/* SSE error */}
      {sseError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
          <span className="font-bold">Pipeline error: </span>{sseError}
        </div>
      )}
    </div>
  );
}
