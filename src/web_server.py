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
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<style>
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #0f0f1a;
  --bg-tertiary: #1a1a2e;
  --neon-cyan: #00f0ff;
  --neon-magenta: #ff00aa;
  --neon-purple: #a855f7;
  --text-primary: #e0e0f0;
  --text-secondary: #8888bb;
  --text-dim: #555577;
  --glow-cyan: 0 0 12px rgba(0,240,255,.12), 0 0 30px rgba(0,240,255,.04);
  --glow-magenta: 0 0 12px rgba(255,0,170,.12), 0 0 30px rgba(255,0,170,.04);
  --border: #2a2a4e;
}

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

.header {
  background: var(--bg-secondary);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  position: relative;
}
.header::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-magenta), transparent);
}
.header-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.header-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.btn {
  padding: 6px 16px;
  border: 1px solid var(--neon-magenta);
  border-radius: 6px;
  background: transparent;
  color: var(--neon-magenta);
  cursor: pointer;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all .2s;
}
.btn:hover {
  background: var(--neon-magenta);
  color: var(--bg-primary);
  box-shadow: var(--glow-magenta);
}

#messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-behavior: smooth;
}
#messages::-webkit-scrollbar { width: 6px; }
#messages::-webkit-scrollbar-track { background: var(--bg-primary); }
#messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

.msg {
  max-width: 82%;
  padding: 14px 18px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  position: relative;
}
.msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, rgba(255,0,170,.12), rgba(168,85,247,.08));
  border: 1px solid rgba(255,0,170,.25);
  border-bottom-right-radius: 4px;
  box-shadow: var(--glow-magenta);
}
.msg.bot {
  align-self: flex-start;
  background: linear-gradient(135deg, rgba(0,240,255,.08), rgba(168,85,247,.04));
  border: 1px solid rgba(0,240,255,.18);
  border-bottom-left-radius: 4px;
  box-shadow: var(--glow-cyan);
}
.msg.bot p { margin: 0 0 8px; }
.msg.bot p:last-child { margin-bottom: 0; }
.msg.bot code {
  background: rgba(0,240,255,.08);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: var(--neon-cyan);
}
.msg.bot pre {
  background: rgba(0,0,0,.4);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid rgba(0,240,255,.1);
  position: relative;
}
.msg.bot pre code { background: none; padding: 0; color: inherit; font-family: 'JetBrains Mono', monospace; font-size: 13px; }
.msg.bot ul, .msg.bot ol { padding-left: 20px; margin: 4px 0; }
.msg.bot a { color: var(--neon-cyan); text-decoration: none; }
.msg.bot a:hover { text-shadow: 0 0 8px rgba(0,240,255,.5); }
.msg.bot hr { border: none; border-top: 1px solid var(--border); margin: 12px 0; }
.msg.bot blockquote {
  border-left: 3px solid var(--neon-purple);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--text-secondary);
}

.copy-btn {
  position: absolute;
  top: 6px; right: 6px;
  padding: 3px 8px;
  font-size: 10px;
  background: rgba(0,240,255,.08);
  border: 1px solid rgba(0,240,255,.15);
  border-radius: 4px;
  color: var(--neon-cyan);
  cursor: pointer;
  opacity: 0;
  transition: opacity .2s;
}
pre:hover .copy-btn { opacity: 1; }
.copy-btn:hover { background: rgba(0,240,255,.18); }

.timestamp {
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 4px;
  text-align: right;
}

.search-info {
  font-size: 11px;
  color: var(--neon-magenta);
  align-self: flex-start;
  padding: 2px 18px;
  opacity: .75;
}

.loading {
  align-self: flex-start;
  color: var(--neon-cyan);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  padding: 8px 18px;
}

.input-area {
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}
.input-area textarea {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  resize: none;
  min-height: 42px;
  max-height: 160px;
  line-height: 1.4;
  font-family: inherit;
  transition: border-color .2s, box-shadow .2s;
}
.input-area textarea:focus {
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}
.input-area textarea::placeholder { color: var(--text-dim); }
.input-area button {
  padding: 10px 24px;
  border: 1px solid var(--neon-cyan);
  border-radius: 8px;
  background: transparent;
  color: var(--neon-cyan);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: all .2s;
  align-self: flex-end;
}
.input-area button:hover {
  background: var(--neon-cyan);
  color: var(--bg-primary);
  box-shadow: var(--glow-cyan);
}
.input-area button:disabled { opacity: .3; cursor: not-allowed; box-shadow: none; }
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="header-title">OLLAMA BOT</div>
    <div class="header-sub">Model: MODEL_NAME</div>
  </div>
  <button class="btn" onclick="clearChat()">Clear</button>
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

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
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
    if (!started) removeLoading();
    renderBotContent();
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('input').focus();
  });

    es.addEventListener('error', function (e) {
    es.close();
    removeLoading();
    if (e.data) {
      try {
        const p = JSON.parse(e.data);
        const c = document.getElementById('messages');
        const d = document.createElement('div');
        d.className = 'msg bot';
        d.innerHTML = '<span style="color:var(--neon-magenta)">ERROR: ' + (p.message || '') + '</span>';
        c.appendChild(d);
      } catch (_) {}
    } else if (!started) {
      const c = document.getElementById('messages');
      const d = document.createElement('div');
      d.className = 'msg bot';
      d.textContent = 'Error: connection failed';
      c.appendChild(d);
    }
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('input').focus();
  });
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
