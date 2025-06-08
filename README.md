# 🚐 can-mqtt-lab

A **test tool for CAN-based systems** – built with **Python, Flask, and Docker**.  
This project simulates a CAN network entirely in software and visualizes the data in real time via a web-based dashboard.

✅ **Runs entirely in Docker – no physical CAN hardware required.**

---

## 🎯 Purpose

This project was created to:
- Practice using Docker in an embedded systems context
- Understand container-based testing environments for CAN networks
- Build a complete simulated vehicle telemetry flow using MQTT + SocketIO

---

## ⚙️ System Overview

| Component     | Function                                                  |
|---------------|-----------------------------------------------------------|
| `generator/`  | Simulates CAN traffic with fake vehicle data              |
| `can-reader/` | Reads CAN (if enabled) and republishes to MQTT            |
| `api/`        | Flask API that receives, stores, and exposes CAN messages |
| `frontend/`   | Web dashboard with real-time updates via WebSocket        |
| `Docker`      | Runs everything in isolation using Docker Compose         |

---

## 🚀 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/your-username/docker-can-lab.git
cd docker-can-lab
```

2. **Create virtual CAN interface (host only)**
```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

3. **Start the lab environment**
```bash
docker compose up --build
```

4. **Open the dashboard**

Visit [http://localhost:5000](http://localhost:5000) to see the live vehicle data.

---

## 🧪 Features

- Live vehicle telemetry: GPS, doors, passengers, stop name, speed, etc.
- MQTT-based transport for all CAN messages
- Web dashboard auto-refreshes via WebSockets
- Modular structure: each container has a clear role
- Optional CAN integration using `python-can` + `vcan`

---

## 📦 Docker Architecture

```
+-------------+        MQTT         +-------------+
| generator   |  ───────────────▶   | mqtt-broker |
+-------------+                    +-------------+
       │                                 ▲
       ▼                                 │
+-------------+   HTTP/MQTT      +-------------+
| can-reader  | ───────────────▶ |     api     |
+-------------+                  +-------------+
                                       │
                                       ▼
                                +-------------+
                                |  frontend   |
                                +-------------+
```

---

## 🛠️ Tech Stack

- Python (Flask, SocketIO, Paho MQTT)
- Docker & Docker Compose
- HTML, JavaScript (AJAX + WebSocket)
- virtual CAN (`vcan0`) via `python-can`

---

## 📜 License

MIT – free to use and modify.

---

## ✨ Future Ideas

- Save/load message history to disk
- Support extended 29-bit CAN IDs
- Interactive dashboard filters
- Graphs for time-based data (speed, delay, fuel)

---

Made with ❤️ to learn Docker for embedded systems.
