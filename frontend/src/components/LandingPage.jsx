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
      <div className="relative flex flex-col items-center text-center py-12 sm:py-20 space-y-6">
        {/* Emblem background watermark */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 flex items-center justify-center"
          style={{ zIndex: 0 }}
        >
          <img
            src="/emblem.jpg"
            alt=""
            className="h-full w-auto max-h-full select-none"
            style={{
              opacity: 0.15,
              mixBlendMode: "screen",
            }}
          />
        </div>

        <div className="relative z-10 flex flex-col items-center space-y-6">
          <div className="space-y-2">
            <h1 className="text-5xl sm:text-7xl text-amber-500 font-shrikhand leading-tight">
              न्यायमित्र
            </h1>
            <p className="text-2xl sm:text-4xl font-bold text-zinc-100 tracking-tight">
              NyayaMitra
            </p>
          </div>

          <p className="text-base sm:text-lg text-zinc-300 max-w-xs sm:max-w-sm leading-relaxed">
            AI-powered legal documents for every Indian
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
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {STATS.map((stat, i) => (
          <div
            key={stat.number}
            className={`rounded-xl border border-zinc-800 bg-zinc-900/80 backdrop-blur-sm p-6 text-center space-y-1 stat-reveal stat-reveal-${i + 1}`}
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
              className="rounded-xl border border-zinc-800 bg-zinc-900/80 backdrop-blur-sm p-5 space-y-3"
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
              className="rounded-xl border border-zinc-800 bg-zinc-900/80 backdrop-blur-sm p-4 text-center space-y-2 opacity-80"
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

      {/* Footer note */}
      <p className="text-center font-mono text-xs text-zinc-600 pb-4">
        Not a substitute for professional legal advice &bull; कानूनी सलाह के लिए वकील से मिलें
      </p>
    </div>
  );
}
