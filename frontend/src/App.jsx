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
import AppBackground from "./components/AppBackground";
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

  // Transition to VIEW_RESULTS when SSE signals completion
  useEffect(() => {
    if (isComplete && view === VIEWS.PROCESSING) {
      window.scrollTo(0, 0);
      setView(VIEWS.VIEW_RESULTS);
    }
  }, [isComplete, view]);

  async function handleCaseSubmit(description, extractedData) {
    /* sessionId is pre-generated on SELECT_DOC so CaseInput can use it for /api/chat/intake */
    const sid = sessionId ?? generateSessionId();
    setSessionId(sid);
    setPipelineError(null);
    setIsLoading(true);

    try {
      await startPipeline(selectedDoc, description || "case details collected via chat", sid, extractedData);
      setPipelineStarted(true);
      window.scrollTo(0, 0);
      setView(VIEWS.PROCESSING);
    } catch (err) {
      setPipelineError(err.message ?? "Failed to start pipeline. Is the backend running?");
      setIsLoading(false);
    }
  }

  function handleGetStarted() {
    window.scrollTo(0, 0);
    setView(VIEWS.SELECT_DOC);
  }

  function handleDocTypeSelect(type) {
    setSelectedDoc(type);
    setSessionId(generateSessionId());
    setDemoText(null);
    window.scrollTo(0, 0);
    setView(VIEWS.INPUT_CASE);
  }

  function handleDemoClick() {
    setSelectedDoc(DEMO_DOC_TYPE);
    setSessionId(generateSessionId());
    setDemoText(DEMO_DESCRIPTION);
    window.scrollTo(0, 0);
    setView(VIEWS.INPUT_CASE);
  }

  function handleReset() {
    window.scrollTo(0, 0);
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
      <AppBackground />
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
              onBack={() => { window.scrollTo(0, 0); setView(VIEWS.LANDING); }}
            />
          )}

          {view === VIEWS.INPUT_CASE && (
            <div className="space-y-4">
              <CaseInput
                docType={selectedDoc}
                sessionId={sessionId}
                onSubmit={handleCaseSubmit}
                onBack={() => { window.scrollTo(0, 0); setView(VIEWS.SELECT_DOC); }}
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
