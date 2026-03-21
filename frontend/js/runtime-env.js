// Runtime API base URL
// - Local dev (localhost / 127.0.0.1): để config.js tự phát hiện → http://localhost:8000
// - Production: trỏ về Hugging Face Spaces backend
(function () {
  const host = window.location.hostname;
  const isLocal =
    host === "localhost" ||
    host === "127.0.0.1";

  if (!isLocal) {
    // Shared hosting không có Docker, nên phải set cứng ở đây
    window.__API_BASE_URL__ = "https://hoangkhang2-medai-dermatology.hf.space";
  }
})();
