# 🚐 docker-can-lab

A **test tool for CAN-based systems** – built with **Python, Flask, and Docker**.  
This project simulates a CAN network entirely in software and visualizes the data in real time via a web-based dashboard.

✅ **Runs entirely in Docker – no physical CAN hardware required.**

---

## 🎯 Purpose

This project was created to:
- Practice using Docker in an embedded context
- Understand container-based test environments for CAN networks

---

## ⚙️ System Overview

| Component     | Function                                         |
|---------------|--------------------------------------------------|
| `generator/`  | Generates fake CAN data (ID + payload)           |
| `api/`        | Flask API that receives, stores, and exposes data|
| `frontend/`   | Web dashboard with real-time AJAX updates        |
| `Docker`      | Runs everything isolated and portable via Compose|

---

## 🚀 Getting Started

1. **Clone the repo**
```bash
git clone https://github.com/your-username/docker-can-lab.git
cd docker-can-lab
