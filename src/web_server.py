import json

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from src.agent import Agent
from src.chat import ChatSession

app = FastAPI(title="Ollama Bot Web Server")

_session: ChatSession | None = None


def init(agent: Agent):
    global _session
    _session = ChatSession(agent)


HTML_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ollama Bot</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@400;600&family=VT323&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
/* ===== THEMES ===== */

.theme-cyberpunk,
.theme-default {
  --bg-primary: #0a0a0f;
  --bg-secondary: #0f0f1a;
  --bg-tertiary: #1a1a2e;
  --neon-1: #00f0ff;
  --neon-2: #ff00aa;
  --neon-3: #a855f7;
  --text-primary: #e0e0f0;
  --text-secondary: #8888bb;
  --text-dim: #555577;
  --glow-1: 0 0 12px rgba(0,240,255,.12), 0 0 30px rgba(0,240,255,.04);
  --glow-2: 0 0 12px rgba(255,0,170,.12), 0 0 30px rgba(255,0,170,.04);
  --border: #2a2a4e;
  --font-display: 'Orbitron', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --msg-user-bg: linear-gradient(135deg, rgba(255,0,170,.12), rgba(168,85,247,.08));
  --msg-user-border: rgba(255,0,170,.25);
  --msg-bot-bg: linear-gradient(135deg, rgba(0,240,255,.08), rgba(168,85,247,.04));
  --msg-bot-border: rgba(0,240,255,.18);
  --glow-user: var(--glow-2);
  --glow-bot: var(--glow-1);
}

.theme-orange-crt {
  --bg-primary: #0d0700;
  --bg-secondary: #120a00;
  --bg-tertiary: #1a0e00;
  --neon-1: #ff8800;
  --neon-2: #cc6600;
  --neon-3: #ffaa33;
  --text-primary: #ffb000;
  --text-secondary: #cc8800;
  --text-dim: #885500;
  --glow-1: 0 0 12px rgba(255,136,0,.15), 0 0 30px rgba(255,136,0,.05);
  --glow-2: 0 0 12px rgba(204,102,0,.15), 0 0 30px rgba(204,102,0,.05);
  --border: #3a2000;
  --font-display: 'VT323', monospace;
  --font-mono: 'VT323', monospace;
  --msg-user-bg: rgba(255,136,0,.08);
  --msg-user-border: rgba(255,136,0,.2);
  --msg-bot-bg: rgba(255,136,0,.05);
  --msg-bot-border: rgba(255,136,0,.15);
  --glow-user: var(--glow-2);
  --glow-bot: var(--glow-1);
}

.theme-green-crt {
  --bg-primary: #000d00;
  --bg-secondary: #001200;
  --bg-tertiary: #001a00;
  --neon-1: #00ff33;
  --neon-2: #00cc22;
  --neon-3: #66ff88;
  --text-primary: #00ff33;
  --text-secondary: #00cc33;
  --text-dim: #006611;
  --glow-1: 0 0 12px rgba(0,255,51,.15), 0 0 30px rgba(0,255,51,.05);
  --glow-2: 0 0 12px rgba(0,204,34,.15), 0 0 30px rgba(0,204,34,.05);
  --border: #003300;
  --font-display: 'VT323', monospace;
  --font-mono: 'VT323', monospace;
  --msg-user-bg: rgba(0,255,51,.08);
  --msg-user-border: rgba(0,255,51,.2);
  --msg-bot-bg: rgba(0,255,51,.05);
  --msg-bot-border: rgba(0,255,51,.15);
  --glow-user: var(--glow-2);
  --glow-bot: var(--glow-1);
}

.theme-modern {
  --bg-primary: #1a1a1a;
  --bg-secondary: #222222;
  --bg-tertiary: #2a2a2a;
  --neon-1: #3b82f6;
  --neon-2: #ef4444;
  --neon-3: #8b5cf6;
  --text-primary: #e5e5e5;
  --text-secondary: #888888;
  --text-dim: #555555;
  --glow-1: 0 0 12px rgba(59,130,246,.1);
  --glow-2: 0 0 12px rgba(239,68,68,.1);
  --border: #333333;
  --font-display: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --msg-user-bg: #1e293b;
  --msg-user-border: #334155;
  --msg-bot-bg: #262626;
  --msg-bot-border: #333333;
  --glow-user: none;
  --glow-bot: none;
}

