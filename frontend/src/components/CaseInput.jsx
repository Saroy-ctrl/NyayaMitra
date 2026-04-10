/**
 * CaseInput.jsx — View 3 (INPUT_CASE)
 *
 * Multi-turn conversational intake chatbox.
 * The NyayaMitra intake agent asks clarifying questions until
 * it has enough information to draft the document.
 *
 * Props:
 *   docType    (string)   — selected document type key
 *   sessionId  (string)   — session UUID for this intake conversation
 *   onSubmit   (description, extractedData) — called when intake is complete
 *   onBack     ()         — return to SELECT_DOC
 *   isLoading  (bool)     — true while pipeline is starting (post-submit)
 *   initialText (string|null) — optional pre-filled first message (demo flow)
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { ArrowRight, Loader, Zap, RotateCcw, Mic, MicOff } from "lucide-react";
import { chatWithIntake } from "../lib/api";

/* ─────────────────────────────────────────────────────────────── */
/*  Static data                                                    */
/* ─────────────────────────────────────────────────────────────── */

const DOC_LABELS = {
  fir:                { label: "FIR",                    icon: "📋" },
  legal_notice:       { label: "Legal Notice",           icon: "⚖️" },
  consumer_complaint: { label: "Consumer Complaint",     icon: "🛒" },
  cheque_bounce:      { label: "Cheque Bounce Notice",   icon: "💰" },
  tenant_eviction:    { label: "Tenant Eviction Notice", icon: "🏠" },
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

const WELCOME_EN =
  "Namaste! I'm NyayaMitra. Please describe your situation — what happened, when, where, and who was involved? You can reply in Hindi or English.";
const WELCOME_HI =
  "नमस्ते! मैं न्यायमित्र हूँ। कृपया अपनी स्थिति बताइए — क्या हुआ, कब हुआ, कहाँ हुआ, और कौन शामिल था? आप हिंदी या English में जवाब दे सकते हैं।";

function WelcomeMessage({ lang, onLangChange }) {
  return (
    <div className="rounded-lg p-3 mb-2 bg-amber-950/60 border border-amber-800/40 text-amber-100 text-sm max-w-[80%]">
      <div className="text-xs font-mono text-amber-500 mb-1 uppercase tracking-widest">NyayaMitra</div>
      <p>{lang === "en" ? WELCOME_EN : WELCOME_HI}</p>
      <div className="mt-2 flex gap-2">
        <button
          onClick={() => onLangChange("en")}
          className={`text-xs px-2 py-0.5 rounded border ${lang === "en" ? "border-amber-500 text-amber-300 bg-amber-900/40" : "border-zinc-600 text-zinc-400"}`}
        >English</button>
        <button
          onClick={() => onLangChange("hi")}
          className={`text-xs px-2 py-0.5 rounded border ${lang === "hi" ? "border-amber-500 text-amber-300 bg-amber-900/40" : "border-zinc-600 text-zinc-400"}`}
        >हिंदी</button>
      </div>
    </div>
  );
}

const WELCOME_MESSAGE = {
  role: "agent",
  content: WELCOME_EN,
  isWelcome: true,
};

/* ─────────────────────────────────────────────────────────────── */
/*  Typing indicator                                               */
/* ─────────────────────────────────────────────────────────────── */

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="inline-block w-2 h-2 rounded-full bg-amber-500 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────── */
/*  Individual message bubble                                      */
/* ─────────────────────────────────────────────────────────────── */

function MessageBubble({ message, lang, onLangChange }) {
  const isAgent = message.role === "agent";
  if (message.isWelcome) return <WelcomeMessage lang={lang} onLangChange={onLangChange} />;
  return (
    <div className={`flex flex-col mb-3 ${isAgent ? "items-start" : "items-end"}`}>
      {isAgent && (
        <span className="font-mono text-xs uppercase tracking-widest text-amber-600 mb-1 ml-1">
          NyayaMitra
        </span>
      )}
      <div
        className={[
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isAgent
            ? "bg-amber-950/60 border border-amber-800/40 text-amber-100 rounded-tl-sm"
            : "bg-zinc-700 text-zinc-100 rounded-tr-sm",
        ].join(" ")}
      >
        {message.content}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────── */
/*  Component                                                      */
/* ─────────────────────────────────────────────────────────────── */

export default function CaseInput({
  docType,
  sessionId,
  onSubmit,
  onBack,
  isLoading = false,
  initialText = null,
}) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState(null);
  const [lang, setLang] = useState("en");

  const [isListening, setIsListening] = useState(false);
  const [micError, setMicError] = useState(null);
  const recognitionRef = useRef(null);
  const micErrorTimerRef = useRef(null);

  /* Detect Web Speech API support once */
  const speechSupported =
    typeof window !== "undefined" &&
    Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);

  function startListening() {
    if (!speechSupported || isListening) return;
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = lang === "hi" ? "hi-IN" : "en-US";

    recognition.onresult = (e) => {
      const transcript = e.results[0]?.[0]?.transcript ?? "";
      if (transcript) {
        setInputText((prev) => (prev ? prev + " " + transcript : transcript));
      }
    };

    recognition.onerror = (e) => {
      setIsListening(false);
      if (e.error === "not-allowed" || e.error === "permission-denied") {
        setMicError("Microphone permission denied.");
      } else if (e.error !== "no-speech" && e.error !== "aborted") {
        setMicError("Speech recognition error. Please retry.");
      }
      clearTimeout(micErrorTimerRef.current);
      micErrorTimerRef.current = setTimeout(() => setMicError(null), 3000);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
      setIsListening(true);
      setMicError(null);
    } catch {
      setIsListening(false);
    }
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setIsListening(false);
  }

  function toggleMic() {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }

  /* Clean up recognition on unmount */
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      clearTimeout(micErrorTimerRef.current);
    };
  }, []);

  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const lastUserMessageRef = useRef(null);

  /* Auto-scroll to bottom on new messages */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  /* Auto-send demo text as first user message */
  useEffect(() => {
    if (initialText && messages.length === 1) {
      setInputText(initialText);
    }
  }, [initialText]);

  const sendMessage = useCallback(
    async (text) => {
      const userMsg = { role: "user", content: text };
      const updatedMessages = [...messages, userMsg];
      setMessages(updatedMessages);
      setInputText("");
      setError(null);
      setIsTyping(true);
      lastUserMessageRef.current = text;

      try {
        const result = await chatWithIntake(docType, sessionId, updatedMessages, lang);
        const agentMsg = { role: "agent", content: result.agent_reply };
        setMessages((prev) => [...prev, agentMsg]);

        if (result.extracted_data) {
          setExtractedData(result.extracted_data);
        }

        if (result.is_complete) {
          setIsComplete(true);
        }
      } catch (err) {
        setError(err.message ?? "Something went wrong. Please retry.");
      } finally {
        setIsTyping(false);
      }
    },
    [messages, docType, sessionId]
  );

  function handleSend() {
    const trimmed = inputText.trim();
    if (!trimmed || isTyping || isLoading) return;
    sendMessage(trimmed);
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleRetry() {
    if (lastUserMessageRef.current) {
      setError(null);
      /* Remove last user message from display before resending */
      setMessages((prev) => {
        const idx = [...prev].reverse().findIndex((m) => m.role === "user");
        if (idx === -1) return prev;
        const realIdx = prev.length - 1 - idx;
        return prev.slice(0, realIdx);
      });
      sendMessage(lastUserMessageRef.current);
    }
  }

  function handleForceProceed() {
    setIsComplete(true);
  }

  function handleProceed() {
    /* Build a plain-text description from all user messages for backward compat */
    const description = messages
      .filter((m) => m.role === "user")
      .map((m) => m.content)
      .join(" ");
    onSubmit(description, extractedData ?? {});
  }

  const docMeta = DOC_LABELS[docType] ?? { label: docType, icon: "📄" };
  const hasDemo = Boolean(DEMO_TEXTS[docType]);
  const canSend = inputText.trim().length > 0 && !isTyping && !isLoading && !isComplete;

  return (
    <div className="max-w-3xl mx-auto space-y-6">

      {/* ── Heading row ───────────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
            Step 2 of 3
          </p>
          <button
            type="button"
            onClick={onBack}
            className="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 transition-colors duration-200"
          >
            &#8592; Change type
          </button>
        </div>
        <h2 className="text-2xl font-semibold text-zinc-100">
          Describe your situation
        </h2>
        <p className="text-zinc-400 text-sm">
          अपनी बात हिंदी या English में लिखें — जैसे किसी दोस्त को बताते हैं
        </p>
      </div>

      {/* ── Doc type badge ─────────────────────────────────────────── */}
      <div className="flex items-center gap-3 overflow-hidden rounded-xl border border-amber-600/40 bg-zinc-900">
        <div className="w-1 self-stretch bg-gradient-to-b from-amber-500 to-orange-500 rounded-l-xl flex-shrink-0" />
        <div className="flex items-center gap-3 px-3 py-3">
          <span className="text-2xl leading-none">{docMeta.icon}</span>
          <div>
            <p className="font-semibold text-amber-400">{docMeta.label}</p>
            <p className="text-xs text-zinc-500">Selected document type</p>
          </div>
        </div>
      </div>

      {/* ── Chat card ─────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-zinc-700 bg-zinc-900 shadow-2xl shadow-black/40 overflow-hidden">

        {/* Scrollable chat history */}
        <div className="max-h-96 overflow-y-auto px-4 pt-4 pb-2 space-y-1">
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} lang={lang} onLangChange={setLang} />
          ))}

          {isTyping && (
            <div className="flex flex-col items-start mb-3">
              <span className="font-mono text-xs uppercase tracking-widest text-amber-600 mb-1 ml-1">
                NyayaMitra
              </span>
              <div className="bg-amber-950/60 border border-amber-800/40 rounded-2xl rounded-tl-sm">
                <TypingIndicator />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Mic permission error banner */}
        {micError && (
          <div className="mx-4 mb-2 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
            <MicOff className="h-3.5 w-3.5 flex-shrink-0" />
            <span>{micError}</span>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mx-4 mb-2 flex items-center justify-between rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
            <span>{error}</span>
            <button
              type="button"
              onClick={handleRetry}
              className="flex items-center gap-1.5 ml-3 text-red-300 hover:text-red-100 transition-colors duration-200 font-medium"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Retry
            </button>
          </div>
        )}

        {/* Input area or Proceed button */}
        {isComplete ? (
          <div className="border-t border-zinc-800 px-4 py-4 flex flex-col items-center gap-2">
            <p className="text-sm text-emerald-400 font-medium">
              Information collected. Ready to generate your document.
            </p>
            <button
              type="button"
              onClick={handleProceed}
              disabled={isLoading}
              className="flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold bg-gradient-to-r from-amber-500 to-orange-500 text-zinc-950 transition-colors duration-200 hover:from-amber-400 hover:to-orange-400 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  Starting pipeline...
                </>
              ) : (
                <>
                  <ArrowRight className="h-4 w-4" />
                  Proceed to Drafting
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="border-t border-zinc-800">
            <div className="px-4 pt-3 pb-1">
              <textarea
                ref={textareaRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your reply... (Hindi ya English dono chalega)"
                disabled={isTyping || isLoading}
                rows={3}
                className="w-full resize-none bg-transparent text-zinc-100 placeholder-zinc-500 text-sm leading-relaxed focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>

            <div className="flex items-center justify-between border-t border-zinc-800/60 px-3 py-2">
              {/* Left: demo fill */}
              <div className="flex items-center gap-3">
                {hasDemo && messages.length === 1 && (
                  <button
                    type="button"
                    onClick={() => setInputText(DEMO_TEXTS[docType])}
                    disabled={isTyping || isLoading}
                    className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs text-zinc-400 hover:text-amber-400 transition-colors duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <Zap className="h-3.5 w-3.5" />
                    Try example
                  </button>
                )}
                <button
                  type="button"
                  onClick={handleForceProceed}
                  disabled={isTyping || isLoading}
                  className="text-xs text-zinc-600 hover:text-zinc-400 transition-colors duration-200 disabled:opacity-40"
                >
                  Skip / Force Proceed
                </button>
              </div>

              {/* Right: mic + send */}
              <div className="flex items-center gap-2">
                {speechSupported && (
                  <button
                    type="button"
                    onClick={toggleMic}
                    disabled={isTyping || isLoading || isComplete}
                    title={isListening ? "Stop recording" : "Speak your message"}
                    className={[
                      "relative flex items-center justify-center rounded-xl p-2 transition-colors duration-200 disabled:opacity-40 disabled:cursor-not-allowed",
                      isListening
                        ? "border border-amber-500 bg-amber-500/10 text-amber-400 amberGlow"
                        : "border border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-amber-600/50 hover:text-amber-400",
                    ].join(" ")}
                  >
                    {isListening ? (
                      <>
                        <Mic className="h-4 w-4 animate-pulse" />
                        <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-red-500" />
                      </>
                    ) : (
                      <Mic className="h-4 w-4" />
                    )}
                  </button>
                )}

              {/* Send button */}
              <button
                type="button"
                onClick={handleSend}
                disabled={!canSend}
                className={[
                  "flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors duration-200",
                  canSend
                    ? "bg-gradient-to-r from-amber-500 to-orange-500 text-zinc-950 cursor-pointer hover:from-amber-400 hover:to-orange-400"
                    : "bg-zinc-800 text-zinc-600 cursor-not-allowed",
                ].join(" ")}
              >
                <ArrowRight className="h-4 w-4" />
                Send
              </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-zinc-600">
        Press Enter to send, Shift+Enter for new line. Your data is not stored permanently.
      </p>
    </div>
  );
}
