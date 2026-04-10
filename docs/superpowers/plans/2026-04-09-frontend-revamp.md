# NyayaMitra Frontend Revamp — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revamp the NyayaMitra frontend into a polished 5-view single-page app (Landing → Select Doc → Describe → Processing → Results) while preserving all existing SSE/pipeline/API logic.

**Architecture:** Enhanced state machine in App.jsx — add `LANDING` as the initial view, extract `ProcessingPage` and `ResultsPage` into dedicated components, and add a new `LandingPage` component. All view transitions use a CSS `animate-fade-in` keyframe triggered by React remounting on key change.

**Tech Stack:** React 18, Vite, Tailwind CSS, 21st.dev MCP (hero + stats in LandingPage), Playwright MCP (e2e verification)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/index.css` | Modify | Add `@keyframes fadeInUp` + `.animate-fade-in` class |
| `frontend/src/App.jsx` | Modify | Add `LANDING` view, `handleGetStarted`, update `handleReset`, wire all 5 views |
| `frontend/src/components/LandingPage.jsx` | Create | Hero, stats, how-it-works, doc preview strip, CTAs |
| `frontend/src/components/DocTypeSelector.jsx` | Modify | Add `onBack` prop, richer cards with hover glow + scale, step indicator |
| `frontend/src/components/CaseInput.jsx` | Modify | Larger textarea, prominent doc badge, step indicator |
| `frontend/src/components/AgentPipeline.jsx` | Modify | Add `filing_assistant` as 5th agent, animate connector lines on completion |
| `frontend/src/components/ProcessingPage.jsx` | Create | Full-screen processing view wrapping AgentPipeline |
| `frontend/src/components/ResultsPage.jsx` | Create | Stacked results: pipeline summary, draft, verifier, filing guide, PDF download |

**Unchanged files (zero modifications):**
- `frontend/src/hooks/useSSE.js`
- `frontend/src/lib/api.js`
- `frontend/src/components/FilingAssistant.jsx`
- `frontend/src/components/PDFDownload.jsx`
- `frontend/src/components/DraftPreview.jsx`
- `frontend/src/components/VerifierFlags.jsx`
- Everything in `backend/`

---

## Task 1: Add fade-in animation to index.css

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Add the keyframe and utility class**

Open `frontend/src/index.css` and append after the existing `.font-devanagari` rule:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Devanagari font stack for Hindi text */
.font-devanagari {
  font-family: "Noto Sans Devanagari", "Noto Serif Devanagari", sans-serif;
}

/* View transition animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fadeInUp 0.2s ease-out;
}
```

- [ ] **Step 2: Verify dev server still compiles**

```bash
cd frontend && npm run dev
```

Expected: No CSS compilation errors. Browser at `localhost:5173` still loads.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: add fade-in view transition animation"
```

---

## Task 2: Add LANDING view to App.jsx state machine

**Files:**
- Modify: `frontend/src/App.jsx`

This task only touches the VIEWS constant, initial state, and the two handler functions. The JSX render section is updated in Task 9.

- [ ] **Step 1: Update VIEWS constant and add handleGetStarted**

In `frontend/src/App.jsx`, replace the VIEWS object and add `handleGetStarted`:

```jsx
const VIEWS = {
  LANDING: "LANDING",
  SELECT_DOC: "SELECT_DOC",
  INPUT_CASE: "INPUT_CASE",
  PROCESSING: "PROCESSING",
  VIEW_RESULTS: "VIEW_RESULTS",
};

// Demo pre-fill: tenant eviction in Hinglish
const DEMO_DOC_TYPE = "tenant_eviction";
const DEMO_DESCRIPTION =
  "Mera naam Ramesh Kumar hai. Main Lajpat Nagar, Delhi mein kiraya par rehta tha. " +
  "Makaan malik ne bina kisi notice ke mujhe ghar se nikaalne ki koshish ki aur mere saamaan bahar rakh diye. " +
  "Maine 3 saal ka kiraya diya hai aur kabhi late nahi ki. " +
  "Ab wo keh raha hai ki ghar khaali karo kyunki uske bete ko chahiye. Mujhe apna haq chahiye.";
