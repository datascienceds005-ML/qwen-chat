#!/data/data/com.termux/files/usr/bin/bash
# One-time device provisioning. The repo twin of devcontainer.json.
set -e
REPO_URL="git@github.com:<you>/qwen-chat.git"      # read-only deploy key configured

pkg update -y && pkg upgrade -y
pkg install -y python python-pip build-essential cmake ninja python-numpy git
termux-wake-lock

git clone "$REPO_URL" ~/qwen-chat && cd ~/qwen-chat

# Pure-python deps (Termux/Bionic cannot use manylinux wheels):
pip install "pydantic<2"          # avoid pydantic v2's Rust core
pip install uvicorn               # NOT [standard] — skips uvloop/httptools builds

# ONE-TIME heavy step: compile llama.cpp for ARM64 (~15–30 min). Nothing to write.
CMAKE_ARGS="-DGGML_NATIVE=ON" pip install -e "./backend[mobile]"

# Model (out-of-band; verify checksum)
mkdir -p models
wget -O models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
sha256sum models/*.gguf   # compare against the checksum recorded in docs/runbook-device-day.md

# Serve: real engine, loopback only
ENGINE=real python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
