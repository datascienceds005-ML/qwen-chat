ADR-002 — Escape-first built-in Markdown renderer
Status: accepted · Date: v0.1.0

Context
Model output is untrusted. We need markdown rendering that works with zeronetwork access at build or runtime (strict GitHub-only phase) and is safe.

Decision
app.js HTML-escapes ALL model output first, then parses with a whitelistrenderer that only emits markup it generates itself (p, h3–h6, ul/ol, li,blockquote, hr, strong, em, code, a[href^=http]). Code fences are handled bysplitting on ``` before escaping, so partial fences degrade gracefullymid-stream. Copy buttons are delegated events reading DOM text.

Consequences
XSS from model output is structurally impossible — no sanitizer needed.
Repo stays fully self-contained (no vendored marked/DOMPurify).
If full CommonMark is needed later, swap to marked+DOMPurify behind the samerenderMarkdown(text) → html signature; nothing else changes.