```

- [ ] **Step 2: Change initial view and update handleReset + add handleGetStarted**

In the `App()` function body, change the initial view and update handlers:

```jsx
export default function App() {
  const [view, setView] = useState(VIEWS.LANDING);   // was VIEWS.SELECT_DOC
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [pipelineStarted, setPipelineStarted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [pipelineError, setPipelineError] = useState(null);
  const [demoText, setDemoText] = useState(null);

  const { events, agentStatuses, isComplete, error: sseError, draft, verification, filingData } = useSSE(
    pipelineStarted ? sessionId : null
  );

  useEffect(() => {
    if (isComplete && view === VIEWS.PROCESSING) {
      setView(VIEWS.VIEW_RESULTS);
    }
  }, [isComplete, view]);

  async function handleCaseSubmit(description) {
    const sid = generateSessionId();
    setSessionId(sid);
    setPipelineError(null);
    setIsLoading(true);

    try {
      await startPipeline(selectedDoc, description, sid);
      setPipelineStarted(true);
      setView(VIEWS.PROCESSING);
    } catch (err) {
      setPipelineError(err.message ?? "Failed to start pipeline. Is the backend running?");
      setIsLoading(false);
    }
  }

  function handleGetStarted() {
    setView(VIEWS.SELECT_DOC);
  }

  function handleDocTypeSelect(type) {
    setSelectedDoc(type);
    setDemoText(null);
    setView(VIEWS.INPUT_CASE);
  }

  function handleDemoClick() {
    setSelectedDoc(DEMO_DOC_TYPE);
    setDemoText(DEMO_DESCRIPTION);
    setView(VIEWS.INPUT_CASE);
  }

  function handleReset() {
    setView(VIEWS.LANDING);          // was VIEWS.SELECT_DOC
    setSelectedDoc(null);
    setSessionId(null);
    setPipelineStarted(false);
    setIsLoading(false);
    setPipelineError(null);
    setDemoText(null);
  }

  // JSX return — unchanged for now, updated in Task 9
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="border-b border-zinc-800 px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <button
            onClick={handleReset}
            className="text-left transition-opacity duration-200 hover:opacity-75"
          >
            <div className="flex items-center gap-2">
              <span className="text-xl">&#9878;</span>
              <div>
                <span className="font-bold text-amber-500 text-lg leading-none">NyayaMitra</span>
                <p className="font-mono text-xs text-zinc-500 leading-none mt-0.5">
                  AI Legal Document Assistant &bull; न्यायमित्र
                </p>
              </div>
            </div>
          </button>
          <span className="hidden sm:block font-mono text-xs text-zinc-600">
            Powered by Llama 3.3 &bull; भारत
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <div key={view} className="animate-fade-in">
          {view === VIEWS.LANDING && (
            <div className="text-zinc-400">Landing page coming in Task 3...</div>
          )}
          {view === VIEWS.SELECT_DOC && (
            <div className="text-zinc-400">Select doc coming in Task 4...</div>
          )}
          {view === VIEWS.INPUT_CASE && (
            <div className="text-zinc-400">Input case coming in Task 5...</div>
          )}
          {view === VIEWS.PROCESSING && (
            <div className="text-zinc-400">Processing coming in Task 7...</div>
          )}
          {view === VIEWS.VIEW_RESULTS && (
            <div className="text-zinc-400">Results coming in Task 8...</div>
          )}
        </div>
      </main>

      <footer className="border-t border-zinc-800 px-4 py-6 mt-12 text-center">
        <p className="font-mono text-xs text-zinc-600">
          NyayaMitra &bull; Not a substitute for professional legal advice &bull; कानूनी सलाह के लिए वकील से मिलें
        </p>
      </footer>
    </div>
  );
}
```

- [ ] **Step 3: Verify app loads without errors**

```bash
cd frontend && npm run dev
```

Expected: App loads at `localhost:5173` showing "Landing page coming in Task 3..." placeholder text. No console errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: add LANDING view to App state machine"
```

---

## Task 3: Create LandingPage.jsx

**Files:**
- Create: `frontend/src/components/LandingPage.jsx`

- [ ] **Step 1: Try 21st.dev MCP for hero section (optional enhancement)**

Use the `mcp__magic__21st_magic_component_builder` tool with this prompt:
> "Dark themed hero section for a legal document AI app called NyayaMitra. Large bilingual headline in Hindi (न्यायमित्र) and English. Amber accent color on zinc-950 dark background. Two CTA buttons side by side. React + Tailwind CSS."

If the generated component fits the zinc/amber design system, use it as the hero. Otherwise use the implementation in Step 2 which is the spec-compliant fallback.

- [ ] **Step 2: Create the full LandingPage component**

Create `frontend/src/components/LandingPage.jsx`:

