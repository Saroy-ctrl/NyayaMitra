/**
 * PaymentModal.jsx — Simulated lawyer-verification payment flow
 *
 * Props:
 *   onClose() — called when the user dismisses the modal
 *
 * Internal state machine: "idle" → "processing" → "success"
 */

import { useState } from "react";

const PAYMENT_METHODS = [
  { id: "upi", label: "UPI", desc: "Pay via UPI ID or QR code" },
  { id: "card", label: "Card", desc: "Debit / Credit card" },
];

export default function PaymentModal({ onClose }) {
  const [paymentMethod, setPaymentMethod] = useState("upi");
  const [paymentStatus, setPaymentStatus] = useState("idle"); // idle | processing | success

  function handlePay() {
    setPaymentStatus("processing");
    setTimeout(() => {
      setPaymentStatus("success");
    }, 2000);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/80 backdrop-blur-sm px-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 sm:p-8 max-w-md w-full space-y-6 shadow-2xl">

        {paymentStatus === "success" ? (
          /* ── Success state ── */
          <div className="flex flex-col items-center text-center space-y-4 py-4">
            <div className="h-16 w-16 rounded-full bg-amber-500/15 border border-amber-500/40 flex items-center justify-center">
              <span className="text-3xl text-amber-400">&#10003;</span>
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-semibold text-zinc-100">Payment Successful!</h3>
              <p className="text-sm text-zinc-400 leading-relaxed">
                A lawyer has been assigned to verify your document. You will receive a confirmation
                within 24 hours.
              </p>
            </div>
            <p className="font-devanagari text-xs text-zinc-600">
              एक वकील को आपके दस्तावेज़ की पुष्टि के लिए नियुक्त किया गया है
            </p>
            <button
              onClick={onClose}
              className="mt-2 w-full rounded-xl bg-amber-500 hover:bg-amber-400 px-6 py-2.5 text-sm font-bold text-zinc-950 transition-colors duration-200"
            >
              Done
            </button>
          </div>
        ) : (
          /* ── Idle / Processing state ── */
          <>
            {/* Header */}
            <div className="flex items-start justify-between">
              <div>
                <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">
                  Expert Verification
                </p>
                <h3 className="text-lg font-semibold text-zinc-100">Lawyer Review — &#8377;199</h3>
                <p className="text-xs text-zinc-500 mt-0.5">
                  One-time fee &bull; Verified within 24 hours
                </p>
              </div>
              <button
                onClick={onClose}
                disabled={paymentStatus === "processing"}
                className="text-zinc-500 hover:text-zinc-300 transition-colors disabled:opacity-40 p-1"
                aria-label="Close"
              >
                &#10005;
              </button>
            </div>

            {/* What you get */}
            <ul className="space-y-2 rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
              {[
                "Qualified lawyer reviews your generated document",
                "Flags any factual or legal accuracy issues",
                "Issues a signed verification certificate",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-zinc-300">
                  <span className="text-amber-500 mt-0.5 shrink-0">&#10003;</span>
                  {item}
                </li>
              ))}
            </ul>

            {/* Payment method selector */}
            <div className="space-y-2">
              <p className="text-xs font-medium text-zinc-400 uppercase tracking-widest">
                Payment Method
              </p>
              <div className="grid grid-cols-2 gap-2">
                {PAYMENT_METHODS.map((method) => (
                  <label
                    key={method.id}
                    className={`flex flex-col gap-0.5 rounded-xl border p-3 cursor-pointer transition-colors duration-150 ${
                      paymentMethod === method.id
                        ? "border-amber-500/60 bg-amber-500/10"
                        : "border-zinc-700 hover:border-zinc-600"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="payment_method"
                        value={method.id}
                        checked={paymentMethod === method.id}
                        onChange={() => setPaymentMethod(method.id)}
                        className="accent-amber-500"
                      />
                      <span className="text-sm font-semibold text-zinc-100">{method.label}</span>
                    </div>
                    <p className="text-xs text-zinc-500 pl-5">{method.desc}</p>
                  </label>
                ))}
              </div>
            </div>

            {/* UPI / Card dummy input */}
            {paymentMethod === "upi" ? (
              <div className="space-y-1">
                <label className="text-xs text-zinc-400">UPI ID</label>
                <input
                  type="text"
                  placeholder="yourname@upi"
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500 transition-colors"
                  disabled={paymentStatus === "processing"}
                />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="space-y-1">
                  <label className="text-xs text-zinc-400">Card Number</label>
                  <input
                    type="text"
                    placeholder="4111 1111 1111 1111"
                    maxLength={19}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500 transition-colors"
                    disabled={paymentStatus === "processing"}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Expiry</label>
                    <input
                      type="text"
                      placeholder="MM / YY"
                      maxLength={7}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500 transition-colors"
                      disabled={paymentStatus === "processing"}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">CVV</label>
                    <input
                      type="text"
                      placeholder="&#8226;&#8226;&#8226;"
                      maxLength={4}
                      className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-amber-500 transition-colors"
                      disabled={paymentStatus === "processing"}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Pay button */}
            <button
              onClick={handlePay}
              disabled={paymentStatus === "processing"}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-60 disabled:cursor-not-allowed px-6 py-3 text-sm font-bold text-zinc-950 transition-colors duration-200"
            >
              {paymentStatus === "processing" ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z" />
                  </svg>
                  Processing…
                </>
              ) : (
                "Pay &#8377;199"
              )}
            </button>

            <p className="text-center font-mono text-xs text-zinc-600">
              * Demo mode &mdash; no real payment is processed
            </p>
          </>
        )}
      </div>
    </div>
  );
}
