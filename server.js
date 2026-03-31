/**
 * ChatOGG Backend Server
 * Receives incoming SMS replies from Twilio, stores them,
 * and streams them to the frontend via Server-Sent Events (SSE).
 *
 * Deploy free on: Railway, Render, Fly.io, or any Node host.
 */

const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// ── Middleware ──
app.use(cors()); // Allow your HTML file to call this server
app.use(bodyParser.urlencoded({ extended: false })); // Twilio sends form-encoded POST
app.use(bodyParser.json());

// ── In-memory reply store ──
// Key: sessionId (timestamp string), Value: array of reply objects
const replySessions = new Map();

// SSE client registry: sessionId → array of res (response) objects
const sseClients = new Map();

// Cleanup old sessions after 10 minutes
function cleanupOldSessions() {
  const cutoff = Date.now() - 10 * 60 * 1000;
  for (const [id, replies] of replySessions.entries()) {
    if (parseInt(id) < cutoff) {
      replySessions.delete(id);
      sseClients.delete(id);
    }
  }
}
setInterval(cleanupOldSessions, 5 * 60 * 1000);

// ── Known group numbers (for validation) ──
const GROUP_NUMBERS = new Set([
  '8168359882','8167191640','8166782527','8163053889',
  '6203631824','6092187364','8163524112','8164534199',
  '8164902580','8165199915','8165200875','8166685543',
  '8168821000','8168074466','9132845401','9136384597',
  '9415677841'
]);

function normalizePhone(raw) {
  // Strip everything non-digit, take last 10 digits
  return raw.replace(/\D/g, '').slice(-10);
}

// ────────────────────────────────────────────────────────────
// POST /chatogg/reply
// Twilio calls this when any group member sends a text back.
// Configure this URL in your Twilio phone number's
// "A MESSAGE COMES IN" webhook field.
// ────────────────────────────────────────────────────────────
app.post('/chatogg/reply', (req, res) => {
  const fromRaw = req.body.From || '';
  const body    = (req.body.Body || '').trim();
  const phone   = normalizePhone(fromRaw);

  console.log(`[Twilio] Incoming from +1${phone}: "${body}"`);

  // Only accept replies from known group members
  if (!GROUP_NUMBERS.has(phone)) {
    console.log(`  → Ignored (not in group): ${phone}`);
    res.set('Content-Type', 'text/xml');
    return res.send('<Response></Response>');
  }

  const reply = {
    phone,
    body,
    timestamp: Date.now(),
  };

  // Find the most recent active session (within last 5 min)
  const cutoff = Date.now() - 5 * 60 * 1000;
  let targetSession = null;
  let latestTime = 0;

  for (const [sessionId] of replySessions.entries()) {
    const t = parseInt(sessionId);
    if (t > cutoff && t > latestTime) {
      latestTime = t;
      targetSession = sessionId;
    }
  }

  if (!targetSession) {
    console.log('  → No active session to attach reply to');
    res.set('Content-Type', 'text/xml');
    return res.send('<Response></Response>');
  }

  const sessionReplies = replySessions.get(targetSession);

  // Deduplicate: ignore if this phone already replied in this session
  if (sessionReplies.some(r => r.phone === phone)) {
    console.log(`  → Duplicate reply from ${phone}, ignoring`);
    res.set('Content-Type', 'text/xml');
    return res.send('<Response></Response>');
  }

  // Only collect first 3 replies
  if (sessionReplies.length >= 3) {
    console.log('  → Already have 3 replies, ignoring');
    res.set('Content-Type', 'text/xml');
    return res.send('<Response></Response>');
  }

  sessionReplies.push(reply);
  console.log(`  → Stored reply #${sessionReplies.length} for session ${targetSession}`);

  // Push to all SSE clients listening on this session
  const clients = sseClients.get(targetSession) || [];
  const event = JSON.stringify(reply);
  clients.forEach(clientRes => {
    try {
      clientRes.write(`data: ${event}\n\n`);
    } catch (e) {
      console.warn('SSE write error:', e.message);
    }
  });

  // Twilio requires an XML response (empty = no auto-reply)
  res.set('Content-Type', 'text/xml');
  res.send('<Response></Response>');
});

// ────────────────────────────────────────────────────────────
// POST /chatogg/session
// Frontend calls this to create a new reply session.
// Returns a sessionId the frontend uses for SSE.
// ────────────────────────────────────────────────────────────
app.post('/chatogg/session', (req, res) => {
  const sessionId = String(Date.now());
  replySessions.set(sessionId, []);
  sseClients.set(sessionId, []);
  console.log(`[Session] Created: ${sessionId}`);
  res.json({ sessionId });
});