```jsx
/**
 * LandingPage.jsx — View 1 (LANDING)
 *
 * Hero section + stats + how-it-works + doc type preview strip.
 *
 * Props:
 *   onGetStarted() — navigate to SELECT_DOC
 *   onDemoClick()  — pre-fill demo case and navigate to INPUT_CASE
 */

const DOC_PREVIEW = [
  { id: "fir", icon: "📋", title: "FIR", titleHi: "प्रथम सूचना रिपोर्ट", laws: "BNS 2023" },
  { id: "legal_notice", icon: "⚖️", title: "Legal Notice", titleHi: "कानूनी नोटिस", laws: "BNS 2023" },
  { id: "consumer_complaint", icon: "🛒", title: "Consumer Complaint", titleHi: "उपभोक्ता शिकायत", laws: "CPA 2019" },
  { id: "cheque_bounce", icon: "💰", title: "Cheque Bounce", titleHi: "चेक बाउंस नोटिस", laws: "NI Act §138" },
  { id: "tenant_eviction", icon: "🏠", title: "Eviction Notice", titleHi: "बेदखली नोटिस", laws: "TPA + DRCA" },
];

const STATS = [
  { number: "50M+", label: "Pending court cases in India", labelHi: "न्यायालय में लंबित मामले" },
  { number: "₹3k–15k", label: "Lawyer fees for basic documents", labelHi: "वकील की फीस" },
  { number: "₹0", label: "Cost with NyayaMitra", labelHi: "न्यायमित्र के साथ" },
];

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Describe your situation",
    titleHi: "अपनी स्थिति बताएं",
    desc: "In Hindi, English, or Hinglish — just like telling a friend",
  },
  {
    step: "2",
    title: "AI agents research & draft",
    titleHi: "AI एजेंट शोध करते हैं",
    desc: "5 agents collaborate using 1,423 real Indian law sections",
  },
  {
    step: "3",
    title: "Download & file",
    titleHi: "डाउनलोड और दाखिल करें",
    desc: "Print-ready bilingual PDF + step-by-step filing guide",
  },
];

export default function LandingPage({ onGetStarted, onDemoClick }) {
  return (
    <div className="space-y-20">
      {/* Hero */}
      <div className="flex flex-col items-center text-center py-12 sm:py-20 space-y-6">
        <div className="space-y-2">
          <h1 className="text-5xl sm:text-7xl font-bold text-amber-500 font-devanagari leading-tight">
            न्यायमित्र
          </h1>
          <p className="text-2xl sm:text-4xl font-bold text-zinc-100 tracking-tight">
            NyayaMitra
          </p>
        </div>

        <p className="text-base sm:text-lg text-zinc-300 max-w-xl leading-relaxed">
          AI-powered legal documents for every Indian — in Hindi, for free.
        </p>

        <p className="font-mono text-xs text-zinc-500">
          Powered by Llama 3.3 &bull; BNS 2023 &bull; ChromaDB &bull; 1,423 law sections indexed
        </p>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            onClick={onGetStarted}
            className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold px-8 py-3 rounded-xl transition-colors duration-200 text-base"
          >
            Get Started &#8594;
          </button>
          <button
            onClick={onDemoClick}
            className="border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 font-medium px-8 py-3 rounded-xl transition-colors duration-200 text-base"
          >
            &#9889; Try Demo
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {STATS.map((stat) => (
          <div
            key={stat.number}
            className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center space-y-1"
          >
            <p className="text-4xl font-bold text-amber-500">{stat.number}</p>
            <p className="text-sm text-zinc-300">{stat.label}</p>
            <p className="text-xs font-devanagari text-zinc-600">{stat.labelHi}</p>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div className="space-y-6">
        <div className="text-center space-y-1">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">How it works</p>
          <h2 className="text-xl font-semibold text-zinc-100">
            From description to print-ready document in 3 steps
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {HOW_IT_WORKS.map((item) => (
            <div
              key={item.step}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 space-y-3"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-zinc-950 font-bold text-sm">
                {item.step}
              </span>
              <div>
                <p className="font-semibold text-zinc-100">{item.title}</p>
                <p className="text-xs font-devanagari text-zinc-500 mt-0.5">{item.titleHi}</p>
              </div>
              <p className="text-sm text-zinc-500 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Document types preview strip */}
      <div className="space-y-4">
        <div className="text-center space-y-1">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
            Documents we generate
          </p>
          <h2 className="text-xl font-semibold text-zinc-100">5 document types covered</h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pointer-events-none select-none">
          {DOC_PREVIEW.map((doc) => (
            <div
              key={doc.id}
              className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center space-y-2 opacity-80"
            >
              <span className="text-3xl leading-none block">{doc.icon}</span>
              <div>
                <p className="text-xs font-semibold text-zinc-300">{doc.title}</p>
                <p className="text-xs font-devanagari text-zinc-600 mt-0.5">{doc.titleHi}</p>
              </div>
              <span className="inline-block rounded bg-zinc-800 border border-zinc-700 px-1.5 py-0.5 font-mono text-xs text-amber-400">
                {doc.laws}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom CTA repeat */}
      <div className="flex flex-col items-center gap-3 py-8 border-t border-zinc-800">
        <p className="text-zinc-400 text-sm">
          Ready to draft your document? It takes under 30 seconds.
        </p>
        <p className="font-devanagari text-zinc-600 text-xs">
          30 सेकंड में आपका दस्तावेज़ तैयार हो जाएगा
        </p>
        <button
          onClick={onGetStarted}
          className="mt-2 bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold px-8 py-3 rounded-xl transition-colors duration-200"
        >
          Get Started &#8594;
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire LandingPage into App.jsx temporarily to verify it renders**

In `frontend/src/App.jsx`, add the import and replace the LANDING placeholder:

```jsx
import LandingPage from "./components/LandingPage";

