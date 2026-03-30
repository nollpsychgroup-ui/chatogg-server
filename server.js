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

// ── Health check ──
app.get('/health', (req, res) => res.json({ status: 'ok', sessions: replySessions.size }));

app.listen(PORT, () => {
  console.log(`\n🧓 ChatOGG server running on port ${PORT}`);
  console.log(`   Webhook URL (set in Twilio): https://YOUR_DOMAIN/chatogg/reply`);
  console.log(`   Health check: http://localhost:${PORT}/health\n`);
});
