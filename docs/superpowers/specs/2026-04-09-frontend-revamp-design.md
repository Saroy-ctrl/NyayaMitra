# NyayaMitra Frontend Revamp — Design Spec
**Date:** 2026-04-09
**Approach:** Option B — Enhanced single-page state machine (no React Router, no new deps)

---

## 1. Goals

Revamp the NyayaMitra frontend into a polished, multi-view experience that:
- Adds a landing page conveying the product's mission and impact
- Gives each step (select doc → describe → processing → results) its own full-screen view with clean transitions
- Preserves all existing SSE/pipeline/API logic without modification
- Uses 21st.dev MCP components where available (hero, stat cards, doc type cards)
- Is verified end-to-end with Playwright MCP after implementation

**Non-goals:** No React Router. No backend changes. No new state management library. No auth.

---

## 2. Architecture

### State Machine (App.jsx)
Add one new view constant:

```
VIEWS: LANDING → SELECT_DOC → INPUT_CASE → PROCESSING → VIEW_RESULTS
```

`LANDING` is the initial view (was `SELECT_DOC`). All existing transitions are shifted one step forward. The `isComplete` SSE trigger still moves `PROCESSING → VIEW_RESULTS`.

### View transitions
- Every view swap calls `window.scrollTo(0, 0)`
- CSS classes on a wrapper div: `transition-all duration-200 ease-out`
- Enter: `opacity-0 translate-y-2` → `opacity-100 translate-y-0`
- Implemented via a `key` prop change on the view wrapper, forcing React remount + CSS transition

### File changes
| File | Action |
|------|--------|
| `src/App.jsx` | Add `LANDING` view, add `ProcessingPage`, extract `ResultsPage`, wire transitions |
| `src/components/LandingPage.jsx` | New — hero, stats, doc strip, CTA |
| `src/components/DocTypeSelector.jsx` | Revamp styling — richer cards, hover glow, step indicator |
| `src/components/CaseInput.jsx` | Revamp styling — doc badge prominent, larger textarea, step indicator |
| `src/components/ProcessingPage.jsx` | New — full-screen pipeline view extracted from App.jsx inline block |
| `src/components/ResultsPage.jsx` | New — extracted from App.jsx VIEW_RESULTS inline block, stacked layout |
| `src/components/AgentPipeline.jsx` | Minor: animated connector lines, 5th agent (filing_assistant) added |
| `src/components/DraftPreview.jsx` | Minor styling only — no logic changes |
| `src/components/VerifierFlags.jsx` | Minor styling only — no logic changes |
| `src/components/FilingAssistant.jsx` | No changes |
| `src/components/PDFDownload.jsx` | No changes |
| `src/hooks/useSSE.js` | No changes |
| `src/lib/api.js` | No changes |

---

## 3. View Specifications

### 3.1 LANDING — `LandingPage.jsx`

**Layout:** Full viewport hero + sections below.

**Hero section:**
- Background: `bg-zinc-950` with subtle radial gradient from amber at center
- Large headline: "न्यायमित्र" (Devanagari, large, amber) + "NyayaMitra" below it
- Tagline: "AI-powered legal documents for every Indian — in Hindi, for free"
- Sub-tagline: "Powered by Llama 3.3 · BNS 2023 · ChromaDB · 1,423 law sections"
- Primary CTA button: "Get Started →" (amber, bold) → triggers `onGetStarted()`
- Secondary link: "Try Demo ⚡" → triggers `onDemo()`

**Stats row (3 cards):**
- "50M+ pending cases" / "₹3,000–15,000 lawyer fees" / "₹0 with NyayaMitra"
- Cards: `bg-zinc-900 border border-zinc-800 rounded-xl`, amber number, zinc-400 label
- 21st.dev MCP: request stat card component if available

**Document types preview strip:**
- 5 doc type cards in a horizontal scroll row (non-clickable, decorative)
- Same styling as SELECT_DOC cards but with `pointer-events-none opacity-80`
- Visible on desktop, hidden on mobile (shows 3 on sm)

