/**
 * hooks/useSSE.js — Custom hook for Server-Sent Events
 *
 * Connects to GET /stream/{sessionId} and parses agent status events.
 *
 * Each SSE message is JSON: { agent, status, data }
 *   agent:  "intake" | "research" | "drafter" | "verifier" | "system"
 *   status: "running" | "complete" | "error"
 *   data:   arbitrary object with agent output
 *
 * Returns:
 *   events         — array of all raw parsed SSE payloads
 *   agentStatuses  — { intake, research, drafter, verifier } each = 'waiting'|'running'|'complete'|'error'
 *   isComplete     — true when system "complete" event received or all 4 agents complete
 *   error          — error message string or null
 *   draft          — string draft text from drafter agent
 *   verification   — verification object from verifier agent
 *
 * When sessionId is null the hook is a no-op (safe to call before pipeline starts).
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { API_BASE } from "../lib/api";

const AGENT_KEYS = ["intake", "research", "drafter", "verifier"];

const DEFAULT_STATUSES = Object.fromEntries(
  AGENT_KEYS.map((k) => [k, "waiting"])
);

/**
 * @param {string|null} sessionId
 * @returns {{ events: object[], agentStatuses: object, isComplete: boolean, error: string|null, draft: string|null, verification: object|null }}
 */
export function useSSE(sessionId) {
  const [events, setEvents] = useState([]);
  const [agentStatuses, setAgentStatuses] = useState({ ...DEFAULT_STATUSES });
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState(null);
  const [draft, setDraft] = useState(null);
  const [verification, setVerification] = useState(null);
  const [filingData, setFilingData] = useState(null);
  const esRef = useRef(null);

  const cleanup = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!sessionId) {
      setEvents([]);
      setAgentStatuses({ ...DEFAULT_STATUSES });
      setIsComplete(false);
      setError(null);
      setDraft(null);
      setVerification(null);
      setFilingData(null);
      return;
    }

    // Reset all state when a new session begins
    setEvents([]);
    setAgentStatuses({ ...DEFAULT_STATUSES });
    setIsComplete(false);
    setError(null);
    setDraft(null);
    setVerification(null);
    setFilingData(null);

    const es = new EventSource(`${API_BASE}/stream/${sessionId}`);
    esRef.current = es;

    es.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }

      const { agent, status, data = {} } = payload;

      // Append to raw events list
      setEvents((prev) => [...prev, payload]);

      if (agent === "system") {
        if (status === "complete") {
          setIsComplete(true);
          if (data.draft) setDraft(data.draft);
          if (data.verification) setVerification(data.verification);
          if (data.filing) setFilingData(data.filing);
          cleanup();
        } else if (status === "error") {
          setError(data.error || data.message || "An unknown error occurred");
          cleanup();
        }
        return;
      }

      // Update individual agent status
      if (AGENT_KEYS.includes(agent)) {
        setAgentStatuses((prev) => ({
          ...prev,
          [agent]: status === "running" ? "running"
                 : status === "complete" ? "complete"
                 : status === "error" ? "error"
                 : prev[agent],
        }));

        // Extract outputs from completed agents
        if (status === "complete") {
          if (agent === "drafter" && data.draft) {
            setDraft(data.draft);
          }
          if (agent === "verifier" && data.verification) {
            setVerification(data.verification);
          }
          if (agent === "filing_assistant" && data.filing) {
            setFilingData(data.filing);
          }
        }
      }
    };

    es.onerror = () => {
      setError((prev) => prev ?? "Connection to server lost");
      cleanup();
    };

    return cleanup;
  }, [sessionId, cleanup]);

  // Derived: mark complete when all 4 agents have finished
  useEffect(() => {
    const allDone = AGENT_KEYS.every((k) => agentStatuses[k] === "complete");
    if (allDone) {
      setIsComplete(true);
    }
  }, [agentStatuses]);

  return { events, agentStatuses, isComplete, error, draft, verification, filingData };
}