// inside the JSX return, replace the LANDING placeholder:
{view === VIEWS.LANDING && (
  <LandingPage onGetStarted={handleGetStarted} onDemoClick={handleDemoClick} />
)}
```

- [ ] **Step 4: Verify landing page renders**

```bash
cd frontend && npm run dev
```

Open `localhost:5173`. Expected:
- "न्यायमित्र" headline in amber
- "NyayaMitra" below it
- "Get Started →" and "Try Demo ⚡" buttons
- 3 stat cards (50M+, ₹3k–15k, ₹0)
- 3 how-it-works cards
- 5 doc type preview cards (non-clickable)
- "Get Started →" button navigates to the SELECT_DOC placeholder

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/LandingPage.jsx frontend/src/App.jsx
git commit -m "feat: add LandingPage component with hero, stats, and doc preview"
```

---

## Task 4: Revamp DocTypeSelector.jsx

**Files:**
- Modify: `frontend/src/components/DocTypeSelector.jsx`

- [ ] **Step 1: Replace DocTypeSelector with revamped version**

Replace the entire contents of `frontend/src/components/DocTypeSelector.jsx`:

```jsx
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
        {DOC_TYPES.map((doc) => {
          const isSelected = selected === doc.id;
          return (
            <button
              key={doc.id}
              onClick={() => handleSelect(doc.id)}
              className={[
                "flex flex-col gap-3 rounded-xl border p-5 text-left transition-all duration-200 cursor-pointer",
                isSelected
                  ? "border-amber-500 bg-zinc-800 ring-2 ring-amber-500/30 shadow-lg shadow-amber-500/10"
                  : "border-zinc-800 bg-zinc-900 hover:border-amber-500 hover:bg-zinc-800 hover:scale-[1.02] hover:shadow-lg hover:shadow-amber-500/10",
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
```

- [ ] **Step 2: Wire DocTypeSelector into App.jsx**

In `frontend/src/App.jsx`, add the import and replace the SELECT_DOC placeholder:

```jsx
import DocTypeSelector from "./components/DocTypeSelector";

// inside the JSX return:
{view === VIEWS.SELECT_DOC && (
  <DocTypeSelector
    onSelect={handleDocTypeSelect}
    onDemoClick={handleDemoClick}
    onBack={() => setView(VIEWS.LANDING)}
  />
)}
```

- [ ] **Step 3: Verify card grid renders and Back button works**

Open `localhost:5173`. Click "Get Started →". Expected:
- 5 doc type cards in grid
- "Step 1 of 3" label top-left
- "← Back" link top-right → returns to landing
- Hovering a card: amber border glow, slight scale-up
- Clicking a card: navigates to INPUT_CASE placeholder

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DocTypeSelector.jsx frontend/src/App.jsx
git commit -m "feat: revamp DocTypeSelector with richer cards and Back button"
```

---

## Task 5: Revamp CaseInput.jsx

**Files:**
- Modify: `frontend/src/components/CaseInput.jsx`

- [ ] **Step 1: Replace CaseInput with revamped version**

Replace the entire contents of `frontend/src/components/CaseInput.jsx`:

```jsx
/**
 * CaseInput.jsx — View 3 (INPUT_CASE)
 *
 * Step 2 of 3. User describes their case in Hindi/English/Hinglish.
 *
 * Props:
 *   docType     (string)      — selected document type key
 *   onSubmit    (description) — called when user submits
 *   onBack      ()            — return to SELECT_DOC
 *   isLoading   (bool)        — true while pipeline is starting
 *   initialText (string|null) — optional pre-filled text (demo flow)
 */

import { useState, useEffect } from "react";

const DOC_LABELS = {
  fir: { label: "FIR", icon: "📋" },
  legal_notice: { label: "Legal Notice", icon: "⚖️" },
  consumer_complaint: { label: "Consumer Complaint", icon: "🛒" },
  cheque_bounce: { label: "Cheque Bounce Notice", icon: "💰" },
  tenant_eviction: { label: "Tenant Eviction Notice", icon: "🏠" },
};