// ────────────────────────────────────────────────────────────
// GET /chatogg/stream/:sessionId
// Frontend connects here for Server-Sent Events.
// Replies are pushed in real-time as they arrive from Twilio.
// ────────────────────────────────────────────────────────────
app.get('/chatogg/stream/:sessionId', (req, res) => {
  const { sessionId } = req.params;

  if (!replySessions.has(sessionId)) {
    return res.status(404).json({ error: 'Session not found' });
  }

  // SSE headers
  res.set({
    'Content-Type':  'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection':    'keep-alive',
    'X-Accel-Buffering': 'no', // Important for nginx proxies
  });
  res.flushHeaders();

  // Send any replies that already came in before SSE connected
  const existing = replySessions.get(sessionId) || [];
  existing.forEach(reply => {
    res.write(`data: ${JSON.stringify(reply)}\n\n`);
  });

  // Register this client
  const clients = sseClients.get(sessionId) || [];
  clients.push(res);
  sseClients.set(sessionId, clients);

  console.log(`[SSE] Client connected to session ${sessionId} (${clients.length} total)`);

  // Heartbeat every 20s to keep connection alive through proxies
  const heartbeat = setInterval(() => {
    try { res.write(': heartbeat\n\n'); } catch {}
  }, 20000);

  // Cleanup on disconnect
  req.on('close', () => {
    clearInterval(heartbeat);
    const list = sseClients.get(sessionId) || [];
    const idx = list.indexOf(res);
    if (idx > -1) list.splice(idx, 1);
    console.log(`[SSE] Client disconnected from session ${sessionId}`);
  });
});

