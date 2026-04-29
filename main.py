#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#  Bambu Lab Print Farm — MQTT Bridge
#  Connects to all 4 printers via MQTT, serves data to the
#  dashboard via WebSocket on 0.0.0.0:3000
#
#  Dependencies:
#    pip install paho-mqtt websockets
# ═══════════════════════════════════════════════════════════════

import asyncio
import json
import ssl
import signal
import sys
import time
import threading
from datetime import datetime, timezone

from http.server import SimpleHTTPRequestHandler, HTTPServer
from functools import partial

import paho.mqtt.client as mqtt
import websockets
from websockets.server import WebSocketServerProtocol

# ── CONFIGURATION ──────────────────────────────────────────────
# Edit these 4 printers with your own values
PRINTERS = [
    {"id": 0, "name": "Printer 1", "ip": "192.168.10.102", "serial": "00M09A3B2700035", "code": "cfda32ee"},
    {"id": 1, "name": "Printer 2", "ip": "192.168.10.106", "serial": "00M09D482400921", "code": "6e144d6b"},
    {"id": 2, "name": "Printer 3", "ip": "192.168.10.103", "serial": "00M09D490201428", "code": "fdc70620"},
    {"id": 3, "name": "Printer 4", "ip": "192.168.10.104", "serial": "00M09C431200531", "code": "f73bb784"},
]
WS_URL = "0.0.0.0"
WS_PORT = 3000  # Port the dashboard connects to
HTTP_URL = "0.0.0.0"
HTTP_PORT  = 8080
# ──────────────────────────────────────────────────────────────

# Holds latest known state for each printer
printer_states = [
    {
        "id": p["id"],
        "name": p["name"],
        "ip": p["ip"],
        "status": "connecting",
        "file": "",
        "progress": 0,
        "remaining": 0,
        "elapsed": 0,
        "nozzle": 0,
        "nozzle_target": 0,
        "bed": 0,
        "bed_target": 0,
        "layer": 0,
        "total_layers": 0,
        "hms": [],
        "print_error": 0,
        "error": None,
        "last_update": None,
    }
    for p in PRINTERS
]

# Active WebSocket clients (dashboard browser tabs)
ws_clients: set[WebSocketServerProtocol] = set()

# Asyncio event loop reference (set at startup)
loop: asyncio.AbstractEventLoop = None


# ── Broadcast to all WebSocket clients ────────────────────────
def broadcast(msg: dict):
    """Send a message to all connected dashboard clients."""
    data = json.dumps(msg)
    if not ws_clients:
        return
    asyncio.run_coroutine_threadsafe(_broadcast_async(data), loop)


async def _broadcast_async(data: str):
    dead = set()
    for client in ws_clients:
        try:
            await client.send(data)
        except websockets.exceptions.ConnectionClosed:
            dead.add(client)
    ws_clients.difference_update(dead)


# ── WebSocket server ───────────────────────────────────────────
async def ws_handler(websocket: WebSocketServerProtocol):
    ws_clients.add(websocket)
    print(f"  Dashboard connected ({len(ws_clients)} client(s))")

    # Send current state immediately on connect
    await websocket.send(json.dumps({"type": "full_state", "printers": printer_states}))

    try:
        await websocket.wait_closed()
    finally:
        ws_clients.discard(websocket)
        print(f"  Dashboard disconnected ({len(ws_clients)} client(s))")


# ── MQTT callbacks ─────────────────────────────────────────────
def make_on_connect(printer: dict):
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc != 0:
            print(f"✗ {printer['name']} connection failed (rc={rc})")
            return

        print(f"✓ {printer['name']} connected")
        state = printer_states[printer["id"]]
        state["status"] = "idle"
        state["error"] = None

        # Subscribe to the printer's report topic
        topic = f"device/{printer['serial']}/report"
        client.subscribe(topic)
        print(f"  Subscribed to {topic}")

        # Request a full status update immediately
        request_topic = f"device/{printer['serial']}/request"
        client.publish(
            request_topic,
            json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}),
        )

        broadcast({"type": "printer_update", "printer": state})

    return on_connect