const DEMO_TEXTS = {
  tenant_eviction:
    "Mera naam Ramesh Kumar hai. Main Lajpat Nagar, Delhi mein kiraya par rehta tha. " +
    "Makaan malik ne bina kisi notice ke mujhe ghar se nikaalne ki koshish ki aur mere saamaan bahar rakh diye. " +
    "Maine 3 saal ka kiraya diya hai aur kabhi late nahi ki. " +
    "Ab wo keh raha hai ki ghar khaali karo kyunki uske bete ko chahiye. Mujhe apna haq chahiye.",
  cheque_bounce:
    "Maine apne dost Suresh ko Rs. 50,000 diye the aur unhone mujhe 15 March 2024 ka cheque diya tha HDFC bank ka. " +
    "Jab maine cheque bank mein lagaya to bounce ho gaya - 'insufficient funds' ka reason tha. " +
    "Bank ka memo 20 March ko mila. Ab Suresh phone nahi uthata.",
  fir:
    "Kal raat mere ghar mein chori ho gayi. Ghar ke peeche ki khidki todi aur andar ghus ke TV, laptop aur " +
    "Rs 20,000 cash le gaye. Neighbours ne ek banda dekha tha. CCTV footage bhi hai.",
  consumer_complaint:
    "Maine Samsung se Rs 45,000 mein ek refrigerator kharida tha 3 mahine pehle. " +
    "Pichhle 1 mahine se cooling nahi ho rahi. Service center ne 5 baar aake fix kiya par theek nahi hua. " +
    "Ab wo keh rahe hain warranty mein cover nahi hoga.",
  legal_notice:
    "Mere employer ne 3 mahine ki salary nahi di - total Rs 90,000 baaki hai. " +
    "Resign karne ke baad bhi full and final settlement nahi kiya. HR ko emails kiye par koi jawab nahi.",
};

export default function CaseInput({
  docType,
  onSubmit,
  onBack,
  isLoading = false,
  initialText = null,
}) {
  const [text, setText] = useState(initialText ?? "");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialText) setText(initialText);
  }, [initialText]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim() || isSubmitting || isLoading) return;
    setIsSubmitting(true);
    await onSubmit(text.trim());
  }

  function handleDemoFill() {
    const demo = DEMO_TEXTS[docType];
    if (demo) setText(demo);
  }

  const docMeta = DOC_LABELS[docType] ?? { label: docType, icon: "📄" };
  const canSubmit = text.trim().length > 0 && !isSubmitting && !isLoading;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Heading row */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">Step 2 of 3</p>
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 transition-colors duration-200"
          >
            &#8592; Change type
          </button>
        </div>
        <h2 className="text-2xl font-semibold text-zinc-100">Describe your situation</h2>
        <p className="text-zinc-400 text-sm">
          अपनी बात हिंदी या English में लिखें — जैसे किसी दोस्त को बताते हैं
        </p>
      </div>

      {/* Selected doc type badge */}
      <div className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3">
        <span className="text-2xl">{docMeta.icon}</span>
        <div>
          <p className="font-semibold text-amber-400">{docMeta.label}</p>
          <p className="text-xs text-zinc-500">Selected document type</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Apna case describe karein... (Hindi ya English mein likha ja sakta hai)"
            className="font-devanagari h-52 w-full resize-none rounded-xl border border-zinc-700 bg-zinc-800 p-4 text-zinc-100 placeholder-zinc-500 transition-colors duration-200 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
            disabled={isSubmitting || isLoading}
          />
          <span className="absolute bottom-3 right-4 font-mono text-xs text-zinc-500 pointer-events-none">
            {text.length} chars
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={!canSubmit}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-3 font-bold text-zinc-950 transition-all duration-200 hover:from-amber-400 hover:to-orange-400 disabled:cursor-not-allowed disabled:opacity-40 w-full sm:w-auto justify-center"
          >
            {isSubmitting || isLoading ? (
              <>
                <svg
                  className="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
                Starting pipeline...
              </>
            ) : (
              <>Generate Document &#8594;</>
            )}
          </button>

          {DEMO_TEXTS[docType] && (
            <button
              type="button"
              onClick={handleDemoFill}
              disabled={isSubmitting || isLoading}
              className="rounded-lg border border-zinc-700 px-4 py-2.5 text-sm text-zinc-300 transition-colors duration-200 hover:border-zinc-500 hover:text-zinc-100 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Try example &#9889;
            </button>
          )}
        </div>

        <p className="text-xs text-zinc-600">
          Minimum 20 characters recommended for best results. Your data is not stored permanently.
        </p>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Wire CaseInput into App.jsx**

In `frontend/src/App.jsx`, add the import and replace the INPUT_CASE placeholder:

```jsx
import CaseInput from "./components/CaseInput";

// inside the JSX return:
{view === VIEWS.INPUT_CASE && (
  <CaseInput
    docType={selectedDoc}
    onSubmit={handleCaseSubmit}
    onBack={() => setView(VIEWS.SELECT_DOC)}
    isLoading={isLoading}
    initialText={demoText}
  />
)}
```

- [ ] **Step 3: Verify input view renders**

