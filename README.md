# 🚀 Llama.cpp Launcher Pro

**Llama.cpp Launcher Pro** 是一款基于 Python 和 PySide6 构建的专业桌面启动器，旨在通过图形化界面简化 `llama.cpp` 的部署、参数精调及服务维护。它将复杂的命令行操作转化为直观的 UI 交互，并提供了工业级的服务自愈机制。

Llama.cpp Launcher Pro is a professional desktop launcher for llama.cpp built with Python and PySide6. It simplifies the deployment, parameter tuning, and maintenance of llama.cpp services through an intuitive graphical interface and an industrial-grade auto-healing mechanism.

---

## ✨ 核心功能 | Core Features

### 🖥️ 硬件实时监测 | Hardware Monitor
- **中文**: 顶部状态栏实时显示 CPU 型号、逻辑核心数、系统内存总量及架构。自动识别 NVIDIA GPU 名称及可用显存，支持手动一键刷新或自动定时更新。
- **English**: Real-time display of CPU model, logical cores, and system memory. Automatically identifies NVIDIA GPU name and available VRAM, supporting manual or periodic updates.

### 📁 增强型路径管理 | Path Management
- **中文**: 集成自定义目录浏览器，支持 Windows 盘符自动检测、逐级导航及手动路径跳转。自动扫描 `.gguf` 文件，支持快速切换主模型与视觉模型。
- **English**: Integrated directory browser with Windows drive detection, hierarchical navigation, and manual path jumping. Automatically scans `.gguf` files for Main and Vision model selection.

### ⚙️ 硬核参数精调 | Inference Parameters
将 `llama-server` 的关键参数可视化：
- **基础性能 (Basic)**: `Context Size`, `GPU Layers (ngl)`, `CPU Threads`.
- **深度优化 (Optimization)**: `Batch Size`, `UBatch Size`, `Parallel (np)`, `Flash Attention`.
- **缓存控制 (Cache)**: 支持自定义 `Cache K/V Type` (如 f16, q8_0, q4_0).
- **内存锁定 (Memory Lock)**: 提供 `--mlock` 开关，防止模型被交换到磁盘。
- **English**: Detailed visualization of key parameters including Context, ngl, threads, batch/ubatch, parallel, and cache types. Includes `--mlock` switch for stability.

### 🔄 自动化运维与自愈 | Auto-Restart Engine
- **中文**: 通过轮询 `/slots` 接口，实时计算 `n_past / n_ctx` 占用率。当占用率超过 98% 或 `/health` 接口不可达时，自动触发重启。在重启模式下智能移除 `--mlock` 以提高成功率。
- **English**: High-precision monitoring via `/slots` API (triggers restart at >98% occupancy) and `/health` API. Smartly removes `--mlock` during auto-restart to ensure higher success rates.

### 📋 实时专业日志 | Service Logs
- **中文**: 采用深色主题终端仿真窗口，支持实时滚动输出。根据日志级别 (INFO, WARN, ERROR, SYS) 自动匹配颜色高亮。
- **English**: Dark-themed terminal simulation with real-time scrolling and semantic color highlighting based on log levels.

---

## 🛠️ 安装与运行 | Installation and Usage

### 1. 环境依赖 | Prerequisites
- **操作系统 (OS)**: Windows 10/11 (64-bit)
- **Python**: 3.8+
- **依赖库 (Dependencies)**:
  ```bash
  pip install PySide6 psutil nvidia-ml-py
  ```

### 2. 快速启动 | Quick Start
```bash
python main.py
```

### 3. 打包为 .exe | Build as .exe
如果您想将其打包为独立的可执行文件：
If you wish to package it as a standalone executable:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Llama.cpp-Launcher-Pro" main.py
```
打包完成后，`.exe` 文件将位于 `dist/` 目录下。 / The .exe will be available in the dist/ folder.

---

## 📈 技术栈 | Tech Stack
- **GUI**: PySide6 (Qt for Python)
- **Core**: Python 3.x / Subprocess
- **Monitoring**: psutil / nvidia-smi / urllib
- **Config**: JSON-based Persistence
