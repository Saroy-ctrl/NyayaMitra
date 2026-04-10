/**
 * AgentPipeline.jsx
 *
 * Vertical stepper showing the 5-agent pipeline status.
 * Connector lines animate from zinc to emerald when the step above completes.
 *
 * Props:
 *   agentStatuses (object) — { intake, research, drafter, verifier, filing_assistant }
 *                            each value: 'waiting' | 'running' | 'complete' | 'error'
 *   events        (array)  — raw SSE event payloads
 */

const AGENTS = [
  {
    id: "intake",
    name: "Intake Agent",
    nameHi: "केस विश्लेषण",
    desc: "Extracting case details...",
  },
  {
    id: "research",
    name: "Legal Research",
    nameHi: "कानूनी शोध",
    desc: "Finding applicable law sections...",
  },
  {
    id: "drafter",
    name: "Document Drafter",
    nameHi: "दस्तावेज़ तैयारी",
    desc: "Drafting your document...",
  },
  {
    id: "verifier",
    name: "Verifier",
    nameHi: "सत्यापन",
    desc: "Quality checking the draft...",
  },
  {
    id: "filing_assistant",
    name: "Filing Assistant",
    nameHi: "दाखिल करें",
    desc: "Preparing filing instructions...",
  },
];

function CircleIndicator({ stepNumber, status }) {
  const base =
    "flex h-10 w-10 shrink-0 items-center justify-center rounded-full font-bold text-sm transition-colors duration-300";

  if (status === "complete") {
    return (
      <div className={`${base} bg-emerald-500 text-white`}>
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    );
  }

  if (status === "running") {
    return (
      <div className={`${base} animate-pulse bg-amber-500 text-zinc-950 animate-amber-glow`}>
        {stepNumber}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className={`${base} bg-red-500 text-white`}>
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    );
  }

  // waiting
  return (
    <div className={`${base} bg-zinc-700 text-zinc-400`}>
      {stepNumber}
    </div>
  );
}

function getStatusText(status, agentId, events) {
  if (status === "waiting") return { text: "Waiting...", className: "text-zinc-500" };
  if (status === "running") return { text: "Processing...", className: "text-amber-400 animate-pulse" };
  if (status === "error") return { text: "Error", className: "text-red-400" };

  if (status === "complete") {
    const completedEvent = [...(events || [])]
      .reverse()
      .find((e) => e.agent === agentId && e.status === "complete");

    let suffix = "";
    if (completedEvent?.data) {
      const d = completedEvent.data;
      if (agentId === "research" && d.sections_found != null) {
        suffix = ` — Found ${d.sections_found} section${d.sections_found !== 1 ? "s" : ""}`;
      } else if (agentId === "intake" && d.doc_type) {
        suffix = ` — ${d.doc_type}`;
      } else if (d.summary) {
        suffix = ` — ${d.summary}`;
      }
    }
    return { text: `Complete${suffix}`, className: "text-emerald-400" };
  }
  return { text: "", className: "text-zinc-500" };
}

export default function AgentPipeline({ agentStatuses = {}, events = [] }) {
  return (
    <div className="space-y-4">
      <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
        AI Agent Pipeline
      </p>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="flex flex-col gap-0">
          {AGENTS.map((agent, idx) => {
            const status = agentStatuses[agent.id] ?? "waiting";
            const { text: statusText, className: statusClass } = getStatusText(
              status,
              agent.id,
              events
            );
            const isLast = idx === AGENTS.length - 1;
            // Connector animates to emerald when the step above is complete
            const connectorDone = status === "complete";

            return (
              <div key={agent.id}>
                <div className="flex items-start gap-4">
                  <CircleIndicator stepNumber={idx + 1} status={status} />
                  <div className="flex-1 pb-2 pt-1">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="font-semibold text-zinc-100 text-sm">{agent.name}</span>
                      <span className="font-devanagari text-xs text-zinc-500">{agent.nameHi}</span>
                    </div>
                    <p className={`text-xs mt-0.5 transition-colors duration-200 ${statusClass}`}>
                      {statusText || agent.desc}
                    </p>
                  </div>
                  <span className="font-mono text-xs text-zinc-600 pt-1.5 shrink-0">
                    {idx + 1}/{AGENTS.length}
                  </span>
                </div>

                {!isLast && (
                  <div
                    className={`ml-5 h-6 w-0.5 transition-colors duration-500 ${
                      connectorDone ? "bg-emerald-500" : "bg-zinc-700"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
