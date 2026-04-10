/**
 * CaseInput.jsx — View 3 (INPUT_CASE)
 *
 * Step 2 of 3. User describes their case in Hindi/English/Hinglish.
 * Animated chat-input card inspired by 21st.dev AnimatedAIChat,
 * reskinned for NyayaMitra's amber/zinc dark palette.
 *
 * Props:
 *   docType     (string)      — selected document type key
 *   onSubmit    (description) — called when user submits
 *   onBack      ()            — return to SELECT_DOC
 *   isLoading   (bool)        — true while pipeline is starting
 *   initialText (string|null) — optional pre-filled text (demo flow)
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, ArrowRight, Loader } from "lucide-react";

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

/* ─────────────────────────────────────────────────────────────── */
/*  Auto-resize hook                                               */
/* ─────────────────────────────────────────────────────────────── */

function useAutoResizeTextarea({ minHeight, maxHeight }) {
  const textareaRef = useRef(null);

  const adjustHeight = useCallback(
    (reset) => {
      const el = textareaRef.current;
      if (!el) return;
      el.style.height = `${minHeight}px`;
      if (!reset) {
        const newH = Math.max(
          minHeight,
          Math.min(el.scrollHeight, maxHeight ?? Infinity)
        );
        el.style.height = `${newH}px`;
      }
    },
    [minHeight, maxHeight]
  );

  return { textareaRef, adjustHeight };
}

/* ─────────────────────────────────────────────────────────────── */
/*  Component                                                      */
/* ─────────────────────────────────────────────────────────────── */

export default function CaseInput({
  docType,
  onSubmit,
  onBack,
  isLoading = false,
  initialText = null,
}) {
  const [text, setText] = useState(initialText ?? "");
  const [isFocused, setIsFocused] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 80,
    maxHeight: 200,
  });

  /* Sync initialText prop (demo flow) */
  useEffect(() => {
    if (initialText) {
      setText(initialText);
      adjustHeight();
    }
  }, [initialText, adjustHeight]);

  /* Adjust height whenever text changes */
  useEffect(() => {
    adjustHeight();
  }, [text, adjustHeight]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!text.trim() || isSubmitting || isLoading) return;
    setIsSubmitting(true);
    await onSubmit(text.trim());
  }

  function handleDemoFill() {
    const demo = DEMO_TEXTS[docType];
    if (demo) {
      setText(demo);
      textareaRef.current?.focus();
    }
  }

  const docMeta  = DOC_LABELS[docType] ?? { label: docType, icon: "📄" };
  const hasText  = text.trim().length > 0;
  const canSubmit = hasText && !isSubmitting && !isLoading;
  const busy     = isSubmitting || isLoading;
  const hasDemo  = Boolean(DEMO_TEXTS[docType]);

  return (
    <div className="max-w-3xl mx-auto space-y-8">

      {/* ── Heading row ────────────────────────────────────────── */}
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

      {/* ── Doc type badge ──────────────────────────────────────── */}
      <div className="flex items-center gap-3 overflow-hidden rounded-xl border border-amber-600/40 bg-zinc-900">
        {/* Left amber accent bar */}
        <div className="w-1 self-stretch bg-gradient-to-b from-amber-500 to-orange-500 rounded-l-xl flex-shrink-0" />
        <div className="flex items-center gap-3 px-3 py-3">
          <span className="text-2xl leading-none">{docMeta.icon}</span>
          <div>
            <p className="font-semibold text-amber-400">{docMeta.label}</p>
            <p className="text-xs text-zinc-500">Selected document type</p>
          </div>
        </div>
      </div>

      {/* ── Animated chat-input card ────────────────────────────── */}
      <form onSubmit={handleSubmit}>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="relative rounded-2xl border border-zinc-700 bg-zinc-900 shadow-2xl shadow-black/40 backdrop-blur-2xl"
        >

          {/* Animated amber focus ring — sits behind the card border */}
          <AnimatePresence>
            {isFocused && (
              <motion.span
                key="focus-ring"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="pointer-events-none absolute inset-0 rounded-2xl ring-2 ring-amber-500/30"
              />
            )}
          </AnimatePresence>

          {/* Textarea */}
          <div className="px-4 pt-4 pb-2">
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Apna case describe karein... (Hindi ya English mein likha ja sakta hai)"
              disabled={busy}
              className="w-full resize-none bg-transparent text-zinc-100 placeholder-zinc-500 text-sm leading-relaxed focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ minHeight: 80, maxHeight: 200 }}
            />
          </div>

          {/* Character count */}
          <div className="px-4 pb-1 flex justify-end">
            <span className="font-mono text-xs text-zinc-600 pointer-events-none select-none">
              {text.length} chars
            </span>
          </div>

          {/* Toolbar */}
          <div className="flex items-center justify-between border-t border-zinc-800 px-3 py-2">

            {/* Left: Try example */}
            <div>
              {hasDemo && (
                <motion.button
                  type="button"
                  onClick={handleDemoFill}
                  disabled={busy}
                  whileTap={{ scale: 0.94 }}
                  className="flex items-center gap-1.5 rounded-lg px-2 py-2 text-xs text-zinc-400 hover:text-amber-400 transition-colors duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Zap className="h-3.5 w-3.5" />
                  Try example
                </motion.button>
              )}
            </div>

            {/* Right: Submit */}
            <motion.button
              type="submit"
              disabled={!canSubmit}
              whileHover={canSubmit ? { scale: 1.01 } : {}}
              whileTap={canSubmit ? { scale: 0.98 } : {}}
              className={[
                "flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors duration-200",
                canSubmit
                  ? "bg-gradient-to-r from-amber-500 to-orange-500 text-zinc-950 cursor-pointer"
                  : "bg-zinc-800 text-zinc-600 cursor-not-allowed",
              ].join(" ")}
            >
              {busy ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  Starting pipeline...
                </>
              ) : (
                <>
                  <ArrowRight className="h-4 w-4" />
                  Generate Document
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* Disclaimer */}
        <p className="mt-3 text-xs text-zinc-600">
          Minimum 20 characters recommended for best results. Your data is not stored permanently.
        </p>
      </form>
    </div>
  );
}