**How it works (3 steps):**
- "1. Describe your situation" / "2. AI agents research & draft" / "3. Download + file"
- Simple numbered row, zinc-700 connector lines between them

**Footer note:** "Not a substitute for professional legal advice · कानूनी सलाह के लिए वकील से मिलें"

**Props:** `onGetStarted()`, `onDemoClick()`

---

### 3.2 SELECT_DOC — `DocTypeSelector.jsx` (revamped)

**Layout:** Full page, centered max-w-5xl.

**Header:**
- Step indicator: `Step 1 of 3` (font-mono, zinc-500)
- H2: "What document do you need?"
- Subtitle: "आपको किस प्रकार का दस्तावेज़ चाहिए? नीचे से चुनें।"
- Back link: "← Back" → returns to `LANDING`

**Card grid:** `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`

Each card:
- Large icon (text-4xl)
- EN title (font-semibold, zinc-100)
- HI title (font-devanagari, zinc-400)
- EN description (zinc-500, text-sm)
- HI description (font-devanagari, zinc-600, text-xs)
- Law badge (font-mono, amber-400, bg-zinc-800)
- Hover: `border-amber-500 bg-zinc-800 scale-[1.02] shadow-amber-500/10 shadow-lg`
- Selected: `border-amber-500 ring-2 ring-amber-500/30 bg-zinc-800`
- Transition: `transition-all duration-200`

**Demo row:** Same as existing — "Try a pre-filled example" + "⚡ Try Demo" amber button.

**Props:** `onSelect(docType)`, `onDemoClick()`, `onBack()`

---

### 3.3 INPUT_CASE — `CaseInput.jsx` (revamped)

**Layout:** Full page, centered max-w-3xl.

**Header:**
- Step indicator: `Step 2 of 3`
- Doc type badge (prominent, amber) + "← Change type" link
- H2: "Describe your situation"
- Subtitle: "अपनी बात हिंदी या English में लिखें — जैसे किसी दोस्त को बताते हैं"

**Textarea:**
- `h-52 w-full` (slightly taller)
- `font-devanagari` for Devanagari support
- Focus: amber border + amber ring glow
- Placeholder: "Apna case describe karein... (Hindi ya English mein)"
- Character count bottom-right (inside relative container)

**Action row:**
- Primary: "Generate Document →" (amber gradient, full-width on mobile)
- Ghost: "Try example ⚡" (border-zinc-700)
- Loading state: spinner + "Starting pipeline..."

**Helper text:** "Your data is not stored permanently. Minimum 20 chars recommended."

**Props:** `docType`, `onSubmit(description)`, `onBack()`, `isLoading`, `initialText`

---

### 3.4 PROCESSING — `ProcessingPage.jsx` (new)

**Layout:** Full page, centered max-w-2xl, vertically centered content.

**Header block:**
- `font-mono text-xs uppercase tracking-widest text-zinc-500`: "Processing Your Case"
- H2: "AI agents are drafting your document..."
- Hindi: "दस्तावेज़ तैयार हो रहा है — कृपया प्रतीक्षा करें"
- Spinner icon (amber, animated)

**Pipeline component (`AgentPipeline.jsx`):**
- 5 agents (add `filing_assistant` — "Filing Assistant / दाखिल करें" — to the AGENTS array)
- Connector lines: when step N completes, connector line N→N+1 animates from `bg-zinc-700` → `bg-emerald-500` over 400ms
- Each agent row: CircleIndicator + name EN + name HI + status text
- Status text uses SSE event data (existing `getStatusText` logic unchanged)

**Error display:** Inline red box if `sseError` fires.

**Props:** `agentStatuses`, `events`, `sseError`

---

### 3.5 VIEW_RESULTS — `ResultsPage.jsx` (new)