.theme-simple {
  --bg-primary: #f8f9fa;
  --bg-secondary: #ffffff;
  --bg-tertiary: #e9ecef;
  --neon-1: #0d6efd;
  --neon-2: #dc3545;
  --neon-3: #6f42c1;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --text-dim: #adb5bd;
  --glow-1: 0 1px 3px rgba(13,110,253,.12);
  --glow-2: 0 1px 3px rgba(220,53,69,.12);
  --border: #dee2e6;
  --font-display: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --msg-user-bg: #e7f1ff;
  --msg-user-border: #b6d4fe;
  --msg-bot-bg: #ffffff;
  --msg-bot-border: #dee2e6;
  --glow-user: none;
  --glow-bot: 0 1px 2px rgba(0,0,0,.05);
}

/* scanlines overlay */
.scanlines {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none; z-index: 9999;
  display: none;
}
.theme-orange-crt .scanlines,
.theme-green-crt .scanlines {
  display: block;
  background: repeating-linear-gradient(
    0deg, transparent 0px, transparent 2px, rgba(0,0,0,.12) 2px, rgba(0,0,0,.12) 4px
  );
}

/* ===== BASE STYLES ===== */

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ===== HEADER ===== */

.header {
  background: var(--bg-secondary);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  position: relative;
  gap: 8px;
}
.header::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon-1), var(--neon-2), transparent);
}
.header-left { display: flex; align-items: center; gap: 14px; }
.header-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--neon-1), var(--neon-2));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header-sub { font-size: 11px; color: var(--text-secondary); margin-top: 1px; }

.theme-modern .header-title,
.theme-simple .header-title {
  -webkit-text-fill-color: var(--text-primary);
  background: none;
  background-clip: unset;
}

.header-right { display: flex; align-items: center; gap: 8px; }

.theme-picker {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 5px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 11px;
  cursor: pointer;
  outline: none;
}
.theme-picker:focus { border-color: var(--neon-1); }

.btn {
  padding: 5px 12px;
  border: 1px solid var(--neon-2);
  border-radius: 5px;
  background: transparent;
  color: var(--neon-2);
  cursor: pointer;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all .2s;
}
.btn:hover {
  background: var(--neon-2);
  color: var(--bg-primary);
  box-shadow: var(--glow-2);
}

/* ===== MESSAGES ===== */

#messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scroll-behavior: smooth;
}
#messages::-webkit-scrollbar { width: 5px; }
#messages::-webkit-scrollbar-track { background: var(--bg-primary); }
#messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

.msg {
  max-width: 82%;
  padding: 12px 16px;
  border-radius: 10px;
  line-height: 1.5;
  font-size: 14px;
  position: relative;
}
.msg.user {
  align-self: flex-end;
  background: var(--msg-user-bg);
  border: 1px solid var(--msg-user-border);
  border-bottom-right-radius: 3px;
  box-shadow: var(--glow-user);
}
.msg.bot {
  align-self: flex-start;
  background: var(--msg-bot-bg);
  border: 1px solid var(--msg-bot-border);
  border-bottom-left-radius: 3px;
  box-shadow: var(--glow-bot);
}
.msg.bot p { margin: 0 0 6px; }
.msg.bot p:last-child { margin-bottom: 0; }
.msg.bot code {
  background: rgba(0,0,0,.08);
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 13px;
  color: var(--neon-1);
}
.msg.bot pre {
  background: rgba(0,0,0,.3);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 6px 0;
  border: 1px solid rgba(0,0,0,.1);
  position: relative;
}
.msg.bot pre code { background: none; padding: 0; color: inherit; font-family: var(--font-mono); font-size: 13px; }
.msg.bot ul, .msg.bot ol { padding-left: 18px; margin: 4px 0; }
.msg.bot a { color: var(--neon-1); text-decoration: none; }
.msg.bot a:hover { text-shadow: 0 0 6px rgba(0,0,0,.3); }
.msg.bot hr { border: none; border-top: 1px solid var(--border); margin: 10px 0; }
.msg.bot blockquote {
  border-left: 3px solid var(--neon-3);
  padding-left: 10px;
  margin: 6px 0;
  color: var(--text-secondary);
}

