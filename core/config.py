import os
import sys
import glob
import json

class ConfigManager:
    """
    配置管理类，负责所有参数的持久化存储与加载
    """
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.defaults = {
            # 路径
            "llama_dir": self._get_default_drive(),
            "model_dir": self._get_default_drive(),
            "main_model": "",
            "vision_model": "",
            # 基础参数
            "ctx_size": 4096,
            "ngl": 99,
            "threads": 4,
            "port": 8080,
            "listen_mode": "local",
            "custom_host": "127.0.0.1",
            "np": 1,
            "img_tokens": 1024,
            # 性能优化
            "batch": 512,
            "ubatch": 512,
            "cache_k": "f16",
            "cache_v": "f16",
            # 高级参数
            "flash_attn": True,
            "mlock": False,
            "cont_batching": True,
            "mmap": False,
            "no_kv_offload": False,
            "tensor_split": "",
            # 自动重启
            "auto_restart": False,
            "detect_method": "api",
            "restart_interval": 3,
            # 额外参数
            "extra_args": "",
        }
        self.config = self.load_config()

    def _get_default_drive(self):
        """自动检测程序所在盘符作为默认路径"""
        try:
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                return os.path.splitdrive(exe_path)[0] + "\\"
            else:
                script_path = os.path.abspath(__file__)
                return os.path.splitdrive(script_path)[0] + "\\"
        except Exception:
            return "C:\\"

    def scan_gguf_files(self, directory):
        """扫描指定目录下的所有 .gguf 文件"""
        gguf_files = []
        if directory and os.path.isdir(directory):
            pattern = os.path.join(directory, "**", "*.gguf")
            gguf_files = glob.glob(pattern, recursive=True)
        return gguf_files

    def load_config(self):
        """加载配置，如果文件不存在则使用默认值"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    full_config = self.defaults.copy()
                    full_config.update(data)
                    return full_config
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.defaults.copy()
        return self.defaults.copy()

    def save_config(self, new_config=None):
        """保存当前配置到文件"""
        if new_config:
            self.config = new_config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key):
        """获取单个配置项"""
        return self.config.get(key, self.defaults.get(key))

    def set(self, key, value):
        """设置单个配置项"""
        self.config[key] = value