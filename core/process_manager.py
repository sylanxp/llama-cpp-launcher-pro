import subprocess
import threading
import time
import os
import platform
import urllib.request
import json
from PySide6.QtCore import Signal, QObject

class ProcessManager(QObject):
    """进程管理：负责 llama.cpp 服务启动、日志捕获、自动重启"""
    log_signal = Signal(str, str)

    def __init__(self, log_callback=None):
        super().__init__()
        self.process = None
        self.is_running = False
        self.is_restarting = False
        self.config = {}
        self.log_callback = log_callback
        self.log_signal.connect(self._emit_log)

    def _emit_log(self, text, level):
        if self.log_callback:
            self.log_callback(text, level)

    def _resolve_model_path(self, model_name, model_dir):
        """将模型名称解析为完整路径。支持三种形态：
        1. 完整绝对路径 -> 直接返回
        2. 相对路径（相对于 model_dir）-> 拼接
        3. 仅文件名 -> 在 model_dir 下递归查找
        """
        if not model_name:
            return ""
        
        # 已经是绝对路径且存在
        if os.path.isabs(model_name) and os.path.exists(model_name):
            return model_name
        
        # 尝试拼接 model_dir
        if model_dir and os.path.isdir(model_dir):
            candidate = os.path.join(model_dir, model_name)
            if os.path.exists(candidate):
                return candidate
            
            # 递归查找（支持子目录中的模型）
            for root, dirs, files in os.walk(model_dir):
                for f in files:
                    if f == os.path.basename(model_name) or f == model_name:
                        return os.path.join(root, f)
        
        self.log_signal.emit(f"警告: 未找到模型文件 '{model_name}'，将使用原值", "WARN")
        return model_name

    def start(self, config):
        """启动 llama-server 进程"""
        self.config = config
        
        server_path = config.get("llama_dir", "")
        model_dir = config.get("model_dir", "")
        model_name = config.get("main_model", "")
        
        if not server_path or not os.path.exists(server_path):
            self.log_signal.emit("错误: Llama.cpp 目录路径无效", "ERROR")
            return False
        
        # 查找执行文件
        exe_path = os.path.join(server_path, "llama-server.exe")
        if platform.system() != "Windows":
            exe_path = os.path.join(server_path, "llama-server")
        
        if not os.path.exists(exe_path):
            self.log_signal.emit(f"错误: 找不到执行文件 {exe_path}", "ERROR")
            return False

        # 解析模型路径（关键修复）
        model_path = self._resolve_model_path(model_name, model_dir)
        if not model_path or not os.path.exists(model_path):
            self.log_signal.emit(f"错误: 找不到模型文件 '{model_name}'", "ERROR")
            return False
        
        self.log_signal.emit(f"模型路径: {model_path}", "INFO")

        cmd = [
            exe_path,
            "-m", model_path,
            "--ctx-size", str(config.get("ctx_size", 4096)),
            "-ngl", str(config.get("ngl", 99)),
            "-t", str(config.get("threads", 4)),
            "-b", str(config.get("batch", 512)),
            "-ub", str(config.get("ubatch", 512)),
            "-np", str(config.get("np", 1)),
            "--port", str(config.get("port", 8080)),
            "--host", config.get("custom_host", "127.0.0.1") if config.get("listen_mode") == "custom" else
                     ("0.0.0.0" if config.get("listen_mode") == "lan" else "127.0.0.1")
        ]

        # 视觉模型支持
        vision_name = config.get("vision_model", "")
        if vision_name:
            vision_path = self._resolve_model_path(vision_name, model_dir)
            if vision_path and os.path.exists(vision_path):
                cmd.extend(["--mmproj", vision_path])
                self.log_signal.emit(f"视觉模型: {vision_path}", "INFO")

        # ===== 性能优化参数 =====
        # 新版 llama-server: --flash-attn [on|off|auto]，不要裸用
        if config.get("flash_attn", True):
            cmd.append("--flash-attn")
            cmd.append("on")
        
        # 智能 mlock：自动重启模式下移除 mlock 以提高成功率
        if not config.get("auto_restart") and config.get("mlock"):
            cmd.append("--mlock")

        # 缓存类型（必须放在 --flash-attn 之后，否则会被吞掉）
        cmd.extend(["--cache-type-k", config.get("cache_k", "f16")])
        cmd.extend(["--cache-type-v", config.get("cache_v", "f16")])

        # 高级参数
        # mmap 在 UI 中是 "Disable mmap" 复选框，勾选 = 禁用 = 传 --no-mmap
        if config.get("mmap", False):
            cmd.append("--no-mmap")
        
        if config.get("cont_batching", True):
            cmd.append("--cont-batching")
        
        if config.get("no_kv_offload", False):
            cmd.append("--no-kv-offload")
        
        if config.get("tensor_split", "").strip():
            cmd.extend(["--tensor-split", config.get("tensor_split", "").strip()])

        # 附加自定义参数
        extra = config.get("extra_args", "").strip()
        if extra:
            cmd.extend(extra.split())

        try:
            self.log_signal.emit(f"正在启动: {' '.join(cmd)}", "INFO")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                cwd=os.path.dirname(exe_path)
            )
            self.is_running = True
            
            threading.Thread(target=self._read_output, daemon=True).start()
            
            if config.get("auto_restart"):
                threading.Thread(target=self._auto_restart_monitor, daemon=True).start()
                
            return True
        except Exception as e:
            self.log_signal.emit(f"启动失败: {str(e)}", "ERROR")
            return False

    def _read_output(self):
        """实时捕获进程 stdout"""
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.log_signal.emit(f"[log] {line.strip()}", "INFO")
        
        if self.process:
            exit_code = self.process.poll()
            self.is_running = False
            self.log_signal.emit(f"进程已退出，退出码: {exit_code}", "WARN")
            
            if self.config.get("auto_restart"):
                self._trigger_restart()

    def _auto_restart_monitor(self):
        """轮询 /slots API，n_past/n_ctx > 98% 时触发重启"""
        port = self.config.get("port", 8080)
        url = f"http://127.0.0.1:{port}/slots"
        
        time.sleep(10)  # 等模型加载
        
        while self.is_running:
            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    data = json.loads(response.read().decode())
                    for slot in data:
                        n_past = slot.get("n_past", slot.get("n_past_tokens", 0))
                        n_ctx = slot.get("n_ctx", 1)
                        if n_ctx > 0 and (n_past / n_ctx) > 0.98:
                            pct = int((n_past / n_ctx) * 100)
                            self.log_signal.emit(f"[auto-restart] 上下文占用达 {pct}%，即将重启", "SYS")
                            self._trigger_restart()
                            break
            except Exception:
                if self.config.get("detect_method") == "api":
                    self.log_signal.emit("[auto-restart] API 响应超时，准备重启...", "SYS")
                    self._trigger_restart()
            
            time.sleep(3)

    def _trigger_restart(self):
        if self.is_restarting:
            return
        self.is_restarting = True
        
        self.stop()
        
        delay = self.config.get("restart_interval", 3)
        time.sleep(delay)
        
        self.is_restarting = False
        self.start(self.config)

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None
            self.is_running = False
            self.log_signal.emit("服务已停止，资源已释放。", "WARN")
            return True
        return False