/* copy button */
.copy-btn {
  position: absolute;
  top: 5px; right: 5px;
  padding: 2px 7px;
  font-size: 10px;
  background: rgba(0,0,0,.15);
  border: 1px solid rgba(0,0,0,.1);
  border-radius: 3px;
  color: var(--text-secondary);
  cursor: pointer;
  opacity: 0;
  transition: opacity .2s;
}
pre:hover .copy-btn { opacity: 1; }
.copy-btn:hover { background: rgba(0,0,0,.25); }

.timestamp {
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 4px;
  text-align: right;
}

.search-info {
  font-size: 11px;
  color: var(--neon-2);
  align-self: flex-start;
  padding: 2px 16px;
  opacity: .7;
}

.loading {
  align-self: flex-start;
  color: var(--neon-1);
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 6px 16px;
}

/* ===== INPUT ===== */

.input-area {
  padding: 14px 20px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.input-area textarea {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 7px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  resize: none;
  min-height: 38px;
  max-height: 150px;
  line-height: 1.4;
  font-family: inherit;
  transition: border-color .2s, box-shadow .2s;
}
.input-area textarea:focus {
  border-color: var(--neon-1);
  box-shadow: var(--glow-1);
}
.input-area textarea::placeholder { color: var(--text-dim); }
.input-area button {
  padding: 8px 20px;
  border: 1px solid var(--neon-1);
  border-radius: 7px;
  background: transparent;
  color: var(--neon-1);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all .2s;
  align-self: flex-end;
}
.input-area button:hover {
  background: var(--neon-1);
  color: var(--bg-primary);
  box-shadow: var(--glow-1);
}
.input-area button:disabled { opacity: .3; cursor: not-allowed; box-shadow: none; }
</style>
</head>
<body class="theme-cyberpunk">
<div class="scanlines"></div>

<div class="header">
  <div class="header-left">
    <div>
      <div class="header-title">OLLAMA BOT</div>
      <div class="header-sub">Model: MODEL_NAME</div>
    </div>
  </div>
  <div class="header-right">
    <select class="theme-picker" id="themePicker" onchange="setTheme(this.value)">
      <option value="cyberpunk">Cyberpunk</option>
      <option value="orange-crt">Orange CRT</option>
      <option value="green-crt">Green CRT</option>
      <option value="modern">Modern</option>
      <option value="simple">Simple</option>
    </select>
    <button class="btn" onclick="clearChat()">Clear</button>
  </div>
</div>

<div id="messages"></div>

<div class="input-area">
  <textarea id="input" placeholder="Type your message..." rows="1" autofocus></textarea>
  <button id="sendBtn" onclick="sendMessage()">Send</button>
</div>

<script>
let thinkingTimer = null;
let currentBotMsg = null;
let fullContent = '';

function setTheme(name) {
  document.body.className = 'theme-' + name;
  localStorage.setItem('ollama-bot-theme', name);
  document.getElementById('themePicker').value = name;
}

(function loadTheme() {
  const saved = localStorage.getItem('ollama-bot-theme') || 'cyberpunk';
  setTheme(saved);
})();

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}

function createCopyBtn(pre) {
  const btn = document.createElement('button');
  btn.className = 'copy-btn';
  btn.textContent = 'COPY';
  btn.onclick = () => {
    const code = pre.querySelector('code');
    const text = code ? code.textContent : pre.textContent;
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = 'COPIED';
      setTimeout(() => { btn.textContent = 'COPY'; }, 2000);
    });
  };
  pre.appendChild(btn);
}

function addSearchInfo(query) {
  const c = document.getElementById('messages');
  const d = document.createElement('div');
  d.className = 'search-info';
  d.textContent = 'search: ' + query;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}

function addTimestamp(el) {
  const ts = document.createElement('div');
  ts.className = 'timestamp';
  ts.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  el.appendChild(ts);
}

function addUserMessage(text) {
  const c = document.getElementById('messages');
  const d = document.createElement('div');
  d.className = 'msg user';
  d.textContent = text;
  addTimestamp(d);
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}

function addLoading() {
  const c = document.getElementById('messages');
  const d = document.createElement('div');
  d.className = 'loading';
  d.id = 'loading';
  d.textContent = 'Thinking...';
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
  let secs = 0;
  thinkingTimer = setInterval(() => {
    secs++;
    const el = document.getElementById('loading');
    if (el) el.textContent = 'Thinking... (' + secs + 's)';
  }, 1000);
}

function removeLoading() {
  if (thinkingTimer) clearInterval(thinkingTimer);
  thinkingTimer = null;
  const el = document.getElementById('loading');
  if (el) el.remove();
}

