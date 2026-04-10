/**
 * lib/api.js — Backend API client
 *
 * All fetch calls to the FastAPI backend go through this module.
 * Base URL is read from VITE_API_URL env var (defaults to localhost:8000 for dev).
 *
 * Exports:
 *   API_BASE          — base URL string (consumed by useSSE hook)
 *   startPipeline     — POST /pipeline
 *   downloadPDF       — GET /download-pdf/{sessionId} returning a Blob
 *   generateSessionId — creates a random UUID for the session
 */

export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Generate a random session ID (UUID v4).
 */
export function generateSessionId() {
  return crypto.randomUUID();
}

/**
 * POST /pipeline — kick off the 4-agent pipeline for a session.
 *
 * @param {string} docType
 * @param {string} description
 * @param {string} sessionId
 * @returns {Promise<{ status: string, session_id: string }>}
 */
export async function startPipeline(docType, description, sessionId) {
  const res = await fetch(`${API_BASE}/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      doc_type: docType,
      description,
      session_id: sessionId,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Pipeline start failed (${res.status}): ${text}`);
  }

  return res.json();
}

/**
 * GET /download-pdf/{sessionId} — fetches the generated PDF as a Blob.
 *
 * @param {string} sessionId
 * @returns {Promise<Blob>}
 */
export async function downloadPDF(sessionId) {
  const res = await fetch(`${API_BASE}/download-pdf/${sessionId}`);

  if (!res.ok) {
    throw new Error(`PDF download failed (${res.status})`);
  }

  return res.blob();
}
