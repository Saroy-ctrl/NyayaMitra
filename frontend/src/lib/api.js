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
export async function startPipeline(docType, description, sessionId, extractedData = null) {
  const body = { doc_type: docType, description, session_id: sessionId };
  if (extractedData && Object.keys(extractedData).length > 0) {
    body.extracted_data = extractedData;
  }
  const res = await fetch(`${API_BASE}/pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Pipeline start failed (${res.status}): ${text}`);
  }

  return res.json();
}

/**
 * POST /api/chat/intake — send a conversational message to the intake agent.
 *
 * @param {string} docType
 * @param {string} sessionId
 * @param {Array<{role: string, content: string}>} messages
 * @returns {Promise<{ agent_reply: string, is_complete: boolean, extracted_data: object, missing_fields: string[] }>}
 */
export async function chatWithIntake(docType, sessionId, messages, lang = "en") {
  const res = await fetch(`${API_BASE}/api/chat/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_type: docType, session_id: sessionId, messages, lang }),
  });
  if (!res.ok) throw new Error("Intake API failed");
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
