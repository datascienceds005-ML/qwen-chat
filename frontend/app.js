'use strict';

/* ══════════ Configuration ══════════ */
const API_URL = '/v1/chat/completions';
const SYSTEM_PROMPT =
  "You are Qwen, a helpful AI assistant running fully offline on the user's device. " +
  "Answer clearly and concisely. Use Markdown. Use fenced code blocks for code.";
const TEMPERATURE = 0.7;
const MAX_TOKENS  = 640;
const STORAGE_KEY = 'qwen-chat-v1';

/* ══════════ DOM & state ══════════ */
const chatEl  = document.getElementById('chat');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const dotEl   = document.getElementById('statusDot');
const tagEl   = document.getElementById('engineTag');

let messages   = [];      // [{role, content}] — user/assistant turns
let generating = false;
let abortCtrl  = null;
let bubbleEl   = null;
let answer     = '';
let stick      = true;
let rafPending = false;

function save() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ v: 1, messages: messages.slice(-100) })); } catch {}
}
function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY));
    messages = (raw && raw.v === 1 && Array.isArray(raw.messages)) ? raw.messages : [];
  } catch { messages = []; }
}

/* ══════════ Markdown — escape-first renderer (ADR-002) ══════════
   Every character of model output is HTML-escaped BEFORE any parsing, and
   the parser only emits markup from its own whitelist. Model output can
   never inject HTML — XSS is structurally impossible, no sanitizer needed. */
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;')
          .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function inline(s) {
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/(^|[\s(])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>');
  s = s.replace(/\[([^\]]+)\]\((https?:[^\s)]+)\)/g,
                '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return s;
}
function block(lines) {
  const isUl = l => /^\s*[-*]\s+/.test(l);
  const isOl = l => /^\s*\d+[.)]\s+/.test(l);
  const isH  = l => /^#{1,6}\s+/.test(l);
  const isQ  = l => /^&gt;\s?/.test(l);
  const isHr = l => /^\s*---+\s*$/.test(l);
  let html = '', i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (!l.trim()) { i++; continue; }
    if (isUl(l) || isOl(l)) {
      const ordered = isOl(l), items = [];
      while (i < lines.length && (ordered ? isOl(lines[i]) : isUl(lines[i])))
        items.push(lines[i++].replace(ordered ? /^\s*\d+[.)]\s+/ : /^\s*[-*]\s+/, ''));
      const tag = ordered ? 'ol' : 'ul';
      html += `<${tag}>${items.map(x => `<li>${inline(x)}</li>`).join('')}</${tag}>`;
    } else if (isH(l)) {
      const m = l.match(/^(#{1,6})\s+(.*)/);
      html += `<h${Math.min(m[1].length + 2, 6)}>${inline(m[2])}</h${Math.min(m[1].length + 2, 6)}>`; i++;
    } else if (isHr(l)) { html += '<hr>'; i++;
    } else if (isQ(l)) {
      const buf = [];
      while (i < lines.length && isQ(lines[i])) buf.push(lines[i++].replace(/^&gt;\s?/, ''));
      html += `<blockquote>${inline(buf.join('<br>'))}</blockquote>`;
    } else {
      const buf = [];
      while (i < lines.length && lines[i].trim() && !isUl(lines[i]) && !isOl(lines[i])
             && !isH(lines[i]) && !isQ(lines[i]) && !isHr(lines[i])) buf.push(lines[i++]);
      html += `<p>${buf.map(inline).join('<br>')}</p>`;
    }
  }
  return html || '<p></p>';
}
function renderMarkdown(src) {
  const parts = String(src).split('```');
  let html = '';
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) {                       // code segment — robust mid-stream
      let seg = parts[i], lang = 'code', body = seg;
      const nl = seg.indexOf('\n');
      if (nl > -1 && nl <= 20 && /^[\w+#.-]*$/.test(seg.slice(0, nl).trim())) {
        lang = seg.slice(0, nl).trim() || 'code'; body = seg.slice(nl + 1);
      }
      html += `<div class="codeblock"><div class="codehead"><span>${esc(lang)}</span>` +
              `<button class="copybtn">Copy</button></div>` +
              `<pre><code>${esc(body.replace(/\n$/, ''))}</code></pre></div>`;
    } else {
      html += block(esc(parts[i]).split('\n'));
    }
  }
  return html;
}

/* ══════════ Bubbles & scrolling ══════════ */
function addUserMsg(text) {
  const div = document.createElement('div');
  div.className = 'msg user';
  div.innerHTML = `<div class="bubble">${esc(text).replace(/\n/g, '<br>')}</div>`;
  chatEl.appendChild(div);
}
function addAssistantMsg() {
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.innerHTML = '<div class="bubble"><span class="cursor">▍</span></div>';
  chatEl.appendChild(div);
  bubbleEl = div.querySelector('.bubble');
  answer = '';
}
function addAssistantDone(text) {
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.innerHTML = `<div class="bubble">${renderMarkdown(text)}</div>`;
  chatEl.appendChild(div);
}
const nearBottom = () => chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight < 90;
function scrollToBottom(force) { if (force || stick) chatEl.scrollTop = chatEl.scrollHeight; }
chatEl.addEventListener('scroll', () => { stick = nearBottom(); });

