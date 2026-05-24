import subprocess
import threading
import time
import os
import platform
import urllib.request
import json
from PySide6.QtCore import Signal, QObject

class ProcessManager(QObject):
    """
    进程管理类：负责 llama.cpp 服务的生命周期管理、日志捕获与自动重启
    """
    log_signal = Signal(str, str) # text, level

    def __init__(self, log_callback=None):
        super().__init__()
        self.process = None
        self.is_running = False
        self.is_restarting = False
        self.config = {}
        self.log_callback = log_callback
        
        # 这里的 Signal 用于从线程安全地更新 UI
        self.log_signal.connect(self._emit_log)

    def _emit_log(self, text, level):
        if self.log_callback:
            self.log_callback(text, level)

    def start(self, config):
        """启动服务器"""
        self.config = config
        
        server_path = config.get("llama_dir", "")
        model = config.get("main_model", "")
        
        if not server_path or not os.path.exists(server_path):
            self.log_signal.emit("错误: Llama.cpp 目录路径无效", "ERROR")
            return False
        
        # 1. 拼接命令行参数
        # 注意：server_path 应该是目录，我们需要拼接成 llama-server.exe
        exe_path = os.path.join(server_path, "llama-server.exe")
        if platform.system() != "Windows":
            exe_path = os.path.join(server_path, "llama-server")

        if not os.path.exists(exe_path):
            self.log_signal.emit(f"错误: 找不到执行文件 {exe_path}", "ERROR")
            return False

        cmd = [
            exe_path, 
            "-m", model,
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
        vision_model = config.get("vision_model", "")
        if vision_model and os.path.exists(vision_model):
            cmd.extend(["--mmproj", vision_model])

        # 性能优化参数
        if config.get("flash_attn"):
            cmd.append("--flash-attn")
        
        # 智能 mlock 逻辑：自动重启模式下移除 mlock 以提高成功率
        if not config.get("auto_restart") and config.get("mlock"):
            cmd.append("--mlock")

        # 缓存类型
        cmd.extend(["--cache-type-k", config.get("cache_k", "f16")])
        cmd.extend(["--cache-type-v", config.get("cache_v", "f16")])
        
        # 附加参数
        extra = config.get("extra_args", "").strip()
        if extra:
            cmd.extend(extra.split())

        # 2. 启动进程
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
            
            # 开启日志读取线程
            threading.Thread(target=self._read_output, daemon=True).start()
            
            # 若启用自动重启，启动 API 探针
            if config.get("auto_restart"):
                threading.Thread(target=self._auto_restart_monitor, daemon=True).start()
                
            return True
        except Exception as e:
            self.log_signal.emit(f"启动失败: {str(e)}", "ERROR")
            return False

    def _read_output(self):
        """实时捕获进程输出"""
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.log_signal.emit(f"[log] {line.strip()}", "INFO")
        
        if self.process:
            exit_code = self.process.poll()
            self.is_running = False
            self.log_signal.emit(f"进程已退出，退出码: {exit_code}", "WARN")
            
            # 触发自动重启
            if self.config.get("auto_restart"):
                self._trigger_restart()

    def _auto_restart_monitor(self):
        """高精度 API 轮询监测"""
        port = self.config.get("port", 8080)
        url = f"http://127.0.0.1:{port}/slots"
        
        # 缓冲加载时间
        time.sleep(10)
        
        while self.is_running:
            try:
                # 检测 API 状态
                with urllib.request.urlopen(url, timeout=2) as response:
                    data = json.loads(response.read().decode())
                    for slot in data:
                        n_past = slot.get("n_past", slot.get("n_past_tokens", 0))
                        n_ctx = slot.get("n_ctx", 1)
                        if n_ctx > 0 and (n_past / n_ctx) > 0.98:
                            self.log_signal.emit(f"[auto-restart] 上下文占用达 {int((n_past/n_ctx)*100)}%", "SYS")
                            self._trigger_restart()
                            break
            except Exception:
                # 如果 API 不通，且在自动重启模式下，也尝试重启
                if self.config.get("detect_method") == "api":
                    self.log_signal.emit("[auto-restart] API 响应超时，准备重置...", "SYS")
                    self._trigger_restart()
            
            time.sleep(3)

    def _trigger_restart(self):
        """安全执行重启序列"""
        if self.is_restarting: return
        self.is_restarting = True
        
        # 停止当前进程
        self.stop()
        
        delay = self.config.get("restart_interval", 3)
        time.sleep(delay)
        
        self.is_restarting = False
        self.start(self.config)

    def stop(self):
        """彻底停止服务"""
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
