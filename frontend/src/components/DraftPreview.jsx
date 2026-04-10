/**
 * DraftPreview.jsx
 *
 * Renders the generated legal document in a "paper" style panel.
 * - White background, serif font, legal document margins
 * - BNS/BNSS/BSA/NI Act section references highlighted in amber
 * - Devanagari text detected and rendered with Noto Sans Devanagari
 * - Skeleton loader shown while draft is null
 *
 * Props:
 *   draft (string|null) — full document text from the drafter agent
 */

import { useMemo } from "react";

// Regex to match section references: BNS 302, BNSS 173, BSA 65, Section 138, NI Act 138, धारा 173
const SECTION_REGEX =
  /\b(BNS|BNSS|BSA|NI\s+Act|Section|Sec\.|IPC|CrPC)\s+\d+[\w()]*\b/gi;

// Detect if a string contains Devanagari characters
function hasDevanagari(str) {
  return /[\u0900-\u097F]/.test(str);
}

function renderLine(line, lineIdx) {
  const trimmed = line.trim();

  // Empty line — spacer
  if (!trimmed) {
    return <div key={lineIdx} className="h-3" />;
  }

  // Heading: ALL CAPS line or lines starting with #
  const isHeading =
    trimmed.startsWith("#") ||
    (trimmed === trimmed.toUpperCase() && trimmed.length > 3 && /[A-Z]/.test(trimmed));

  const devanagariClass = hasDevanagari(trimmed)
    ? "font-['Noto_Sans_Devanagari',_sans-serif]"
    : "";

  // Highlight section references within a line
  function annotate(text) {
    const parts = [];
    let lastIndex = 0;
    let match;
    const regex = new RegExp(SECTION_REGEX.source, "gi");

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      parts.push(
        <mark
          key={match.index}
          className="bg-amber-100 text-amber-900 px-1 rounded"
        >
          {match[0]}
        </mark>
      );
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    return parts;
  }

  if (isHeading) {
    const headingText = trimmed.startsWith("#") ? trimmed.replace(/^#+\s*/, "") : trimmed;
    return (
      <h3
        key={lineIdx}
        className={`font-bold text-lg mt-4 mb-2 text-zinc-900 ${devanagariClass}`}
      >
        {annotate(headingText)}
      </h3>
    );
  }

  return (
    <p key={lineIdx} className={`mb-1 leading-relaxed text-zinc-800 ${devanagariClass}`}>
      {annotate(trimmed)}
    </p>
  );
}

function SkeletonLoader() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="h-4 bg-zinc-700 rounded w-1/3 mx-auto" />
      <div className="h-3 bg-zinc-700 rounded w-full" />
      <div className="h-3 bg-zinc-700 rounded w-5/6" />
      <div className="h-3 bg-zinc-700 rounded w-full" />
      <div className="h-3 bg-zinc-700 rounded w-4/5" />
      <div className="h-3 bg-zinc-700 rounded w-full" />
      <div className="h-3 bg-zinc-700 rounded w-3/4" />
    </div>
  );
}

export default function DraftPreview({ draft = null }) {
  const renderedLines = useMemo(() => {
    if (!draft) return null;
    return draft.split("\n").map((line, idx) => renderLine(line, idx));
  }, [draft]);

  return (
    <div className="space-y-3">
      {/* Section label */}
      <p className="font-semibold text-zinc-300 mb-1">Document Preview</p>

      {/* Paper container */}
      {draft ? (
        <div className="bg-white text-zinc-900 rounded-xl p-8 max-h-96 overflow-y-auto font-serif shadow-xl">
          {renderedLines}
        </div>
      ) : (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8">
          <p className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-4">
            Generating document...
          </p>
          <SkeletonLoader />
        </div>
      )}
    </div>
  );
}