**Layout:** Full page, centered max-w-5xl. All sections stacked, full scroll.

**Header row:**
- Left: "Results" label (font-mono zinc-500) + "Your document is ready" H2 + Hindi subtitle
- Right: "← Start Over" button (border-zinc-700)

**Collapsed pipeline summary:**
- `AgentPipeline` with all steps showing `complete` — compact, read-only summary

**Section 1 — Document Preview:**
- `DraftPreview` unchanged (white paper card, serif, amber section highlights)

**Section 2 — Verification Report:**
- `VerifierFlags` unchanged (score circle, issues, recommendations)

**Section 3 — Filing Guide:**
- `FilingAssistant` unchanged (portal card, steps, field mapping, required docs)

**Section 4 — PDF Download:**
- `PDFDownload` component, styled as a prominent amber CTA at the bottom

**Props:** `agentStatuses`, `events`, `draft`, `verification`, `filingData`, `sessionId`, `isComplete`, `onReset()`

---

## 4. App.jsx Changes

```
VIEWS = { LANDING, SELECT_DOC, INPUT_CASE, PROCESSING, VIEW_RESULTS }
```

- Initial view: `LANDING` (was `SELECT_DOC`)
- `handleGetStarted()` → `setView(VIEWS.SELECT_DOC)`
- `handleDocTypeSelect(type)` → sets `selectedDoc`, transitions to `INPUT_CASE`
- `handleCaseSubmit(desc)` → starts pipeline, transitions to `PROCESSING`
- SSE `isComplete` → transitions `PROCESSING → VIEW_RESULTS`
- `handleReset()` → resets all state, goes back to `LANDING`
- `handleDemoClick()` → sets demo doc type + text, goes to `INPUT_CASE`
- View wrapper: `<div key={view} className="animate-fade-in">` with custom CSS class for enter transition
- Add to `index.css`:
  ```css
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .animate-fade-in { animation: fadeInUp 0.2s ease-out; }
  ```

---

## 5. 21st.dev MCP Usage

Use 21st.dev MCP component builder during implementation for:
1. **Hero section** in LandingPage — request a dark-themed hero with bilingual headline + CTA
2. **Stat cards** in LandingPage — 3-card row with large number + label
3. **Doc type cards** in DocTypeSelector — card with icon, title, badge, hover effect

If 21st.dev components do not match the zinc/amber design system, fall back to hand-written Tailwind.

---

## 6. Playwright MCP Verification Plan

After all views are implemented, run the following test sequence:

| Step | Action | Assertion |
|------|--------|-----------|
| 1 | Load app at localhost:5173 | Hero headline "NyayaMitra" visible |
| 2 | Click "Get Started" | Doc type cards (5) visible |
| 3 | Click "FIR" card | Textarea visible, doc badge shows "FIR" |
| 4 | Click "Try example ⚡" | Textarea filled with demo text |
| 5 | Click "Generate Document →" | Pipeline view shown, agent steps visible |
| 6 | Wait for pipeline completion (SSE `complete`) | Results page shown with draft preview |
| 7 | Scroll to PDF section | "Download PDF" button visible |
| 8 | Click PDF download | Request to `/download-pdf/{sessionId}` returns 200 |
| 9 | Click "Start Over" | Landing page shown again |
| 10 | Click "Try Demo ⚡" on landing | Input page shown with pre-filled Hinglish text |

---

## 7. Constraints

- No React Router — view state machine only
- No animation libraries (framer-motion, etc.) — CSS + Tailwind only
- No backend changes — zero modifications to `backend/`
- No changes to `useSSE.js`, `api.js`, `PDFDownload.jsx`, `FilingAssistant.jsx`
- All existing SSE event schema, session ID flow, pipeline orchestration untouched
- Dark zinc/amber design system maintained throughout
- Bilingual (EN + HI) text in every view header
- ASCII-safe — no Unicode symbols in `console.log` / `print()` (Windows constraint)
