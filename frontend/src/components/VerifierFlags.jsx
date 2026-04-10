/**
 * VerifierFlags.jsx
 *
 * Displays the VerifierAgent's quality report:
 *   - Score circle (color-coded 1-10)
 *   - Overall quality badge
 *   - Issues list with severity pills (high/medium/low)
 *   - Recommendations bullet list
 *   - Missing fields warning box
 *
 * Props:
 *   verification (object|null) — VerifierAgent output:
 *     {
 *       score: number (1-10),
 *       overall_quality: string,
 *       issues: [{ severity: 'high'|'medium'|'low', field: string, suggestion: string }],
 *       recommendations: string[],
 *       missing_fields: string[],
 *     }
 */

function ScoreCircle({ score }) {
  const colorClass =
    score >= 8
      ? "bg-emerald-500"
      : score >= 5
      ? "bg-amber-500"
      : "bg-red-500";

  return (
    <div
      className={`flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-full ${colorClass} text-white shadow-lg`}
    >
      <span className="text-2xl font-bold leading-none">{score}/10</span>
      <span className="text-xs leading-tight mt-0.5">Score</span>
    </div>
  );
}

const SEVERITY_PILL = {
  high: "bg-red-500/20 text-red-400 border border-red-500/30",
  medium: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
  low: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
};

const QUALITY_BADGE = {
  excellent: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  good: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  fair: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  poor: "bg-red-500/15 text-red-400 border-red-500/30",
};

export default function VerifierFlags({ verification = null }) {
  if (!verification) return null;

  const {
    score = 0,
    overall_quality = "fair",
    issues = [],
    recommendations = [],
    missing_fields = [],
  } = verification;

  const qualityStyle =
    QUALITY_BADGE[overall_quality?.toLowerCase()] ?? QUALITY_BADGE.fair;

  return (
    <div className="space-y-5">
      {/* Header */}
      <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
        Verification Report
      </p>

      {/* Score row */}
      <div className="flex items-center gap-5">
        <ScoreCircle score={score} />
        <div className="space-y-2">
          <p className="text-zinc-100 font-semibold">Quality Score</p>
          <span
            className={`inline-block rounded border px-3 py-0.5 font-mono text-xs capitalize ${qualityStyle}`}
          >
            {overall_quality}
          </span>
          {score >= 8 && (
            <p className="text-xs text-emerald-400">
              This document meets standard quality requirements.
            </p>
          )}
        </div>
      </div>

      {/* Missing fields warning */}
      {missing_fields.length > 0 && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 space-y-1">
          <p className="font-mono text-xs uppercase tracking-widest text-red-400">
            Missing Information
          </p>
          <ul className="space-y-1 text-sm text-red-300">
            {missing_fields.map((field, idx) => (
              <li key={idx} className="flex items-center gap-2">
                <span className="text-red-500">&#8226;</span>
                {field}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issues list */}
      {issues.length > 0 && (
        <div className="space-y-2">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">Issues</p>
          <ul className="space-y-2">
            {issues.map((issue, idx) => {
              const severityStyle =
                SEVERITY_PILL[issue.severity?.toLowerCase()] ?? SEVERITY_PILL.low;
              return (
                <li
                  key={idx}
                  className="flex items-start gap-3 rounded-lg border border-zinc-800 bg-zinc-900 p-3"
                >
                  {/* Severity pill */}
                  <span
                    className={`shrink-0 rounded px-2 py-0.5 text-xs font-semibold capitalize ${severityStyle}`}
                  >
                    {issue.severity ?? "low"}
                  </span>
                  <div className="min-w-0">
                    {issue.field && (
                      <p className="text-zinc-300 font-medium text-sm truncate">
                        {issue.field}
                      </p>
                    )}
                    {issue.suggestion && (
                      <p className="text-zinc-400 text-xs mt-0.5 leading-relaxed">
                        {issue.suggestion}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 space-y-3">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
            Recommendations
          </p>
          <ul className="space-y-2">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-zinc-300">
                <span className="text-amber-500 shrink-0 mt-0.5">&#8250;</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
