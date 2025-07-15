# 🧱 Azeroth Chain Explorer

**Azeroth Chain Explorer** is a World of Warcraft–themed blockchain simulation platform built with **Flask**, **Socket.IO**, and **JavaScript**. It visually demonstrates the core principles of blockchain technology — including block mining, wallet generation, and transaction validation — through an immersive, fantasy-inspired interface.

---

## 🎯 Project Objective

To **simplify blockchain concepts** for beginners through an interactive, real-time, and visually engaging environment. Azeroth Chain Explorer transforms technical mechanics into an intuitive experience using themed storytelling and gamification.

---

## 🔍 Key Features

- 🔐 **Secure Wallet Generation** — ECDSA-based keypairs for transactions.
- ⛏️ **Proof-of-Work Mining** — Blocks mined with a simulated PoW algorithm.
- 🔄 **Live Blockchain Broadcast** — Real-time updates via Socket.IO.
- 🧩 **Transaction Handling** — Add transactions and validate them on-chain.
- 🌍 **WoW-Inspired UI** — Custom frontend styled after the Warcraft universe.
- 🐳 **Docker-Ready** — Fully containerized for easy setup and deployment.

---

## 🏗️ Tech Stack

| Layer        | Technology                         |
|--------------|-------------------------------------|
| **Frontend** | HTML, CSS, JavaScript               |
| **Backend**  | Python (Flask), Socket.IO, ECDSA    |
| **Deployment** | Docker, Gunicorn, Nginx            |
| **Versioning** | Git + GitHub                        |

---

## 📂 Directory Structure
'''
Azeroth_Chain_Explorer/
├── blockchain/
│ ├── blockchain.py # Core blockchain and API logic
│ ├── static/ # Frontend assets (CSS, JS)
│ ├── templates/ # HTML templates (Jinja2)
│ ├── Dockerfile # Docker build configuration
│ ├── docker-compose.yml # Docker services config
│ └── requirements.txt # Python dependencies
├── .git/ # Git repo
├── .venv/ # Python virtual environment (optional)
└── README.md # Project documentation
'''


---

## ⚙️ Local Setup (via Docker)

To get started locally:

```bash
# 1. Clone the repository
git clone https://github.com/Yanvi09/Azeroth_Chain_Explorer.git
cd Azeroth_Chain_Explorer/blockchain

# 2. Build and start the app using Docker
docker-compose up --build

# 3. Open the app
Visit http://localhost:5000 in your browser

