import axios from "axios";

const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const api  = axios.create({ baseURL: BASE });

export async function uploadPDF(file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post("/api/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) =>
      onProgress && onProgress(Math.round((e.loaded * 100) / e.total)),
  });
  return res.data;
}

export function streamQuery({
  query, sessionId,
  onStatus, onAnswer, onError,
}) {
  const body = JSON.stringify({
    query,
    session_id: sessionId,
  });

  const controller = new AbortController();

  fetch(`${BASE}/api/query/stream`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body,
    signal:  controller.signal,
  })
    .then(async (res) => {
      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const evt = JSON.parse(line.slice(6));
            if (evt.type === "status") onStatus?.(evt.message);
            if (evt.type === "answer") onAnswer?.(evt.payload);
            if (evt.type === "error")  onError?.(evt.message);
          } catch (_) {}
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError?.(err.message);
    });

  return () => controller.abort();
}

export const getEvalStats  = (docId = "") =>
  api.get("/api/eval/stats",  { params: { doc_id: docId } }).then(r => r.data);

export const getRecentRuns = (n = 10, docId = "") =>
  api.get("/api/eval/recent", { params: { n, doc_id: docId } }).then(r => r.data);

export const getHistory   = (sessionId) =>
  api.get(`/api/session/${sessionId}/history`).then(r => r.data);

export const clearSession = (sessionId) =>
  api.delete(`/api/session/${sessionId}`).then(r => r.data);

export const getIndexes   = () =>
  api.get("/api/indexes").then(r => r.data);


export async function uploadMultiplePDFs(files, onProgress) {
  const form = new FormData();
  files.forEach(file => form.append("files", file));

  const res = await api.post("/api/upload/batch", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) =>
      onProgress && onProgress(Math.round((e.loaded * 100) / e.total)),
  });
  return res.data;
}

export const listDocuments   = () =>
  api.get("/api/documents").then(r => r.data);

export const getDocument     = (docId) =>
  api.get(`/api/documents/${docId}`).then(r => r.data);

export const deleteDocument  = (docId) =>
  api.delete(`/api/documents/${docId}`).then(r => r.data);
