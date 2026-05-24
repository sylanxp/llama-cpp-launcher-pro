import psutil
import platform
import subprocess
import re

class HardwareInfo:
    """
    硬件信息检测类，支持 Windows/Linux 跨平台检测
    """
    @staticmethod
    def get_cpu_info():
        """获取处理器型号、核心数、线程数"""
        try:
            # Windows 平台使用 wmic
            if platform.system() == "Windows":
                cmd = "wmic cpu get name"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
                name = output.split('\n')[1].strip() if len(output.split('\n')) > 1 else "Unknown CPU"
            else:
                # Linux 平台读取 /proc/cpuinfo
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if "model name" in line:
                            name = line.split(":")[1].strip()
                            break
                    else:
                        name = "Unknown CPU"
            
            return {
                "model": name,
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True)
            }
        except Exception as e:
            return {"model": "Error", "cores": 0, "threads": 0, "error": str(e)}

    @staticmethod
    def get_memory_info():
        """获取内存总量和系统架构"""
        try:
            mem = psutil.virtual_memory()
            return {
                "total": f"{round(mem.total / (1024**3), 2)} GB",
                "arch": platform.machine()
            }
        except Exception as e:
            return {"total": "Error", "arch": "Error", "error": str(e)}

    @staticmethod
    def get_gpu_info():
        """获取 GPU 名称和显存大小 (优先使用 nvidia-smi)"""
        try:
            # 尝试调用 nvidia-smi
            output = subprocess.check_output("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits", 
                                           shell=True).decode('utf-8', errors='ignore').strip()
            if output:
                parts = output.split(',')
                return {
                    "name": parts[0].strip(),
                    "vram": f"{parts[1].strip()} MB"
                }
        except Exception:
            pass # 如果 nvidia-smi 失败，尝试使用 wmic (Windows)
        
        try:
            if platform.system() == "Windows":
                cmd = "wmic path win32_VideoController get name"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
                name = output.split('\n')[1].strip() if len(output.split('\n')) > 1 else "Generic GPU"
                return {
                    "name": name,
                    "vram": "Unknown"
                }
        except Exception:
            pass
            
        return {"name": "No GPU Detected", "vram": "N/A"}

    @classmethod
    def get_all_info(cls):
        """一次性获取所有硬件快照"""
        return {
            "cpu": cls.get_cpu_info(),
            "memory": cls.get_memory_info(),
            "gpu": cls.get_gpu_info()
        }