Open `localhost:5173`. Click "Get Started →" → select any doc type. Expected:
- "Step 2 of 3" label
- Amber doc type badge with icon
- Large textarea with amber focus ring
- "Generate Document →" button (disabled when empty)
- "Try example ⚡" fills the textarea with demo text
- "← Change type" returns to SELECT_DOC

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/CaseInput.jsx frontend/src/App.jsx
git commit -m "feat: revamp CaseInput with prominent doc badge and larger textarea"
```

---

## Task 6: Update AgentPipeline.jsx — add 5th agent + animated connectors

**Files:**
- Modify: `frontend/src/components/AgentPipeline.jsx`

- [ ] **Step 1: Replace AgentPipeline with updated version**

Replace the entire contents of `frontend/src/components/AgentPipeline.jsx`:

```jsx
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
      <div className={`${base} animate-pulse bg-amber-500 text-zinc-950`}>
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
```

- [ ] **Step 2: Verify no regressions in existing pipeline view**

```bash
cd frontend && npm run dev
```

Navigate past the placeholder PROCESSING view — the AgentPipeline component will be used there in Task 7. For now just confirm the app still compiles without errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AgentPipeline.jsx
git commit -m "feat: add filing_assistant as 5th agent, animate connector lines on completion"
```

---

## Task 7: Create ProcessingPage.jsx

**Files:**
- Create: `frontend/src/components/ProcessingPage.jsx`

- [ ] **Step 1: Create ProcessingPage component**

Create `frontend/src/components/ProcessingPage.jsx`:

```jsx
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
```

- [ ] **Step 2: Wire ProcessingPage into App.jsx**

In `frontend/src/App.jsx`, add the import and replace the PROCESSING placeholder:

```jsx
import ProcessingPage from "./components/ProcessingPage";

// inside the JSX return:
{view === VIEWS.PROCESSING && (
  <ProcessingPage
    agentStatuses={agentStatuses}
    events={events}
    sseError={sseError}
  />
)}
```

Also add the pipeline error display in INPUT_CASE. After the `{view === VIEWS.INPUT_CASE && ...}` block, add:

```jsx
{view === VIEWS.INPUT_CASE && pipelineError && (
  <div className="max-w-3xl mx-auto mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
    <span className="font-bold">Error: </span>{pipelineError}
  </div>
)}
```

- [ ] **Step 3: Verify processing page compiles**

```bash
cd frontend && npm run dev
```

Navigate to the input step, fill in text and click "Generate Document →". Expected:
- If backend is not running: error message shown on INPUT_CASE view
- If backend is running: PROCESSING view appears with animated pipeline steps

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ProcessingPage.jsx frontend/src/App.jsx
git commit -m "feat: add ProcessingPage with animated pipeline and error display"
```

---

## Task 8: Create ResultsPage.jsx

**Files:**
- Create: `frontend/src/components/ResultsPage.jsx`

- [ ] **Step 1: Create ResultsPage component**

Create `frontend/src/components/ResultsPage.jsx`:

```jsx
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
```

- [ ] **Step 2: Wire ResultsPage into App.jsx — final complete App.jsx**

Replace the entire `frontend/src/App.jsx` with the final wired version:

```jsx
/**
 * App.jsx — Root component and 5-view state machine
 *
 * Views:
 *   LANDING      — Hero, stats, doc preview strip
 *   SELECT_DOC   — Pick document type (Step 1 of 3)
 *   INPUT_CASE   — Describe situation (Step 2 of 3)
 *   PROCESSING   — Live agent pipeline via SSE
 *   VIEW_RESULTS — Draft, verifier, filing guide, PDF download
 */

import { useState, useEffect } from "react";
import LandingPage from "./components/LandingPage";
import DocTypeSelector from "./components/DocTypeSelector";
import CaseInput from "./components/CaseInput";
import ProcessingPage from "./components/ProcessingPage";
import ResultsPage from "./components/ResultsPage";
import { useSSE } from "./hooks/useSSE";
import { startPipeline, generateSessionId } from "./lib/api";

const VIEWS = {
  LANDING: "LANDING",
  SELECT_DOC: "SELECT_DOC",
  INPUT_CASE: "INPUT_CASE",
  PROCESSING: "PROCESSING",
  VIEW_RESULTS: "VIEW_RESULTS",
};

const DEMO_DOC_TYPE = "tenant_eviction";
const DEMO_DESCRIPTION =
  "Mera naam Ramesh Kumar hai. Main Lajpat Nagar, Delhi mein kiraya par rehta tha. " +
  "Makaan malik ne bina kisi notice ke mujhe ghar se nikaalne ki koshish ki aur mere saamaan bahar rakh diye. " +
  "Maine 3 saal ka kiraya diya hai aur kabhi late nahi ki. " +
  "Ab wo keh raha hai ki ghar khaali karo kyunki uske bete ko chahiye. Mujhe apna haq chahiye.";

