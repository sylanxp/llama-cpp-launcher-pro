# Llama.cpp Launcher Pro

Llama.cpp Launcher Pro is a professional desktop launcher for llama.cpp built with Python and PySide6. It simplifies the deployment, parameter tuning, and maintenance of llama.cpp services through an intuitive graphical interface and an industrial-grade auto-healing mechanism.

## Core Features

### Hardware Monitor
- CPU Info: Real-time display of CPU model, physical cores, and logical threads.
- GPU Detection: Automatic identification of NVIDIA GPU name and available VRAM (supports nvidia-smi and wmic).
- Dynamic Refresh: Support for manual one-click refresh or automatic periodic updates.

### Path Management
- Smart Browser: Integrated directory browser with Windows drive detection, hierarchical navigation, and manual path jumping.
- Model Selection: Automatic scanning of .gguf files in the specified directory for Main Model and Vision Model selection.

### Inference Parameters
Detailed visualization of llama-server parameters:
- Basic: Context Size, GPU Layers (ngl), CPU Threads.
- Optimization: Batch Size, UBatch Size, Parallel (np), Flash Attention.
- Cache Control: Custom Cache K/V Type (e.g., f16, q8_0, q4_0).
- Memory Lock: --mlock switch to prevent memory swapping to disk.

### Auto-Restart Engine
Self-healing mechanism for long-term operation:
- High-Precision Monitoring: Polls the /slots API to calculate n_past / n_ctx. Triggers restart when occupancy exceeds 98%.
- Health Check: Monitors the /health API to detect service crashes and trigger immediate recovery.
- Smart Strategy: Automatically disables --mlock during auto-restart to ensure higher success rates.
- Visual Feedback: Auto-restart events are highlighted in purple [auto-restart] tags in the log.

### Service Logs
- Terminal Simulation: Dark-themed log window with real-time scrolling output.
- Semantic Highlighting: Color-coded logs based on levels (INFO, WARN, ERROR, SYS) for fast troubleshooting.

---

## Installation and Usage

### 1. Prerequisites
- OS: Windows 10/11 (64-bit)
- Python: 3.8+
- Dependencies:
  ```bash
  pip install PySide6 psutil nvidia-ml-py
  ```

### 2. Quick Start
```bash
python main.py
```

### 3. Build as .exe
To package the application into a standalone executable:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Llama.cpp-Launcher-Pro" main.py
```
The executable will be available in the dist/ folder.

---

## Tech Stack
- GUI: PySide6 (Qt for Python)
- Core: Python 3.x / Subprocess
- Monitoring: psutil / nvidia-smi / urllib
- Config: JSON-based Persistence
