// ═══════════════════════════════════════════════════════════════
//  Bambu Lab Print Farm — MQTT Bridge
//  Connects to all 4 printers via MQTT, serves data to the
//  dashboard via WebSocket on localhost:3000
// ═══════════════════════════════════════════════════════════════

const mqtt = require('mqtt');
const { WebSocketServer } = require('ws');

// ── CONFIGURATION ──────────────────────────────────────────────
// Edit these 4 printers with your own values
const PRINTERS = [
  { id: 0, name: "Printer 1", ip: "192.168.10.102", serial: "00M09A3B2700035", code: "cfda32ee" },
  { id: 1, name: "Printer 2", ip: "192.168.10.106", serial: "00M09D482400921", code: "6e144d6b" },
  { id: 2, name: "Printer 3", ip: "192.168.10.103", serial: "00M09D490201428", code: "fdc70620" },
  { id: 3, name: "Printer 4", ip: "192.168.10.104", serial: "00M09C431200531", code: "f73bb784" },
];

const WS_PORT = 3000; // Port the dashboard connects to
// ──────────────────────────────────────────────────────────────

// Holds latest known state for each printer
const printerStates = PRINTERS.map(p => ({
  id: p.id,
  name: p.name,
  ip: p.ip,
  status: 'connecting',
  file: '',
  progress: 0,
  remaining: 0,
  elapsed: 0,
  nozzle: 0,
  nozzle_target: 0,
  bed: 0,
  bed_target: 0,
  layer: 0,
  total_layers: 0,
  hms: [],
  print_error: 0,
  error: null,
  last_update: null,
}));

// Active WebSocket clients (dashboard browser tabs)
const wsClients = new Set();

// ── WebSocket server ───────────────────────────────────────────
const wss = new WebSocketServer({ port: WS_PORT });

wss.on('listening', () => {
  console.log(`\n✓ WebSocket server running on ws://localhost:${WS_PORT}`);
  console.log('  Open dashboard.html in your browser\n');
});

wss.on('connection', (ws) => {
  wsClients.add(ws);
  console.log(`  Dashboard connected (${wsClients.size} client(s))`);

  // Send current state immediately on connect
  ws.send(JSON.stringify({ type: 'full_state', printers: printerStates }));

  ws.on('close', () => {
    wsClients.delete(ws);
    console.log(`  Dashboard disconnected (${wsClients.size} client(s))`);
  });
});

function broadcast(msg) {
  const data = JSON.stringify(msg);
  for (const client of wsClients) {
    if (client.readyState === 1) client.send(data);
  }
}

// ── Connect to each printer via MQTT ──────────────────────────
PRINTERS.forEach(printer => {
  const mqttUrl = `mqtts://${printer.ip}:8883`;

  console.log(`Connecting to ${printer.name} at ${mqttUrl} ...`);

  const client = mqtt.connect(mqttUrl, {
    username: 'bblp',
    password: printer.code,
    clientId: `dashboard_${printer.serial}_${Date.now()}`,
    rejectUnauthorized: false, // Bambu uses self-signed certs
    reconnectPeriod: 5000,     // Retry every 5s if disconnected
    connectTimeout: 10000,
  });

  client.on('connect', () => {
    console.log(`✓ ${printer.name} connected`);
    printerStates[printer.id].status = 'idle';
    printerStates[printer.id].error = null;

    // Subscribe to the printer's report topic
    const topic = `device/${printer.serial}/report`;
    client.subscribe(topic, (err) => {
      if (err) console.error(`  Failed to subscribe to ${printer.name}:`, err.message);
      else console.log(`  Subscribed to ${topic}`);
    });

    // Request a full status update immediately
    const requestTopic = `device/${printer.serial}/request`;
    client.publish(requestTopic, JSON.stringify({
      pushing: { sequence_id: "0", command: "pushall" }
    }));

    broadcast({ type: 'printer_update', printer: printerStates[printer.id] });
  });

  client.on('message', (topic, message) => {
    try {
      const data = JSON.parse(message.toString());
      const print = data.print;
      if (!print) return;

      const state = printerStates[printer.id];
      const prev_status = state.status;

      // Only update status when gcode_state is present — partial messages omit it
      if (print.gcode_state !== undefined) {
        const gcode = print.gcode_state.toUpperCase();
        if (['RUNNING', 'PREPARE', 'SLICING'].includes(gcode)) state.status = 'printing';
        else if (gcode === 'PAUSE') state.status = 'paused';
        else if (gcode === 'FAILED') state.status = 'error';
        else if (['FINISH', 'IDLE'].includes(gcode)) state.status = 'idle';
      }


      // Progress & time
      if (print.mc_percent !== undefined) state.progress = Math.round(print.mc_percent);
      if (print.mc_remaining_time !== undefined) state.remaining = print.mc_remaining_time * 60;

      // Estimate elapsed from progress + remaining
      if (state.progress > 0 && state.remaining > 0) {
        const total = state.remaining / (1 - state.progress / 100);
        state.elapsed = Math.round(total * (state.progress / 100));
      }

      // Temperatures
      if (print.nozzle_temper !== undefined) state.nozzle = Math.round(print.nozzle_temper);
      if (print.nozzle_target_temper !== undefined) state.nozzle_target = Math.round(print.nozzle_target_temper);
      if (print.bed_temper !== undefined) state.bed = Math.round(print.bed_temper);
      if (print.bed_target_temper !== undefined) state.bed_target = Math.round(print.bed_target_temper);

      // Layers
      if (print.layer_num !== undefined) state.layer = print.layer_num;
      if (print.total_layer_num !== undefined) state.total_layers = print.total_layer_num;

      // File name
      if (print.subtask_name) state.file = print.subtask_name;
      else if (print.gcode_file) state.file = print.gcode_file.split('/').pop();

      // Pause / error reason codes
      if (print.hms !== undefined) state.hms = print.hms;
      if (print.print_error !== undefined) state.print_error = print.print_error;

      state.last_update = new Date().toISOString();
      state.error = null;

      if (prev_status !== state.status) {
        console.log(`  ${printer.name}: ${prev_status} → ${state.status}`);
      }

      broadcast({ type: 'printer_update', printer: state });

    } catch (e) {
      // Silently ignore malformed messages
    }
  });

  client.on('error', (err) => {
    console.error(`✗ ${printer.name} error:`, err.message);
    printerStates[printer.id].status = 'error';
    printerStates[printer.id].error = err.message.includes('ECONNREFUSED')
      ? 'Connection refused — check IP'
      : err.message.includes('auth')
        ? 'Auth failed — check access code'
        : err.message;
    broadcast({ type: 'printer_update', printer: printerStates[printer.id] });
  });

  client.on('offline', () => {
    console.log(`  ${printer.name} offline, retrying...`);
    printerStates[printer.id].status = 'connecting';
    broadcast({ type: 'printer_update', printer: printerStates[printer.id] });
  });
});

// ── Graceful shutdown ──────────────────────────────────────────
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  wss.close();
  process.exit(0);
});

console.log('━'.repeat(50));
console.log('  Bambu Lab Print Farm Dashboard — Bridge');
console.log('━'.repeat(50));
