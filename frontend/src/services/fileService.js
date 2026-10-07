export function validatePDF(file) {
  if (!file) return "No file selected.";
  if (!file.name.toLowerCase().endsWith(".pdf"))
    return "Only PDF files are accepted.";
  if (file.size > 50 * 1024 * 1024)
    return "File exceeds the 50 MB limit.";
  return null; // null = valid
}

export function formatFileSize(bytes) {
  if (bytes < 1024)       return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatTimestamp(ts) {
  return new Date(ts * 1000).toLocaleTimeString();
}
