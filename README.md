# 🚀 Llama.cpp Launcher Pro

Llama.cpp Launcher Pro 是一款基于 Python 和 PySide6 构建的专业桌面启动器，旨在通过图形化界面简化 `llama.cpp` 的部署、参数精调及自动化运维。它将复杂的命令行操作转化为直观的 UI 交互，并提供了工业级的服务自愈机制。

## ✨ 核心功能

### 🖥️ 硬件实时监测 (Hardware Monitor)
- **多维度状态**：顶部状态栏实时显示 CPU 型号、逻辑核心数、系统内存总量及架构。
- **GPU 深度探测**：自动识别 NVIDIA GPU 名称及可用显存，兼容 `nvidia-smi` 与 `wmic` 探测路径。
- **动态刷新**：支持手动一键刷新或自动定时更新，确保启动前资源状态可见。

### 📁 增强型路径管理 (Advanced Path Management)
- **智能浏览**：集成自定义目录浏览器，支持 Windows 盘符自动检测、逐级导航及手动路径跳转。
- **模型快选**：自动扫描指定目录下的 `.gguf` 文件，支持快速切换 **主模型 (Main Model)** 与 **视觉模型 (Vision Model)**。

### ⚙️ 硬核参数精调 (Advanced Inference Params)
将 `llama-server` 的所有关键参数可视化：
- **基础性能**：`Context Size`, `GPU Layers (ngl)`, `CPU Threads`。
- **深度优化**：`Batch Size`, `UBatch Size`, `Parallel (np)`, `Flash Attention`。
- **缓存控制**：支持自定义 `Cache K/V Type` (如 f16, q8_0, q4_0)。
- **内存锁定**：提供 `--mlock` 开关，防止模型被交换到磁盘，提升推理稳定性。

### 🔄 自动化运维与自愈 (Auto-Restart Engine)
针对长时间运行或无限上下文场景设计的自愈机制：
- **高精度心跳监测**：通过轮询 `/slots` 接口，实时计算 $\text{n\_past / n\_ctx}$。当占用率超过 **98%** 时主动触发重启。
- **健康检查**：支持 API `/health` 接口监测，一旦服务不可达立即执行重启。
- **智能重启策略**：
  - **mlock 动态移除**：在自动重启模式下自动禁用 `--mlock`，避免因内存锁定导致的重启失败。
  - **可配置延迟**：支持自定义重启等待时间，防止频繁重启导致系统崩溃。
- **紫色高亮日志**：重启事件在日志窗口中以 `[auto-restart]` 紫色标签显著标出。

### 📋 实时专业日志 (Service Logs)
- **终端仿真**：深色主题日志窗口，支持实时滚动输出。
- **语义着色**：根据日志级别（INFO, WARN, ERROR, SYS）自动匹配颜色高亮，快速定位问题。

---

## 🛠️ 安装与运行

### 1. 环境依赖
- **操作系统**: Windows 10/11 (64-bit)
- **Python**: 3.8+
- **依赖库**:
  ```bash
  pip install PySide6 psutil nvidia-ml-py
  ```

### 2. 快速启动
```bash
python main.py
```

### 3. 打包为 .exe (Release)
如果你想将其打包为独立的可执行文件，请安装 `pyinstaller`：
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Llama.cpp-Launcher-Pro" main.py
```
打包完成后，`.exe` 文件将位于 `dist/` 目录下。

---

## 📈 技术栈
- **GUI**: PySide6 (Qt for Python)
- **Core**: Python 3.x / Subprocess
- **Monitoring**: psutil / nvidia-smi / urllib
- **Config**: JSON-based Persistence
