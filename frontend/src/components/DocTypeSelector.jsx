/**
 * DocTypeSelector.jsx — View 2 (SELECT_DOC)
 *
 * Step 1 of 3. Full-page card grid for choosing document type.
 * Richer cards with hover glow, scale, EN+HI labels.
 *
 * Props:
 *   onSelect(docType: string) — called with doc_type key when a card is clicked
 *   onDemoClick()             — pre-filled demo flow
 *   onBack()                  — return to LANDING view
 */

import { useState } from "react";

const DOC_TYPES = [
  {
    id: "fir",
    icon: "📋",
    title: "FIR",
    titleHi: "प्रथम सूचना रिपोर्ट",
    desc: "Report a crime to the police",
    descHi: "पुलिस में शिकायत दर्ज करें",
    laws: "BNS 2023 + BNSS 2023",
  },
  {
    id: "legal_notice",
    icon: "⚖️",
    title: "Legal Notice",
    titleHi: "कानूनी नोटिस",
    desc: "Formal demand letter with legal backing",
    descHi: "कानूनी मांग पत्र",
    laws: "BNS 2023",
  },
  {
    id: "consumer_complaint",
    icon: "🛒",
    title: "Consumer Complaint",
    titleHi: "उपभोक्ता शिकायत",
    desc: "File with Consumer Commission",
    descHi: "उपभोक्ता आयोग में शिकायत",
    laws: "Consumer Protection Act 2019",
  },
  {
    id: "cheque_bounce",
    icon: "💰",
    title: "Cheque Bounce Notice",
    titleHi: "चेक बाउंस नोटिस",
    desc: "Demand payment for dishonoured cheque",
    descHi: "बाउंस हुए चेक की वसूली",
    laws: "NI Act §138",
  },
  {
    id: "tenant_eviction",
    icon: "🏠",
    title: "Tenant Eviction Notice",
    titleHi: "बेदखली नोटिस",
    desc: "Notice to vacate the premises",
    descHi: "किरायेदार को खाली करने की नोटिस",
    laws: "Transfer of Property Act + Delhi RCA",
  },
];

export default function DocTypeSelector({ onSelect, onDemoClick, onBack }) {
  const [selected, setSelected] = useState(null);

  function handleSelect(id) {
    setSelected(id);
    onSelect(id);
  }

  return (
    <div className="space-y-8">
      {/* Heading row */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">Step 1 of 3</p>
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 transition-colors duration-200"
          >
            &#8592; Back
          </button>
        </div>
        <h2 className="text-2xl font-semibold text-zinc-100">What document do you need?</h2>
        <p className="text-zinc-400 text-sm">
          आपको किस प्रकार का दस्तावेज़ चाहिए? नीचे से चुनें।
        </p>
      </div>

      {/* Document type grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {DOC_TYPES.map((doc, idx) => {
          const isSelected = selected === doc.id;
          return (
            <button
              key={doc.id}
              onClick={() => handleSelect(doc.id)}
              className={[
                `flex flex-col gap-3 rounded-xl border p-5 text-left transition-all duration-200 cursor-pointer card-reveal card-reveal-${idx + 1}`,
                isSelected
                  ? "border-amber-500 bg-zinc-800/90 ring-2 ring-amber-500/30 shadow-lg shadow-amber-500/10"
                  : "border-zinc-800 bg-zinc-900/80 backdrop-blur-sm hover:border-amber-500 hover:bg-zinc-800/90 hover:scale-[1.02] hover:shadow-lg hover:shadow-amber-500/10",
              ].join(" ")}
            >
              {/* Icon */}
              <span className="text-4xl leading-none">{doc.icon}</span>

              {/* Titles */}
              <div>
                <p className="font-semibold text-zinc-100">{doc.title}</p>
                <p className="font-devanagari text-sm text-zinc-400 mt-0.5">{doc.titleHi}</p>
              </div>

              {/* Description */}
              <p className="text-sm text-zinc-500 leading-snug">{doc.desc}</p>
              <p className="font-devanagari text-xs text-zinc-600">{doc.descHi}</p>

              {/* Law badge */}
              <span className="inline-block self-start rounded bg-zinc-800 border border-zinc-700 px-2 py-0.5 font-mono text-xs text-amber-400">
                {doc.laws}
              </span>
            </button>
          );
        })}
      </div>

      {/* Demo button row */}
      <div className="flex flex-col items-center gap-3 pt-2 border-t border-zinc-800">
        <p className="text-sm text-zinc-500">
          Want to see how it works? Try a pre-filled example.
        </p>
        <button
          onClick={onDemoClick}
          className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold px-6 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
        >
          <span>&#9889;</span>
          Try Demo
        </button>
      </div>
    </div>
  );
}
