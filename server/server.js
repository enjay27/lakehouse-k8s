// ============================================================
// Polaris Webhook Listener Server
// Accepts: JSON, plain text, Kafka REST Proxy format
//
// Endpoints:
//   POST /sms        → SMS alert webhook
//   POST /messenger  → Messenger alert webhook
//   GET  /history    → last 20 received payloads
//   GET  /           → health check
//
// Run: node server.js
// ============================================================

const express = require('express');
const app = express();
const PORT = 3000;

const history = { sms: [], messenger: [] };
const MAX_HISTORY = 20;

// ── Middleware — accept any body format ───────────────────────
app.use((req, res, next) => {
  // Try JSON first
  express.json({ type: '*/*' })(req, res, (err) => {
    if (err) {
      // Fallback: plain text
      express.text({ type: '*/*' })(req, res, next);
    } else {
      next();
    }
  });
});

// ── Colors ───────────────────────────────────────────────────
const c = {
  reset:  '\x1b[0m',
  red:    '\x1b[31m',
  yellow: '\x1b[33m',
  green:  '\x1b[32m',
  cyan:   '\x1b[36m',
  bold:   '\x1b[1m',
  dim:    '\x1b[2m',
};
const clr = (text, col) => `${c[col]}${text}${c.reset}`;
const div = () => console.log(clr('─'.repeat(60), 'dim'));

// ── Parse body — handles all formats ─────────────────────────
function parseBody(body) {
  // Already parsed object
  if (body && typeof body === 'object') return body;

  // Plain text string → try JSON parse
  if (typeof body === 'string') {
    try { return JSON.parse(body); } catch (_) {}
    return { raw: body };
  }

  return {};
}

// ── Extract Kafka REST record value ──────────────────────────
function extractRecord(body) {
  // Kafka REST Proxy format:
  // { value_schema_id, records: [{ value: { noti_phone, ... } }] }
  if (body && body.records && Array.isArray(body.records)) {
    return body.records[0]?.value || null;
  }
  return null;
}

// ── Print webhook to terminal ────────────────────────────────
function printWebhook(channel, rawBody, req) {
  const now = new Date().toISOString();
  console.log('');
  div();
  console.log(
      clr('📨 WEBHOOK RECEIVED', 'bold') +
      clr(` [${channel.toUpperCase()}]`, 'cyan') +
      clr(` ${now}`, 'dim')
  );
  console.log(clr(`From:     ${req.ip}`, 'dim'));
  console.log(clr(`Type:     ${req.headers['content-type'] || 'unknown'}`, 'dim'));

  const body = parseBody(rawBody);

  // Plain text (OpenSearch test button)
  if (body.raw) {
    console.log('');
    console.log(clr('  ⚠️  Plain text body (OpenSearch test message):', 'yellow'));
    console.log(`  ${body.raw}`);
    div();
    return body;
  }

  // Kafka REST Proxy / company SMS format
  const record = extractRecord(body);
  if (record) {
    const level = (record.noti_title || '').includes('ERROR') ? 'red'
        : (record.noti_title || '').includes('WARN')  ? 'yellow'
            : 'green';
    console.log('');
    console.log(clr('  Schema ID : ', 'dim') + (body.value_schema_id || '-'));
    console.log(clr('  Phone     : ', 'dim') + (record.noti_phone  || '-'));
    console.log(clr('  Title     : ', 'dim') + clr(record.noti_title   || '-', level));
    console.log(clr('  Content   : ', 'dim') + clr(record.noti_content || '-', level));
    console.log(clr('  Date      : ', 'dim') + (record.dt || '-'));
  }

  // Full JSON
  console.log('');
  console.log(clr('  Full JSON:', 'dim'));
  const pretty = JSON.stringify(body, null, 2);
  pretty.split('\n').forEach(line => console.log('  ' + line));
  div();

  return body;
}

// ── POST /sms ─────────────────────────────────────────────────
app.post('/sms', (req, res) => {
  const body = printWebhook('sms', req.body, req);
  history.sms.unshift({ receivedAt: new Date().toISOString(), body });
  if (history.sms.length > MAX_HISTORY) history.sms.length = MAX_HISTORY;
  res.status(200).json({ status: 'received', channel: 'sms' });
});

// ── POST /messenger ───────────────────────────────────────────
app.post('/messenger', (req, res) => {
  const body = printWebhook('messenger', req.body, req);
  history.messenger.unshift({ receivedAt: new Date().toISOString(), body });
  if (history.messenger.length > MAX_HISTORY) history.messenger.length = MAX_HISTORY;
  res.status(200).json({ status: 'received', channel: 'messenger' });
});

// ── GET /history ──────────────────────────────────────────────
app.get('/history', (req, res) => {
  const ch = req.query.channel;
  if (ch && history[ch]) {
    return res.json({ channel: ch, count: history[ch].length, items: history[ch] });
  }
  res.json({
    sms:       { count: history.sms.length,       items: history.sms },
    messenger: { count: history.messenger.length, items: history.messenger },
  });
});

// ── GET / ─────────────────────────────────────────────────────
app.get('/', (req, res) => {
  res.json({
    status: 'running',
    service: 'polaris-webhook-server',
    accepts: ['application/json', 'application/vnd.kafka.avro.v2+json', 'text/plain'],
    endpoints: {
      'POST /sms':       'SMS alert (Kafka REST or JSON)',
      'POST /messenger': 'Messenger alert',
      'GET  /history':   'Last 20 payloads',
    },
    history_count: { sms: history.sms.length, messenger: history.messenger.length },
  });
});

// ── Start ─────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log('');
  console.log(clr('═'.repeat(60), 'cyan'));
  console.log(clr('  Polaris Webhook Listener Server', 'bold'));
  console.log(clr('═'.repeat(60), 'cyan'));
  console.log(clr('  Port    : ', 'dim') + PORT);
  console.log(clr('  Accepts : ', 'dim') + 'JSON / Kafka REST / plain text');
  console.log('');
  console.log(clr('  POST ', 'cyan') + `http://localhost:${PORT}/sms`);
  console.log(clr('  POST ', 'cyan') + `http://localhost:${PORT}/messenger`);
  console.log(clr('  GET  ', 'cyan') + `http://localhost:${PORT}/history`);
  console.log('');
  console.log(clr('  OpenSearch → http://host.docker.internal:3000/sms', 'yellow'));
  console.log(clr('═'.repeat(60), 'cyan'));
});