export default function App() {
  const [view, setView] = useState(VIEWS.LANDING);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [pipelineStarted, setPipelineStarted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [pipelineError, setPipelineError] = useState(null);
  const [demoText, setDemoText] = useState(null);

  const {
    events,
    agentStatuses,
    isComplete,
    error: sseError,
    draft,
    verification,
    filingData,
  } = useSSE(pipelineStarted ? sessionId : null);

  useEffect(() => {
    if (isComplete && view === VIEWS.PROCESSING) {
      setView(VIEWS.VIEW_RESULTS);
    }
  }, [isComplete, view]);

  async function handleCaseSubmit(description) {
    const sid = generateSessionId();
    setSessionId(sid);
    setPipelineError(null);
    setIsLoading(true);

    try {
      await startPipeline(selectedDoc, description, sid);
      setPipelineStarted(true);
      setView(VIEWS.PROCESSING);
    } catch (err) {
      setPipelineError(err.message ?? "Failed to start pipeline. Is the backend running?");
      setIsLoading(false);
    }
  }

  function handleGetStarted() {
    setView(VIEWS.SELECT_DOC);
  }

  function handleDocTypeSelect(type) {
    setSelectedDoc(type);
    setDemoText(null);
    setView(VIEWS.INPUT_CASE);
  }

  function handleDemoClick() {
    setSelectedDoc(DEMO_DOC_TYPE);
    setDemoText(DEMO_DESCRIPTION);
    setView(VIEWS.INPUT_CASE);
  }

  function handleReset() {
    setView(VIEWS.LANDING);
    setSelectedDoc(null);
    setSessionId(null);
    setPipelineStarted(false);
    setIsLoading(false);
    setPipelineError(null);
    setDemoText(null);
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <header className="border-b border-zinc-800 px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <button
            onClick={handleReset}
            className="text-left transition-opacity duration-200 hover:opacity-75"
          >
            <div className="flex items-center gap-2">
              <span className="text-xl">&#9878;</span>
              <div>
                <span className="font-bold text-amber-500 text-lg leading-none">NyayaMitra</span>
                <p className="font-mono text-xs text-zinc-500 leading-none mt-0.5">
                  AI Legal Document Assistant &bull; न्यायमित्र
                </p>
              </div>
            </div>
          </button>
          <span className="hidden sm:block font-mono text-xs text-zinc-600">
            Powered by Llama 3.3 &bull; भारत
          </span>
        </div>
      </header>

      {/* Main content — key={view} triggers animate-fade-in on every view change */}
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <div key={view} className="animate-fade-in">
          {view === VIEWS.LANDING && (
            <LandingPage onGetStarted={handleGetStarted} onDemoClick={handleDemoClick} />
          )}

          {view === VIEWS.SELECT_DOC && (
            <DocTypeSelector
              onSelect={handleDocTypeSelect}
              onDemoClick={handleDemoClick}
              onBack={() => setView(VIEWS.LANDING)}
            />
          )}

          {view === VIEWS.INPUT_CASE && (
            <div className="space-y-4">
              <CaseInput
                docType={selectedDoc}
                onSubmit={handleCaseSubmit}
                onBack={() => setView(VIEWS.SELECT_DOC)}
                isLoading={isLoading}
                initialText={demoText}
              />
              {pipelineError && (
                <div className="max-w-3xl mx-auto rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
                  <span className="font-bold">Error: </span>{pipelineError}
                </div>
              )}
            </div>
          )}

          {view === VIEWS.PROCESSING && (
            <ProcessingPage
              agentStatuses={agentStatuses}
              events={events}
              sseError={sseError}
            />
          )}

          {view === VIEWS.VIEW_RESULTS && (
            <ResultsPage
              agentStatuses={agentStatuses}
              events={events}
              draft={draft}
              verification={verification}
              filingData={filingData}
              sessionId={sessionId}
              isComplete={isComplete}
              onReset={handleReset}
            />
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800 px-4 py-6 mt-12 text-center">
        <p className="font-mono text-xs text-zinc-600">
          NyayaMitra &bull; Not a substitute for professional legal advice &bull; कानूनी सलाह के लिए वकील से मिलें
        </p>
      </footer>
    </div>
  );
}
```

- [ ] **Step 3: Verify full navigation flow works**

```bash
cd frontend && npm run dev
```

Walk the full flow manually:
1. Landing page loads at `localhost:5173` — hero, stats, 3 steps, 5 doc cards visible
2. "Get Started →" → SELECT_DOC with 5 cards
3. "← Back" → returns to landing with fade-in animation
4. Select "FIR" → INPUT_CASE with amber FIR badge
5. "← Change type" → returns to SELECT_DOC
6. Fill demo text → "Generate Document →" → PROCESSING view (with backend) or error (without backend)
7. "← NyayaMitra" logo → resets to LANDING

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResultsPage.jsx frontend/src/App.jsx
git commit -m "feat: add ResultsPage and complete 5-view App state machine wiring"
```

---

## Task 9: Playwright MCP End-to-End Verification

**Files:**
- No file changes — verification only

- [ ] **Step 1: Start the frontend dev server**

```bash
cd frontend && npm run dev
```

Confirm it runs at `localhost:5173`.

- [ ] **Step 2: Run Playwright verification via MCP**

Use the Playwright MCP tool to execute the following test sequence. Run each step and assert the result before proceeding:

**Test 1 — Landing page loads:**
- Navigate to `http://localhost:5173`
- Assert: text "NyayaMitra" is visible
- Assert: text "Get Started" button is visible
- Assert: text "50M+" is visible (stats card)

**Test 2 — Navigation to SELECT_DOC:**
- Click "Get Started" button
- Assert: text "Step 1 of 3" is visible
- Assert: text "FIR" card is visible (5 cards rendered)

**Test 3 — Back navigation works:**
- Click "Back" link
- Assert: text "NyayaMitra" hero headline visible (back on landing)

**Test 4 — Doc type selection leads to INPUT_CASE:**
- Click "Get Started"
- Click the "FIR" card
- Assert: text "Step 2 of 3" is visible
- Assert: textarea element is present
- Assert: text "FIR" is visible in the amber badge

**Test 5 — Demo fill works:**
- Click "Try example" button
- Assert: textarea value contains "Kal raat mere ghar mein" (FIR demo text)

**Test 6 — Change type navigation:**
- Click "Change type" link
- Assert: text "Step 1 of 3" is visible (back on SELECT_DOC)

**Test 7 — Demo flow from landing:**
- Navigate to `http://localhost:5173`
- Click "Try Demo" button
- Assert: text "Step 2 of 3" is visible
- Assert: textarea value contains "Mera naam Ramesh Kumar" (tenant eviction demo)

**Test 8 — Logo resets to landing:**
- Click "NyayaMitra" logo in header
- Assert: text "Get Started" CTA button visible (back on landing)

**Test 9 — Pipeline + results (requires backend):**
- If backend is running at `localhost:8000`:
  - Navigate to `localhost:5173`, click "Get Started", select "FIR", fill demo text, click "Generate Document →"
  - Assert: "Processing Your Case" heading visible (PROCESSING view)
  - Wait for pipeline to complete (up to 60 seconds)
  - Assert: "Your document is ready" heading visible (VIEW_RESULTS)
  - Assert: "Document Preview" section visible
  - Assert: "Download PDF" button visible and not disabled
- If backend is NOT running:
  - Assert: error message appears on INPUT_CASE view after submit attempt

- [ ] **Step 3: Fix any failures found by Playwright**

If any assertion fails:
- Check the browser console for errors
- Check that component prop names match exactly (e.g. `onBack` vs `onBack()`)
- Check that view names in VIEWS constant match the conditions in App.jsx JSX

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete NyayaMitra frontend revamp — 5-view SPA with landing page, polished components, and animated pipeline"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] LANDING view with hero, stats, how-it-works, doc strip → Task 3
- [x] SELECT_DOC revamp with richer cards, hover glow, onBack → Task 4
- [x] INPUT_CASE revamp with step indicator, amber badge, larger textarea → Task 5
- [x] AgentPipeline 5th agent + animated connectors → Task 6
- [x] PROCESSING full-screen view → Task 7
- [x] VIEW_RESULTS stacked layout → Task 8
- [x] App.jsx complete wiring, view transitions with animate-fade-in → Tasks 2 + 8
- [x] window.scrollTo(0,0) — NOTE: not yet added. Add to handleReset and each navigation handler in App.jsx Task 8, Step 2. In `handleGetStarted`, `handleDocTypeSelect`, `handleDemoClick`, `handleReset`, and `handleCaseSubmit` (after setView), add `window.scrollTo(0, 0);`
- [x] 21st.dev MCP note in Task 3
- [x] Playwright MCP verification → Task 9
- [x] FilingAssistant, PDFDownload, DraftPreview, VerifierFlags, useSSE, api.js — all untouched

**Scroll-to-top fix (discovered in self-review):** In Task 8, Step 2, inside `App.jsx`, add `window.scrollTo(0, 0)` to all five navigation handlers: `handleGetStarted`, `handleDocTypeSelect`, `handleDemoClick`, `handleReset`, and after `setView(VIEWS.PROCESSING)` in `handleCaseSubmit`. The final App.jsx already shows the handlers — add `window.scrollTo(0, 0)` as the last line of each `setView(...)` call.
