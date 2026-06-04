from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f0f1a;
    color: #e0e0e0;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  .header {
    background: #1a1a2e;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #2a2a4a;
    flex-shrink: 0;
  }
  .header-title { font-size: 18px; font-weight: 600; }
  .header-sub { font-size: 12px; color: #888; }
  .btn {
    padding: 6px 14px;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    background: #2a2a4a;
    color: #e0e0e0;
    cursor: pointer;
    font-size: 13px;
  }
  .btn:hover { background: #3a3a5a; }

  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .msg {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.5;
    font-size: 14px;
  }
  .msg.user {
    align-self: flex-end;
    background: #1e3a5f;
    border-bottom-right-radius: 4px;
  }
  .msg.bot {
    align-self: flex-start;
    background: #2a2a3e;
    border-bottom-left-radius: 4px;
  }
  .msg.bot p { margin: 0 0 8px; }
  .msg.bot p:last-child { margin-bottom: 0; }
  .msg.bot code {
    background: #1a1a2e;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
  }
  .msg.bot pre {
    background: #1a1a2e;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 8px 0;
  }
  .msg.bot pre code { background: none; padding: 0; }
  .msg.bot ul, .msg.bot ol { padding-left: 20px; margin: 4px 0; }
  .msg.bot a { color: #4fc3f7; }

  .search-info {
    font-size: 11px;
    color: #666;
    align-self: flex-start;
    padding: 0 16px;
    margin-top: -8px;
  }

  .input-area {
    padding: 16px 20px;
    background: #1a1a2e;
    border-top: 1px solid #2a2a4a;
    display: flex;
    gap: 10px;
    flex-shrink: 0;
  }
  .input-area input {
    flex: 1;
    padding: 10px 16px;
    border: 1px solid #3a3a5a;
    border-radius: 8px;
    background: #0f0f1a;
    color: #e0e0e0;
    font-size: 14px;
    outline: none;
  }
  .input-area input:focus { border-color: #4fc3f7; }
  .input-area button {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    background: #1e3a5f;
    color: #e0e0e0;
    cursor: pointer;
    font-size: 14px;
  }
  .input-area button:hover { background: #2a4a7f; }
  .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }

  .loading {
    align-self: flex-start;
    color: #888;
    font-size: 13px;
    padding: 8px 16px;
  }
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="header-title">Ollama Bot</div>
    <div class="header-sub">Model: MODEL_NAME</div>
  </div>
  <div class="header-actions">
    <button class="btn" onclick="clearChat()">Clear</button>
  </div>
</div>

<div id="messages"></div>

<div class="input-area">
  <input type="text" id="input" placeholder="Type your message..." autofocus>
  <button id="sendBtn" onclick="sendMessage()">Send</button>
</div>

<script>
function addMessage(role, content, searchQuery) {
  const container = document.getElementById('messages');
  if (searchQuery) {
    const info = document.createElement('div');
    info.className = 'search-info';
    info.textContent = 'search: ' + searchQuery;
    container.appendChild(info);
  }
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  if (role === 'bot') {
    div.innerHTML = marked.parse(content);
  } else {
    div.textContent = content;
  }
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function addLoading() {
  const container = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'loading';
  div.id = 'loading';
  div.textContent = 'Thinking...';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeLoading() {
  const el = document.getElementById('loading');
  if (el) el.remove();
}

async function sendMessage() {
  const input = document.getElementById('input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  document.getElementById('sendBtn').disabled = true;

  addMessage('user', text);
  addLoading();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    removeLoading();
    addMessage('bot', data.response, data.search_query);
  } catch (err) {
    removeLoading();
    addMessage('bot', 'Error: ' + err.message);
  }
  document.getElementById('sendBtn').disabled = false;
  document.getElementById('input').focus();
}

async function clearChat() {
  document.getElementById('messages').innerHTML = '';
  await fetch('/api/clear', { method: 'POST' });
}

document.getElementById('input').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') sendMessage();
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    model_name = _session.agent.llm.model if _session else "unknown"
    return HTML_PAGE.replace("MODEL_NAME", model_name, 2)


@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "").strip()
    if not message:
        return JSONResponse({"error": "empty message"}, status_code=400)
    response = _session.send(message)
    return {
        "response": response,
        "search_query": getattr(_session, "last_search_query", ""),
    }


@app.post("/api/clear")
async def clear():
    _session.clear()
    return {"status": "ok"}


@app.get("/api/report")
async def report():
    return _session.report()


def run_server(agent: Agent, host: str = "127.0.0.1", port: int = 80):
    import uvicorn

    init(agent)
    print(f"Web server listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