function updateAssistant() {                     // throttled to display refresh
  if (rafPending) return;
  rafPending = true;
  requestAnimationFrame(() => {
    rafPending = false;
    if (bubbleEl) bubbleEl.innerHTML = renderMarkdown(answer) + '<span class="cursor">▍</span>';
  });
}

/* ══════════ Send / stream / stop ══════════ */
function setGenerating(on) {
  generating = on;
  sendBtn.classList.toggle('stop', on);
  sendBtn.textContent = on ? '■' : '↑';
  sendBtn.title = on ? 'Stop generating' : 'Send';
}

function send() {
  const text = inputEl.value.trim();
  if (!text || generating) return;
  inputEl.value = ''; autoGrow();
  if (chatEl.querySelector('.hero')) chatEl.innerHTML = '';
  stick = true;
  messages.push({ role: 'user', content: text });
  addUserMsg(text);
  addAssistantMsg();
  scrollToBottom(true);
  setGenerating(true);
  streamCompletion();
}

async function streamCompletion() {
  abortCtrl = new AbortController();
  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'system', content: SYSTEM_PROMPT }, ...messages],
        stream: true, temperature: TEMPERATURE, max_tokens: MAX_TOKENS,
      }),
      signal: abortCtrl.signal,
    });
    if (!res.ok) {
      let detail = `Server error ${res.status}`;
      try { const j = await res.json(); if (typeof j.detail === 'string') detail = j.detail; } catch {}
      throw new Error(detail);
    }
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const raw of lines) {
        const line = raw.trim();
        if (!line.startsWith('data:')) continue;
        const payload = line.slice(5).trim();
        if (payload === '[DONE]') continue;
        let j; try { j = JSON.parse(payload); } catch { continue; }
        if (j.error) throw new Error(j.error.message || 'Engine error');
        const piece = j.choices?.[0]?.delta?.content;
        if (piece) { answer += piece; updateAssistant(); scrollToBottom(); }
      }
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      const note = `<div class="error">⚠ ${esc(err.message ||
        'Could not reach the local server. Start it in Termux with ./start.sh')}</div>`;
      if (bubbleEl && answer.trim()) {
        bubbleEl.innerHTML = renderMarkdown(answer) + note;
        messages.push({ role: 'assistant', content: answer }); save();
      } else if (bubbleEl) {
        bubbleEl.innerHTML = note;
      }
      bubbleEl = null;
    }
  } finally {
    if (bubbleEl) {
      if (answer.trim()) {
        bubbleEl.innerHTML = renderMarkdown(answer);
        messages.push({ role: 'assistant', content: answer });
        save();
      } else {
        bubbleEl.closest('.msg').remove();       // aborted before first token
      }
      bubbleEl = null;
    }
    setGenerating(false);
    abortCtrl = null;
    answer = '';
    scrollToBottom();
  }
}

/* ══════════ Empty state, misc ══════════ */
function greet() {
  chatEl.innerHTML = `
    <div class="hero">
      <div class="logo">●</div>
      <h2>Qwen2.5 · 1.5B — On-device</h2>
      <p>Everything runs locally.<br>No internet, no cloud, no telemetry.</p>
      <div class="chips">
        <button data-q="Explain how large language models work">Explain how LLMs work</button>
        <button data-q="write code for a palindrome check in Python">Write Python code</button>
        <button data-q="tell a long story about a robot">Tell me a story</button>
      </div>
    </div>`;
  chatEl.querySelectorAll('.chips button').forEach(b =>
    b.addEventListener('click', () => { inputEl.value = b.dataset.q; autoGrow(); inputEl.focus(); }));
}
function newChat() {
  if (generating && abortCtrl) abortCtrl.abort();
  messages = []; save();
  chatEl.innerHTML = '';
  greet();
  inputEl.focus();
}
function autoGrow() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 140) + 'px';
}
async function checkHealth() {
  try {
    const r = await fetch('/api/health', { cache: 'no-store' });
    dotEl.className = 'dot ' + (r.ok ? 'ok' : 'bad');
    if (r.ok) {
      const j = await r.json();
      tagEl.textContent = j.engine === 'mock' ? 'MOCK ENGINE' : 'LOCAL';
      dotEl.title = `${j.engine} · v${j.version}`;
    }
  } catch { dotEl.className = 'dot bad'; }
}

/* ══════════ Events & init ══════════ */
sendBtn.addEventListener('click', () => generating ? abortCtrl.abort() : send());
document.getElementById('newChatBtn').addEventListener('click', newChat);
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!generating) send(); }
});
inputEl.addEventListener('input', autoGrow);

chatEl.addEventListener('click', e => {          // copy buttons on code blocks
  const b = e.target.closest('.copybtn');
  if (!b) return;
  const code = b.closest('.codeblock').querySelector('code');
  navigator.clipboard.writeText(code.innerText).then(() => {
    b.textContent = 'Copied';
    setTimeout(() => { b.textContent = 'Copy'; }, 1200);
  });
});

load();
if (messages.length) {
  for (const m of messages) {
    if (m.role === 'user') addUserMsg(m.content);
    else if (m.role === 'assistant') addAssistantDone(m.content);
  }
  requestAnimationFrame(() => chatEl.scrollTop = chatEl.scrollHeight);
} else greet();

autoGrow();
checkHealth(); setInterval(checkHealth, 5000);

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () =>
    navigator.serviceWorker.register('/sw.js').catch(() => {}));
}