def make_on_message(printer: dict):
    def on_message(client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            print_data = data.get("print")
            if not print_data:
                return

            state = printer_states[printer["id"]]
            prev_status = state["status"]

            # Only update status when gcode_state is present
            if "gcode_state" in print_data:
                gcode = print_data["gcode_state"].upper()
                if gcode in ("RUNNING", "PREPARE", "SLICING"):
                    state["status"] = "printing"
                elif gcode == "PAUSE":
                    state["status"] = "paused"
                elif gcode == "FAILED":
                    state["status"] = "error"
                elif gcode in ("FINISH", "IDLE"):
                    state["status"] = "idle"

            # Progress & time
            if "mc_percent" in print_data:
                state["progress"] = round(print_data["mc_percent"])
            if "mc_remaining_time" in print_data:
                state["remaining"] = print_data["mc_remaining_time"] * 60

            # Estimate elapsed from progress + remaining
            if state["progress"] > 0 and state["remaining"] > 0:
                total = state["remaining"] / (1 - state["progress"] / 100)
                state["elapsed"] = round(total * (state["progress"] / 100))

            # Temperatures
            if "nozzle_temper" in print_data:
                state["nozzle"] = round(print_data["nozzle_temper"])
            if "nozzle_target_temper" in print_data:
                state["nozzle_target"] = round(print_data["nozzle_target_temper"])
            if "bed_temper" in print_data:
                state["bed"] = round(print_data["bed_temper"])
            if "bed_target_temper" in print_data:
                state["bed_target"] = round(print_data["bed_target_temper"])

            # Layers
            if "layer_num" in print_data:
                state["layer"] = print_data["layer_num"]
            if "total_layer_num" in print_data:
                state["total_layers"] = print_data["total_layer_num"]

            # File name
            if print_data.get("subtask_name"):
                state["file"] = print_data["subtask_name"]
            elif print_data.get("gcode_file"):
                state["file"] = print_data["gcode_file"].split("/")[-1]

            # Pause / error reason codes
            if "hms" in print_data:
                state["hms"] = print_data["hms"]
            if "print_error" in print_data:
                state["print_error"] = print_data["print_error"]

            state["last_update"] = datetime.now(timezone.utc).isoformat()
            state["error"] = None

            if prev_status != state["status"]:
                print(f"  {printer['name']}: {prev_status} → {state['status']}")

            broadcast({"type": "printer_update", "printer": state})

        except (json.JSONDecodeError, KeyError):
            # Silently ignore malformed messages
            pass

    return on_message


def make_on_disconnect(printer: dict):
    def on_disconnect(client, userdata, rc, properties=None):
        print(f"  {printer['name']} offline, retrying...")
        state = printer_states[printer["id"]]
        state["status"] = "connecting"
        broadcast({"type": "printer_update", "printer": state})

    return on_disconnect


def make_on_error(printer: dict):
    """paho-mqtt does not have a dedicated error callback; errors surface via
    on_connect (bad rc) or as exceptions.  This helper is kept for symmetry and
    called manually where needed."""

    def handle_error(err_msg: str):
        print(f"✗ {printer['name']} error: {err_msg}")
        state = printer_states[printer["id"]]
        state["status"] = "error"
        if "ECONNREFUSED" in err_msg or "Connection refused" in err_msg:
            state["error"] = "Connection refused — check IP"
        elif "auth" in err_msg.lower():
            state["error"] = "Auth failed — check access code"
        else:
            state["error"] = err_msg
        broadcast({"type": "printer_update", "printer": state})

    return handle_error


# ── Connect to each printer via MQTT ──────────────────────────
def connect_printer(printer: dict) -> mqtt.Client:
    mqtt_url = f"mqtts://{printer['ip']}:8883"
    print(f"Connecting to {printer['name']} at {mqtt_url} ...")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"dashboard_{printer['serial']}_{int(time.time() * 1000)}",
        protocol=mqtt.MQTTv5,
    )
    client.username_pw_set("bblp", printer["code"])

    # Bambu printers use self-signed TLS certificates
    tls_ctx = ssl.create_default_context()
    tls_ctx.check_hostname = False
    tls_ctx.verify_mode = ssl.CERT_NONE
    client.tls_set_context(tls_ctx)

    handle_error = make_on_error(printer)

    client.on_connect = make_on_connect(printer)
    client.on_message = make_on_message(printer)
    client.on_disconnect = make_on_disconnect(printer)

    try:
        client.connect(printer["ip"], port=8883, keepalive=60)
    except Exception as exc:
        handle_error(str(exc))

    # paho's background thread handles reconnects automatically
    client.reconnect_delay_set(min_delay=5, max_delay=5)
    client.loop_start()

    return client

# ── HTTP server ────────────────────────────────────────────────
def start_http_server(directory: str = ".", port: int = 8080):
    handler = partial(SimpleHTTPRequestHandler, directory=directory)
    httpd = HTTPServer((HTTP_URL, port), handler)
    print(f"✓ HTTP server running on http://{HTTP_URL}:{port}")
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


# ── Main ───────────────────────────────────────────────────────
async def main():
    global loop
    loop = asyncio.get_running_loop()

    print("━" * 50)
    print("  Bambu Lab Print Farm Dashboard — Bridge")
    print("━" * 50)

    # Start MQTT connections (each runs its own background thread)
    mqtt_clients = [connect_printer(p) for p in PRINTERS]

    # Start the http server inside the public folder
    http_server = start_http_server(directory="./public", port=HTTP_PORT)

    # open browser
    import webbrowser
    webbrowser.open(f'http://localhost:{HTTP_PORT}')

    # Start WebSocket server
    async with websockets.serve(ws_handler, WS_URL, WS_PORT):
        print(f"\n✓ WebSocket server running on ws://{WS_URL}:{WS_PORT}")
        print("  Open dashboard.html in your browser\n")

        # Run until interrupted
        stop = loop.create_future()

        def _shutdown(*_):
            print("\nShutting down...")
            http_server.shutdown()
            for c in mqtt_clients:
                c.loop_stop()
                c.disconnect()
            stop.set_result(None)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        await stop


if __name__ == "__main__":
    asyncio.run(main())