// ── Serve ChatOGG frontend at root ──
const CHATOGG_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChatOGG — Old Guy Group</title>
<link href="https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;0,900;1,400&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #1a1208;
    --surface: #231a0d;
    --surface2: #2e2210;
    --border: #5a3e1b;
    --border-light: #7a5a2a;
    --gold: #c9922a;
    --gold-bright: #e8b84b;
    --gold-dim: #7a5510;
    --cream: #f0e6c8;
    --cream-dim: #b8a882;
    --green: #4a8c3f;
    --green-bright: #6db862;
    --red: #8c3f3f;
    --text: #e8dfc0;
    --text-dim: #9a8a65;
    --phone-blue: #5a9adf;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Courier Prime', monospace;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse at 15% 15%, rgba(201,146,42,0.07) 0%, transparent 55%),
      radial-gradient(ellipse at 85% 85%, rgba(201,146,42,0.04) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  .app {
    width: 100%;
    max-width: 800px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    position: relative;
    z-index: 1;
    padding: 0 18px 36px;
  }

  /* ── HEADER ── */
  header {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 28px 0 22px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
    position: relative;
  }

  header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 100px; height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent);
  }

  .logo-svg {
    width: 74px; height: 74px; flex-shrink: 0;
    filter: drop-shadow(0 0 14px rgba(201,146,42,0.45));
    animation: bob 3.5s ease-in-out infinite;
  }
  @keyframes bob {
    0%,100% { transform: translateY(0) rotate(-1deg); }
    50%      { transform: translateY(-4px) rotate(1deg); }
  }

  .brand-name {
    font-family: 'Merriweather', serif;
    font-weight: 900;
    font-size: 2.1rem;
    color: var(--gold-bright);
    letter-spacing: -0.5px;
    line-height: 1;
    text-shadow: 0 2px 16px rgba(201,146,42,0.35);
  }

  .brand-tagline {
    font-size: 0.68rem;
    color: var(--text-dim);
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-top: 5px;
  }

  .status-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background: var(--green-bright);
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s ease-in-out infinite;
  }
  @keyframes pulse {
    0%,100% { opacity:1; box-shadow: 0 0 0 0 rgba(109,184,98,.5); }
    50%      { opacity:.7; box-shadow: 0 0 0 5px rgba(109,184,98,0); }
  }

  .members-badge {
    margin-left: auto;
    text-align: right;
    font-size: 0.65rem;
    color: var(--text-dim);
    line-height: 1.7;
  }
  .members-count {
    font-family: 'Merriweather', serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--gold);
    display: block;
  }

  /* ── CONFIG ── */
  .config-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    background: none;
    border: none;
    color: var(--text-dim);
    font-family: 'Courier Prime', monospace;
    font-size: 0.7rem;
    cursor: pointer;
    padding: 4px 0;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    transition: color 0.2s;
    margin-bottom: 8px;
  }
  .config-toggle:hover { color: var(--gold); }
  .config-toggle .arr { transition: transform .2s; font-size:.58rem; }
  .config-toggle.open .arr { transform: rotate(90deg); }

  .config-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 18px;
    margin-bottom: 16px;
    display: none;
    flex-direction: column;
    gap: 13px;
  }
  .config-panel.visible { display: flex; }

  .config-row { display: flex; gap: 12px; }
  .config-field { flex: 1; display: flex; flex-direction: column; gap: 5px; }
  .config-label { font-size: 0.63rem; color: var(--text-dim); text-transform: uppercase; letter-spacing:.12em; }

  .config-input {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 3px;
    color: var(--text);
    font-family: 'Courier Prime', monospace;
    font-size: 0.82rem;
    padding: 7px 10px;
    transition: border-color 0.2s;
    width: 100%;
  }
  .config-input:focus { outline: none; border-color: var(--gold); }

  .config-note {
    font-size: 0.67rem;
    color: var(--text-dim);
    font-style: italic;
    line-height: 1.6;
    padding: 10px 12px;
    background: rgba(201,146,42,.05);
    border: 1px solid var(--border);
    border-radius: 3px;
  }

  .demo-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.68rem;
    color: var(--text-dim);
    cursor: pointer;
  }
  .demo-row input { cursor: pointer; accent-color: var(--gold); }

  /* ── CHAT AREA ── */
  .chat-container {
    flex: 1;
    min-height: 360px;
    max-height: 500px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 24px;
    margin-bottom: 18px;
    overflow-y: auto;
    scroll-behavior: smooth;
  }

  /* Placeholder */
  .chat-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 290px;
    gap: 14px;
    opacity: 0.45;
    text-align: center;
  }
  .chat-placeholder p {
    font-size: 0.82rem;
    color: var(--text-dim);
    font-style: italic;
    line-height: 1.8;
  }

  /* Query */
  .query-wrap {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 22px;
    animation: slide-r 0.3s ease;
  }
  @keyframes slide-r { from { opacity:0; transform:translateX(14px); } to { opacity:1; transform:translateX(0); } }

  .query-bubble {
    background: var(--gold-dim);
    border: 1px solid var(--gold);
    border-radius: 18px 18px 4px 18px;
    padding: 13px 17px;
    max-width: 68%;
    font-size: 0.92rem;
    line-height: 1.55;
  }
  .query-bubble .qlabel {
    font-size: 0.62rem;
    color: var(--gold-bright);
    text-transform: uppercase;
    letter-spacing: .12em;
    margin-bottom: 5px;
  }

  /* Waiting header */
  .waiting-row {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.63rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: .15em;
    margin-bottom: 14px;
  }
  .waiting-row::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }
  .wait-dots span {
    display: inline-block;
    width: 6px; height: 6px;
    background: var(--gold);
    border-radius: 50%;
    margin: 0 2px;
    animation: bdot 1.2s ease-in-out infinite;
  }
  .wait-dots span:nth-child(2) { animation-delay:.15s; }
  .wait-dots span:nth-child(3) { animation-delay:.3s; }
  @keyframes bdot {
    0%,80%,100% { transform:scale(.65); opacity:.35; }
    40%          { transform:scale(1);   opacity:1;   }
  }

  /* Reply bubble — streams in one at a time */
  .reply-bubble {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-bottom: 14px;
    animation: slide-l 0.4s cubic-bezier(.22,.68,0,1.2) backwards;
  }
  @keyframes slide-l {
    from { opacity:0; transform:translateX(-14px) scale(.97); }
    to   { opacity:1; transform:translateX(0) scale(1); }
  }

  .reply-avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: var(--surface2);
    border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem;
    flex-shrink: 0;
  }

  .reply-meta {
    font-size: 0.6rem;
    color: var(--text-dim);
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .reply-num { color: var(--phone-blue); }
  .reply-rank {
    background: var(--gold-dim);
    color: var(--gold-bright);
    font-size: 0.58rem;
    text-transform: uppercase;
    letter-spacing: .1em;
    padding: 1px 6px;
    border-radius: 2px;
  }

  .reply-text {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px 18px 18px 18px;
    padding: 12px 16px;
    font-size: 0.9rem;
    line-height: 1.65;
    max-width: 520px;
  }

  /* Typing indicator — shown while waiting for each reply */
  .typing-bubble {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 14px;
    animation: fade-in .3s ease;
  }
  @keyframes fade-in { from{opacity:0;} to{opacity:1;} }

  .typing-avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: var(--surface2);
    border: 1px dashed var(--border-light);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    opacity: 0.6;
  }

  .typing-body {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px 18px 18px 18px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.75rem;
    color: var(--text-dim);
    font-style: italic;
  }

  /* Done banner */
  .done-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.63rem;
    color: var(--green-bright);
    text-transform: uppercase;
    letter-spacing: .15em;
    margin-top: 8px;
    animation: fade-in .4s ease;
  }
  .done-banner::before, .done-banner::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--green), transparent);
  }

  /* Error */
  .error-box {
    background: rgba(140,63,63,.2);
    border: 1px solid var(--red);
    border-radius: 4px;
    padding: 13px 16px;
    font-size: 0.84rem;
    color: #e08080;
    margin-bottom: 16px;
    animation: fade-in .3s ease;
  }
  .error-box strong {
    display: block;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin-bottom: 4px;
  }

  /* ── INPUT ── */
  .input-wrapper {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    margin-bottom: 8px;
  }

  .prompt-textarea {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    font-family: 'Merriweather', serif;
    font-size: 0.95rem;
    padding: 14px 16px;
    resize: none;
    min-height: 56px;
    max-height: 180px;
    line-height: 1.6;
    transition: border-color .2s, box-shadow .2s;
  }
  .prompt-textarea:focus {
    outline: none;
    border-color: var(--gold);
    box-shadow: 0 0 0 2px rgba(201,146,42,.12);
  }
  .prompt-textarea::placeholder { color: var(--text-dim); font-style: italic; }
  .prompt-textarea:disabled { opacity: .5; }

  .send-btn {
    background: var(--gold);
    color: var(--bg);
    border: none;
    border-radius: 4px;
    padding: 0 22px;
    height: 56px;
    font-family: 'Courier Prime', monospace;
    font-weight: 700;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: .13em;
    cursor: pointer;
    transition: background .2s, transform .1s;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .send-btn:hover:not(:disabled) { background: var(--gold-bright); }
  .send-btn:active:not(:disabled) { transform: scale(.97); }
  .send-btn:disabled { background: var(--gold-dim); cursor: not-allowed; opacity:.6; }

  .input-footer {
    display: flex;
    justify-content: space-between;
    font-size: 0.61rem;
    color: var(--text-dim);
  }
  .kbd {
    display: inline-block;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 1px 5px;
  }
  .mode-pill {
    font-weight: 700;
    letter-spacing: .05em;
  }

  footer {
    margin-top: 28px;
    padding-top: 18px;
    border-top: 1px solid var(--border);
    font-size: 0.6rem;
    color: var(--text-dim);
    text-align: center;
    line-height: 1.9;
  }
  footer strong { color: var(--gold); }

  ::-webkit-scrollbar { width: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>
<div class="app">

  <!-- HEADER -->
  <header>
    <svg class="logo-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <!-- Body -->
      <ellipse cx="50" cy="79" rx="18" ry="13" fill="#5a3e1b"/>
      <ellipse cx="50" cy="77" rx="16" ry="11" fill="#7a5a2a"/>
      <!-- Suspenders -->
      <line x1="42" y1="68" x2="44" y2="88" stroke="#c9922a" stroke-width="2.5"/>
      <line x1="58" y1="68" x2="56" y2="88" stroke="#c9922a" stroke-width="2.5"/>
      <line x1="43" y1="77" x2="57" y2="77" stroke="#c9922a" stroke-width="2"/>
      <!-- Neck -->
      <rect x="45" y="55" width="10" height="10" rx="3" fill="#d4a055"/>
      <!-- Head -->
      <ellipse cx="50" cy="44" rx="20" ry="22" fill="#d4a055"/>
      <!-- Bald top -->
      <ellipse cx="50" cy="26" rx="19" ry="12" fill="#c9922a"/>
      <!-- Wispy white hair -->
      <path d="M30 37 Q25 27 31 21 Q33 31 36 35" fill="white" opacity=".9"/>
      <path d="M70 37 Q75 27 69 21 Q67 31 64 35" fill="white" opacity=".9"/>
      <!-- Ears -->
      <ellipse cx="29" cy="45" rx="5.5" ry="7" fill="#c9922a"/>
      <ellipse cx="71" cy="45" rx="5.5" ry="7" fill="#c9922a"/>
      <path d="M27.5 41 Q25.5 45 27.5 49" stroke="#a06818" stroke-width="1.2" fill="none"/>
      <path d="M72.5 41 Q74.5 45 72.5 49" stroke="#a06818" stroke-width="1.2" fill="none"/>
      <!-- Eyes -->
      <ellipse cx="40" cy="43" rx="5" ry="3.8" fill="white"/>
      <ellipse cx="60" cy="43" rx="5" ry="3.8" fill="white"/>
      <circle cx="41" cy="43" r="2.4" fill="#2a1800"/>
      <circle cx="61" cy="43" r="2.4" fill="#2a1800"/>
      <circle cx="42" cy="42" r=".8" fill="white"/>
      <circle cx="62" cy="42" r=".8" fill="white"/>
      <!-- Bushy white eyebrows -->
      <path d="M33 38 Q40 33 47 36" stroke="white" stroke-width="4" stroke-linecap="round" fill="none"/>
      <path d="M53 36 Q60 33 67 38" stroke="white" stroke-width="4" stroke-linecap="round" fill="none"/>
      <!-- Nose -->
      <ellipse cx="50" cy="52" rx="6" ry="5" fill="#c08030"/>
      <circle cx="47" cy="53.5" r="2" fill="#a06020"/>
      <circle cx="53" cy="53.5" r="2" fill="#a06020"/>
      <!-- Smile -->
      <path d="M40 59 Q50 66 60 59" stroke="#7a4a10" stroke-width="2.2" fill="none" stroke-linecap="round"/>
      <rect x="46" y="59" width="4.5" height="5" rx="1" fill="white"/>
      <rect x="49.5" y="59" width="4.5" height="5" rx="1" fill="white"/>
      <!-- Wrinkles -->
      <path d="M33 47 Q35 51 33 55" stroke="#a06818" stroke-width="1" fill="none" opacity=".55"/>
      <path d="M67 47 Q65 51 67 55" stroke="#a06818" stroke-width="1" fill="none" opacity=".55"/>
      <path d="M38 30 Q50 27 62 30" stroke="#a06818" stroke-width=".9" fill="none" opacity=".4"/>
      <!-- Phone in hand -->
      <rect x="62" y="71" width="10" height="17" rx="2" fill="#1a1a1a" stroke="#444" stroke-width=".6"/>
      <rect x="63.5" y="72.5" width="7" height="12" rx="1" fill="#3a7abd" opacity=".85"/>
      <line x1="65" y1="75" x2="69.5" y2="75" stroke="white" stroke-width=".9" opacity=".7"/>
      <line x1="65" y1="77" x2="69.5" y2="77" stroke="white" stroke-width=".9" opacity=".5"/>
      <line x1="65" y1="79" x2="67.5" y2="79" stroke="white" stroke-width=".9" opacity=".35"/>
    </svg>

    <div>
      <div class="brand-name">ChatOGG</div>
      <div class="brand-tagline">
        <span class="status-dot"></span>Old Guy Group · Est. Since Forever
      </div>
    </div>

    <div class="members-badge">
      <span class="members-count">17</span>
      old guys on call
    </div>
  </header>

  <!-- Hidden credentials -->
  <div style="display:none">
    <input id="sid" value="AC238597b7e39e0b2df6082b89ee752021"/>
    <input id="tok" value="b45912596644158e20fa5e18d7273481"/>
    <input id="from" value="+18557746017"/>
    <input id="backendUrl" value="https://chatogg-server-production.up.railway.app"/>
    <input type="checkbox" id="demoChk" checked onchange="updateMode()">
  </div>

  <!-- GO LIVE button -->
  <div id="goLiveBar" style="margin-bottom:16px;text-align:center;">
    <button id="goLiveBtn" onclick="goLive()" style="background:var(--surface);border:1px solid var(--border);color:var(--text-dim);font-family:'Courier Prime',monospace;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.15em;padding:8px 22px;border-radius:3px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.borderColor='var(--gold)';this.style.color='var(--gold)'" onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--text-dim)'">
      🟢 Switch to Live SMS
    </button>
  </div>

  <!-- CHAT -->
  <div class="chat-container" id="chat">
    <div class="chat-placeholder" id="placeholder">
      <svg width="52" height="52" viewBox="0 0 48 48" fill="none">
        <path d="M8 8h32a4 4 0 014 4v20a4 4 0 01-4 4H14l-8 8V12a4 4 0 014-4z" stroke="#c9922a" stroke-width="2"/>
        <path d="M16 20h16M16 26h10" stroke="#c9922a" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <p>
        Ask the Old Guys anything.<br>
        First 3 replies appear as they come in.<br><br>
        <em>*Wisdom not guaranteed. Tennis tips are.</em>
      </p>
    </div>
  </div>

  <!-- INPUT -->
  <div class="input-wrapper">
    <textarea
      class="prompt-textarea"
      id="inp"
      placeholder="Ask the group chat something..."
      rows="2"
      onkeydown="handleKey(event)"
      oninput="autoResize(this)"
    ></textarea>
    <button class="send-btn" id="sendBtn" onclick="send()">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M1 1l14 7-14 7V9l10-1L1 7V1z"/></svg>
      Send
    </button>
  </div>
  <div class="input-footer">
    <span><span class="kbd">Enter</span> to send &nbsp;·&nbsp; <span class="kbd">Shift+Enter</span> new line</span>
    <span class="mode-pill" id="modePill" style="color:var(--gold)">● Demo Mode</span>
  </div>
  <div id="liveConfirm" style="display:none;margin-top:10px;background:var(--surface);border:1px solid var(--gold);border-radius:4px;padding:14px 16px;font-size:0.78rem;line-height:1.7;">
    <strong style="color:var(--gold-bright);display:block;margin-bottom:6px;">🟢 Switching to Live SMS</strong>
    Real texts will be sent to all 17 members. Your Twilio number is verified and the backend is running.<br><br>
    <div style="display:flex;gap:10px;margin-top:4px;">
      <button onclick="confirmLive()" style="background:var(--gold);color:var(--bg);border:none;border-radius:3px;padding:7px 18px;font-family:'Courier Prime',monospace;font-weight:700;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;cursor:pointer;">Yes, Go Live</button>
      <button onclick="cancelLive()" style="background:var(--surface2);color:var(--text-dim);border:1px solid var(--border);border-radius:3px;padding:7px 18px;font-family:'Courier Prime',monospace;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;cursor:pointer;">Cancel</button>
    </div>
  </div>

  <footer>
    <strong>ChatOGG</strong> — Collective wisdom of <strong>17</strong> legendary old guys ·
    SMS via Twilio · Streaming replies via SSE ·
    Opinions may include unsolicited advice, weather observations & tennis hot takes
  </footer>
</div>

<script>
// ── Constants ──
const GROUP_NUMBERS = [
  '8168359882','8167191640','8166782527','8163053889',
  '6203631824','6092187364','8163524112','8164534199',
  '8164902580','8165199915','8165200875','8166685543',
  '8168821000','8168074466','9132845401','9136384597',
  '9415677841'
];

const AVATARS  = ['👴','🧓','👨‍🦳','👨‍🦲','🎩','🤠','👒','🪖','🎣','⛳'];
const RANKS    = ['🥇 First in','🥈 Second in','🥉 Third in'];

// ── State ──
let isDemoMode = true;
let busy = false;
let currentSSE = null;

// ── Persist config ──
function saveCfg() {
  localStorage.setItem('chatogg_sid',     document.getElementById('sid').value);
  localStorage.setItem('chatogg_tok',     document.getElementById('tok').value);
  localStorage.setItem('chatogg_from',    document.getElementById('from').value);
  localStorage.setItem('chatogg_backend', document.getElementById('backendUrl').value);
}
function loadCfg() {
  document.getElementById('sid').value        = localStorage.getItem('chatogg_sid')     || 'AC238597b7e39e0b2df6082b89ee752021';
  document.getElementById('tok').value        = localStorage.getItem('chatogg_tok')     || 'b45912596644158e20fa5e18d7273481';
  document.getElementById('from').value       = localStorage.getItem('chatogg_from')    || '+18557746017';
  document.getElementById('backendUrl').value = localStorage.getItem('chatogg_backend') || 'https://chatogg-server-production.up.railway.app';
}

function toggleCfg() {
  document.getElementById('cfgBtn').classList.toggle('open');
  document.getElementById('cfgPanel').classList.toggle('visible');
}

function updateMode() {
  isDemoMode = document.getElementById('demoChk').checked;
  const pill = document.getElementById('modePill');
  pill.textContent = isDemoMode ? '● Demo Mode' : '● Live SMS';
  pill.style.color = isDemoMode ? 'var(--gold)' : 'var(--green-bright)';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 180) + 'px';
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function fmtPhone(n) {
  return \`(\${n.slice(0,3)}) \${n.slice(3,6)}-\${n.slice(6)}\`;
}

function rndFrom(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

// ── UI helpers ──
function removePlaceholder() {
  const el = document.getElementById('placeholder');
  if (el) el.remove();
}

function chatEl() { return document.getElementById('chat'); }

function scrollBottom() {
  const c = chatEl();
  c.scrollTop = c.scrollHeight;
}

function appendQueryBubble(text) {
  removePlaceholder();
  const d = document.createElement('div');
  d.className = 'query-wrap';
  d.innerHTML = \`
    <div class="query-bubble">
      <div class="qlabel">📤 Inquiry to ChatOGG</div>
      \${esc(text)}
    </div>\`;
  chatEl().appendChild(d);
  scrollBottom();
}

function appendWaitingHeader() {
  const d = document.createElement('div');
  d.className = 'waiting-row';
  d.id = 'waitRow';
  d.innerHTML = \`
    Awaiting old guy wisdom &nbsp;
    <span class="wait-dots"><span></span><span></span><span></span></span>\`;
  chatEl().appendChild(d);
  scrollBottom();
}

function removeWaitingHeader() {
  const el = document.getElementById('waitRow');
  if (el) el.remove();
}

// Typing indicator (shown while waiting for each reply)
function addTypingIndicator(id) {
  const d = document.createElement('div');
  d.className = 'typing-bubble';
  d.id = \`typing-\${id}\`;
  d.innerHTML = \`
    <div class="typing-avatar">❓</div>
    <div class="typing-body">
      <span class="wait-dots"><span></span><span></span><span></span></span>
      someone is composing a reply…
    </div>\`;
  chatEl().appendChild(d);
  scrollBottom();
}

function removeTypingIndicator(id) {
  const el = document.getElementById(\`typing-\${id}\`);
  if (el) el.remove();
}

let replyCount = 0;

function appendReply(phone, body) {
  const rank  = replyCount;
  replyCount++;

  // Remove this slot's typing indicator
  removeTypingIndicator(rank);

  const now  = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  const d    = document.createElement('div');
  d.className = 'reply-bubble';
  d.style.animationDelay = '0ms'; // already timed by arrival

  d.innerHTML = \`
    <div class="reply-avatar">\${rndFrom(AVATARS)}</div>
    <div style="flex:1">
      <div class="reply-meta">
        <span class="reply-num">\${fmtPhone(phone)}</span>
        <span style="color:var(--text-dim)">\${now}</span>
        <span class="reply-rank">\${RANKS[rank] || \`#\${rank+1} in\`}</span>
      </div>
      <div class="reply-text">\${esc(body)}</div>
    </div>\`;

  chatEl().appendChild(d);
  scrollBottom();
}

function appendDone(count) {
  const d = document.createElement('div');
  d.className = 'done-banner';
  d.textContent = \`\${count} repl\${count===1?'y':'ies'} received\`;
  chatEl().appendChild(d);
  scrollBottom();
}

function appendError(msg) {
  removeWaitingHeader();
  // Remove any remaining typing indicators
  for (let i = 0; i < 3; i++) removeTypingIndicator(i);
  const d = document.createElement('div');
  d.className = 'error-box';
  d.innerHTML = \`<strong>⚠ Error</strong>\${esc(msg)}\`;
  chatEl().appendChild(d);
  scrollBottom();
}

function setLoading(on) {
  busy = on;
  document.getElementById('sendBtn').disabled = on;
  document.getElementById('inp').disabled = on;
  document.getElementById('sendBtn').innerHTML = on
    ? \`<span class="wait-dots" style="gap:3px"><span style="width:6px;height:6px;background:var(--bg);border-radius:50%;animation:bdot 1.2s ease-in-out infinite;display:inline-block"></span><span style="width:6px;height:6px;background:var(--bg);border-radius:50%;animation:bdot 1.2s ease-in-out .15s infinite;display:inline-block"></span><span style="width:6px;height:6px;background:var(--bg);border-radius:50%;animation:bdot 1.2s ease-in-out .3s infinite;display:inline-block"></span></span>\`
    : \`<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M1 1l14 7-14 7V9l10-1L1 7V1z"/></svg> Send\`;
}

// ── MAIN SEND ──
async function send() {
  if (busy) return;
  const inp = document.getElementById('inp');
  const prompt = inp.value.trim();
  if (!prompt) return;

  inp.value = '';
  inp.style.height = 'auto';
  replyCount = 0;

  setLoading(true);
  appendQueryBubble(prompt);
  appendWaitingHeader();

  // Stagger 3 typing indicators
  for (let i = 0; i < 3; i++) {
    setTimeout(() => addTypingIndicator(i), i * 600);
  }

  if (isDemoMode) {
    await runDemo(prompt);
  } else {
    await runLive(prompt);
  }

  setLoading(false);
}

// ── DEMO MODE ──
const demoReplies = [
  p => \`Back in my day we didn't need to ask. You just figured it out. But since you asked — "\${p.slice(0,30)}..." — my honest answer is: try the opposite of whatever you're doing.\`,
  () => \`I asked my doctor something similar. He said don't worry about it. I'm going with that.\`,
  p => \`\${p.split(' ').slice(0,4).join(' ')}... you know what, just call someone. That's what I do. Works every time.\`,
  () => \`My wife handles all of that. Couldn't tell ya. Ask her.\`,
  () => \`Great question. The answer is: it depends. Always has, always will.\`,
  () => \`I saw something about this on the news. Fox or CNN, one of 'em. They said something. Trust me.\`,
  () => \`You're overthinking it. Have a beer and sleep on it. Works for everything.\`,
  () => \`Classic situation. What you want to do is the OPPOSITE of what seems right. I've been saying this for years.\`,
  () => \`Handled something like this in '92. Took about 3 months. Hope you got time.\`,
  () => \`Ask Gary. Gary knows about these things. He's been right before.\`,
  () => \`I have a strong opinion on this but it would take too long to explain on text. I'll tell you at the next tennis match.\`,
  () => \`What kind of question is this? Are you doing okay? Call your mother.\`,
];

async function runDemo(prompt) {
  const used = new Set();
  const TIMEOUT_MS = 90_000;
  const start = Date.now();

  for (let i = 0; i < 3; i++) {
    if (Date.now() - start > TIMEOUT_MS) break;

    const delay = 1200 + Math.random() * 2200;
    await new Promise(r => setTimeout(r, delay));

    // Remove the typing indicator for this slot just before reply appears
    removeTypingIndicator(i);

    let phone;
    do { phone = GROUP_NUMBERS[Math.floor(Math.random() * GROUP_NUMBERS.length)]; }
    while (used.has(phone));
    used.add(phone);

    const replyFn = demoReplies[Math.floor(Math.random() * demoReplies.length)];
    appendReply(phone, replyFn(prompt));
  }

  removeWaitingHeader();
  appendDone(Math.min(3, replyCount));
}

// ── LIVE MODE via SSE ──
async function runLive(prompt) {
  const sid     = document.getElementById('sid').value.trim();
  const tok     = document.getElementById('tok').value.trim();
  const from    = document.getElementById('from').value.trim();
  const backend = document.getElementById('backendUrl').value.trim().replace(/\\/$/, '');

  if (!sid || !tok || !from || !backend) {
    appendError('Fill in all SMS Gateway Settings above: Twilio SID, Auth Token, From number, and your Backend Server URL.');
    return;
  }

  // 1. Create session on backend
  let sessionId;
  try {
    const r = await fetch(\`\${backend}/chatogg/session\`, { method: 'POST' });
    if (!r.ok) throw new Error(\`Session create failed: \${r.status}\`);
    const data = await r.json();
    sessionId = data.sessionId;
  } catch (e) {
    appendError(\`Could not reach backend server: \${e.message}\`);
    return;
  }

  // 2. Send SMS to all group members
  const body = \`Inquiry to ChatOGG: \${prompt}\`;
  let sentCount = 0;

  const sendAll = GROUP_NUMBERS.map(async num => {
    try {
      const fd = new URLSearchParams({ To: \`+1\${num}\`, From: from, Body: body });
      const r = await fetch(\`https://api.twilio.com/2010-04-01/Accounts/\${sid}/Messages.json\`, {
        method: 'POST',
        headers: {
          'Authorization': 'Basic ' + btoa(\`\${sid}:\${tok}\`),
          'Content-Type':  'application/x-www-form-urlencoded',
        },
        body: fd.toString(),
      });
      if (r.ok) sentCount++;
    } catch {}
  });

  await Promise.allSettled(sendAll);
  console.log(\`[ChatOGG] Sent to \${sentCount}/\${GROUP_NUMBERS.length} members\`);

  if (sentCount === 0) {
    appendError('Failed to send any texts. Double-check your Twilio SID, Auth Token, and From number.');
    for (let i = 0; i < 3; i++) removeTypingIndicator(i);
    return;
  }

  // 3. Open SSE stream and wait for replies
  await new Promise((resolve) => {
    const timeout = setTimeout(() => {
      sse.close();
      resolve();
    }, 90_000);

    const sse = new EventSource(\`\${backend}/chatogg/stream/\${sessionId}\`);
    currentSSE = sse;

    sse.onmessage = (e) => {
      try {
        const reply = JSON.parse(e.data);
        const phone = reply.phone.replace(/\\D/g,'').slice(-10);
        removeTypingIndicator(replyCount); // remove next slot's indicator
        appendReply(phone, reply.body);

        if (replyCount >= 3) {
          clearTimeout(timeout);
          sse.close();
          resolve();
        }
      } catch {}
    };

    sse.onerror = () => {
      // SSE errors are often just connection resets — let timeout handle it
    };
  });

  currentSSE = null;
  removeWaitingHeader();
  for (let i = replyCount; i < 3; i++) removeTypingIndicator(i);

  if (replyCount === 0) {
    appendError('No replies received within 90 seconds. The old guys might be on the tennis court.');
  } else {
    appendDone(replyCount);
  }
}

// ── Go Live ──
function goLive() {
  document.getElementById('liveConfirm').style.display = 'block';
  document.getElementById('goLiveBar').style.display = 'none';
}
function cancelLive() {
  document.getElementById('liveConfirm').style.display = 'none';
  document.getElementById('goLiveBar').style.display = 'block';
}
function confirmLive() {
  document.getElementById('demoChk').checked = false;
  updateMode();
  document.getElementById('liveConfirm').style.display = 'none';
  document.getElementById('goLiveBar').style.display = 'none';
  const pill = document.getElementById('modePill');
  pill.textContent = '🟢 Live SMS Active';
  pill.style.color = 'var(--green-bright)';
}

// ── Init ──
loadCfg();
updateMode();
</script>
</body>
</html>
`;

app.get('/', (req, res) => {
  res.set('Content-Type', 'text/html');
  res.send(CHATOGG_HTML);
});

// ── Health check ──
app.get('/health', (req, res) => res.json({ status: 'ok', sessions: replySessions.size }));

app.listen(PORT, () => {
  console.log(`\n🧓 ChatOGG server running on port ${PORT}`);
  console.log(`   Webhook URL (set in Twilio): https://YOUR_DOMAIN/chatogg/reply`);
  console.log(`   Health check: http://localhost:${PORT}/health\n`);
});