function renderBotContent() {
  if (!currentBotMsg) return;
  currentBotMsg.innerHTML = marked.parse(fullContent);
  currentBotMsg.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
  currentBotMsg.querySelectorAll('pre').forEach(pre => {
    if (!pre.querySelector('.copy-btn')) createCopyBtn(pre);
  });
  addTimestamp(currentBotMsg);
  document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
}

async function sendMessage() {
  const ta = document.getElementById('input');
  const text = ta.value.trim();
  if (!text) return;
  ta.value = '';
  autoResize(ta);
  document.getElementById('sendBtn').disabled = true;

  addUserMessage(text);
  addLoading();
  currentBotMsg = null;
  fullContent = '';
  let started = false;

  const es = new EventSource('/api/chat?message=' + encodeURIComponent(text));

  es.addEventListener('search', function (e) {
    const p = JSON.parse(e.data);
    addSearchInfo(p.query);
  });

  es.addEventListener('token', function (e) {
    if (connTimeout) clearTimeout(connTimeout);
    if (!started) { removeLoading(); started = true; }
    const p = JSON.parse(e.data);
    fullContent = p.text;
    if (!currentBotMsg) {
      currentBotMsg = document.createElement('div');
      currentBotMsg.className = 'msg bot';
      currentBotMsg.id = 'bot-msg';
      document.getElementById('messages').appendChild(currentBotMsg);
    }
    currentBotMsg.textContent = fullContent;
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
  });

  es.addEventListener('done', function (e) {
    es.close();
    if (connTimeout) clearTimeout(connTimeout);
    if (!started) removeLoading();
    renderBotContent();
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('input').focus();
  });

  let esErrCount = 0;

  es.addEventListener('error', function (e) {
    if (e.data) {
      es.close();
      removeLoading();
      try {
        const p = JSON.parse(e.data);
        const c = document.getElementById('messages');
        const d = document.createElement('div');
        d.className = 'msg bot';
        d.innerHTML = '<span style="color:var(--neon-2)">ERROR: ' + (p.message || '') + '</span>';
        c.appendChild(d);
      } catch (_) {}
      document.getElementById('sendBtn').disabled = false;
      document.getElementById('input').focus();
      return;
    }
    esErrCount++;
    if (esErrCount >= 5) {
      es.close();
      removeLoading();
      if (!started) {
        const c = document.getElementById('messages');
        const d = document.createElement('div');
        d.className = 'msg bot';
        d.textContent = 'Error: connection failed';
        c.appendChild(d);
      }
      document.getElementById('sendBtn').disabled = false;
      document.getElementById('input').focus();
    }
  });

  const connTimeout = setTimeout(function () {
    if (!started) {
      es.close();
      removeLoading();
      const c = document.getElementById('messages');
      const d = document.createElement('div');
      d.className = 'msg bot';
      d.textContent = 'Error: connection timed out';
      c.appendChild(d);
      document.getElementById('sendBtn').disabled = false;
      document.getElementById('input').focus();
    }
  }, 120000);
}

async function clearChat() {
  document.getElementById('messages').innerHTML = '';
  fullContent = '';
  currentBotMsg = null;
  await fetch('/api/clear', { method: 'POST' });
}

const ta = document.getElementById('input');
ta.addEventListener('input', function () { autoResize(this); });
ta.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    model_name = _session.agent.llm.model if _session else "unknown"
    return HTML_PAGE.replace("MODEL_NAME", model_name, 2)


@app.get("/api/chat")
async def chat(message: str = ""):
    message = message.strip()
    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)

    async def event_stream():
        async for event in _session.stream_send(message):
            if event["type"] == "search":
                yield f"event: search\ndata: {json.dumps({'query': event['query']})}\n\n"
            elif event["type"] == "token":
                yield f"event: token\ndata: {json.dumps({'text': event['text']})}\n\n"
            elif event["type"] == "done":
                yield f"event: done\ndata: {json.dumps({'processing_time': event['processing_time']})}\n\n"
            elif event["type"] == "error":
                yield f"event: error\ndata: {json.dumps({'message': event['message']})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/clear")
async def clear():
    _session.clear()
    return {"status": "ok"}


@app.get("/api/report")
async def report():
    return _session.report()


def run_server(agent: Agent, host: str = "0.0.0.0", port: int = 80):
    import uvicorn

    init(agent)
    print(f"Web server listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
