/**
 * FilingAssistant.jsx — Shows portal info, step-by-step instructions,
 * field mapping, and warnings for filing the generated document.
 */

import { useState } from "react";

const MODE_CONFIG = {
  online: {
    label: "Online Filing Available",
    labelHi: "ऑनलाइन दाखिल करें",
    color: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
    dot: "bg-emerald-400",
  },
  offline: {
    label: "In-Person Filing Required",
    labelHi: "पुलिस स्टेशन जाएं",
    color: "text-amber-400",
    border: "border-amber-500/30",
    bg: "bg-amber-500/10",
    dot: "bg-amber-400",
  },
  post: {
    label: "Send via Registered Post",
    labelHi: "रजिस्टर्ड डाक से भेजें",
    color: "text-blue-400",
    border: "border-blue-500/30",
    bg: "bg-blue-500/10",
    dot: "bg-blue-400",
  },
};

export default function FilingAssistant({ data }) {
  const [showHindi, setShowHindi] = useState(false);

  if (!data) return null;

  const {
    portal_name,
    portal_url,
    filing_mode,
    portal_note,
    steps = [],
    fields_mapping = [],
    required_documents = [],
    warnings = [],
  } = data;

  const mode = MODE_CONFIG[filing_mode] || MODE_CONFIG.offline;

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 overflow-hidden">
      {/* Header */}
      <div className="border-b border-zinc-800 px-6 py-5 flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">
            Next Steps — Filing Guide
          </p>
          <h3 className="text-lg font-semibold text-zinc-100">
            How to Submit Your Document
          </h3>
          <p className="text-zinc-400 text-sm mt-0.5">दस्तावेज़ कैसे जमा करें</p>
        </div>
        {steps.length > 0 && (
          <button
            onClick={() => setShowHindi((v) => !v)}
            className="shrink-0 text-xs font-mono border border-zinc-700 rounded-lg px-3 py-1.5 text-zinc-400 hover:text-zinc-200 hover:border-zinc-500 transition-colors"
          >
            {showHindi ? "EN" : "हिं"}
          </button>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Portal card */}
        <div className={`rounded-xl border ${mode.border} ${mode.bg} p-4`}>
          <div className="flex items-center gap-2 mb-2">
            <span className={`h-2 w-2 rounded-full shrink-0 ${mode.dot}`} />
            <span className={`text-sm font-semibold ${mode.color}`}>{mode.label}</span>
            <span className="text-zinc-600 text-xs">·</span>
            <span className="text-zinc-500 text-xs">{mode.labelHi}</span>
          </div>
          <p className="text-zinc-200 font-medium text-sm">{portal_name}</p>
          {portal_note && (
            <p className="text-zinc-400 text-xs mt-1">{portal_note}</p>
          )}
          {portal_url && (
            <a
              href={portal_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-1.5 mt-3 text-sm font-medium ${mode.color} hover:underline`}
            >
              Open Portal &#8599;
            </a>
          )}
        </div>

        {/* Step-by-step instructions */}
        {steps.length > 0 && (
          <div>
            <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-3">
              Step-by-Step Instructions
            </h4>
            <ol className="space-y-3">
              {steps.map((step, i) => (
                <li key={i} className="flex gap-3">
                  <span className="shrink-0 h-6 w-6 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-bold text-amber-400">
                    {i + 1}
                  </span>
                  <div className="pt-0.5">
                    <p className="text-sm text-zinc-200">{step.en}</p>
                    {showHindi && step.hi && (
                      <p className="text-xs text-zinc-500 mt-0.5 font-devanagari">{step.hi}</p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Field mapping table */}
        {fields_mapping.length > 0 && (
          <div>
            <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-3">
              Form Fields — What to Fill
            </h4>
            <div className="rounded-xl border border-zinc-800 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900">
                    <th className="text-left px-4 py-2.5 text-xs font-mono uppercase tracking-wider text-zinc-500 w-2/5">
                      Field on Form
                    </th>
                    <th className="text-left px-4 py-2.5 text-xs font-mono uppercase tracking-wider text-zinc-500">
                      Your Value
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {fields_mapping.map((row, i) => (
                    <tr
                      key={i}
                      className={`border-b border-zinc-800/60 last:border-0 ${i % 2 === 0 ? "" : "bg-zinc-900/40"}`}
                    >
                      <td className="px-4 py-3 text-zinc-400 font-mono text-xs align-top">
                        {row.field}
                      </td>
                      <td className="px-4 py-3 align-top">
                        <span
                          className={
                            row.value?.startsWith("[")
                              ? "text-amber-400 font-medium text-xs"
                              : "text-zinc-200 text-xs"
                          }
                        >
                          {row.value}
                        </span>
                        {row.hint && (
                          <p className="text-zinc-600 text-xs mt-0.5">{row.hint}</p>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Required documents */}
        {required_documents.length > 0 && (
          <div>
            <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-3">
              Documents to Upload
            </h4>
            <ul className="space-y-2">
              {required_documents.map((doc, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span className="text-emerald-500 mt-0.5 shrink-0">&#10003;</span>
                  <span className="text-zinc-300">{doc}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div>
            <h4 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-3">
              Important Notes
            </h4>
            <ul className="space-y-2">
              {warnings.map((w, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span className="text-amber-500 mt-0.5 shrink-0">&#9888;</span>
                  <span className="text-zinc-400">{w}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
