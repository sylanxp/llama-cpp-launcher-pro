import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, 
    QCheckBox, QPlainTextEdit, QScrollArea, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextCursor

from core.config import ConfigManager
from core.hardware import HardwareInfo
from core.process_manager import ProcessManager
from ui.file_browser import DirectoryBrowser

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Llama.cpp Launcher Pro")
        self.setMinimumSize(950, 800)
        
        self.config_mgr = ConfigManager()
        self.hw_info = HardwareInfo()
        self.proc_mgr = ProcessManager(self.append_log)
        
        self.init_ui()
        self.update_hw_display()
        
        self.hw_timer = QTimer()
        self.hw_timer.timeout.connect(self.update_hw_display)
        self.hw_timer.start(5000)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ===== 1. 硬件信息卡片 =====
        hw_frame = self._make_card_frame()
        hw_layout = QHBoxLayout(hw_frame)
        
        self.cpu_label = QLabel("CPU: 检测中...")
        self.mem_label = QLabel("MEM: 检测中...")
        self.gpu_label = QLabel("GPU: 检测中...")
        self.btn_refresh_hw = QPushButton("🔄 刷新")
        self.btn_refresh_hw.setFixedWidth(80)
        self.btn_refresh_hw.clicked.connect(self.update_hw_display)
        
        hw_layout.addWidget(self.cpu_label)
        hw_layout.addWidget(self.mem_label)
        hw_layout.addWidget(self.gpu_label)
        hw_layout.addStretch()
        hw_layout.addWidget(self.btn_refresh_hw)
        main_layout.addWidget(hw_frame)

        # ===== 2. 滚动配置区 =====
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setFrameShape(QFrame.NoFrame)
        
        config_container = QWidget()
        config_vbox = QVBoxLayout(config_container)
        config_vbox.setSpacing(8)

        self.controls = {}

        # ---------- A. 模型与路径 ----------
        group_path = QGroupBox("📂 模型与路径")
        path_grid = QGridLayout(group_path)
        path_grid.setSpacing(8)
        
        row = 0
        path_grid.addWidget(QLabel("Llama.cpp 目录"), row, 0)
        self.c_llama_dir = QLineEdit()
        btn1 = QPushButton("浏览"); btn1.setFixedWidth(60)
        btn1.clicked.connect(lambda: self.browse_dir("llama_dir"))
        hb = QHBoxLayout(); hb.addWidget(self.c_llama_dir); hb.addWidget(btn1)
        path_grid.addLayout(hb, row, 1)
        self.controls["llama_dir"] = self.c_llama_dir

        row = 1
        path_grid.addWidget(QLabel("模型目录"), row, 0)
        self.c_model_dir = QLineEdit()
        btn2 = QPushButton("浏览"); btn2.setFixedWidth(60)
        btn2.clicked.connect(self.browse_and_scan_models)
        hb = QHBoxLayout(); hb.addWidget(self.c_model_dir); hb.addWidget(btn2)
        path_grid.addLayout(hb, row, 1)
        self.controls["model_dir"] = self.c_model_dir

        row = 2
        path_grid.addWidget(QLabel("主模型"), row, 0)
        self.c_main_model = QComboBox()
        self.c_main_model.setEditable(True)
        self.c_main_model.setPlaceholderText("请先选择模型目录...")
        path_grid.addWidget(self.c_main_model, row, 1)
        self.controls["main_model"] = self.c_main_model

        row = 3
        path_grid.addWidget(QLabel("视觉模型"), row, 0)
        self.c_vision_model = QComboBox()
        self.c_vision_model.setEditable(True)
        self.c_vision_model.setPlaceholderText("留空 = 不使用视觉模型")
        path_grid.addWidget(self.c_vision_model, row, 1)
        self.controls["vision_model"] = self.c_vision_model

        config_vbox.addWidget(group_path)

        # ---------- B. 基础参数 ----------
        group_basic = QGroupBox("⚙️ 基础参数")
        basic_grid = QGridLayout(group_basic)
        basic_grid.setSpacing(8)

        basic_fields = [
            ("Context Size", "ctx_size", "int", 4096),
            ("GPU Layers (ngl)", "ngl", "int", 99),
            ("CPU Threads", "threads", "int", 4),
            ("Server Port", "port", "int", 8080),
            ("监听模式", "listen_mode", "combo", ["local", "lan", "custom"]),
            ("自定义 Host", "custom_host", "text", "127.0.0.1"),
            ("Parallel (np)", "np", "int", 1),
            ("Image Tokens", "img_tokens", "int", 1024),
        ]
        self._add_grid_fields(basic_grid, basic_fields, 0)
        config_vbox.addWidget(group_basic)

        # ---------- C. 性能优化 ----------
        group_perf = QGroupBox("⚡ 性能优化")
        perf_grid = QGridLayout(group_perf)
        perf_grid.setSpacing(8)

        perf_fields = [
            ("Batch Size", "batch", "int", 512),
            ("UBatch Size", "ubatch", "int", 512),
            ("Cache K Type", "cache_k", "combo", ["f16", "q8_0", "q4_0"]),
            ("Cache V Type", "cache_v", "combo", ["f16", "q8_0", "q4_0"]),
        ]
        self._add_grid_fields(perf_grid, perf_fields, 0)
        config_vbox.addWidget(group_perf)

        # ---------- D. 高级参数 ----------
        group_adv = QGroupBox("🔧 高级参数")
        adv_grid = QGridLayout(group_adv)
        adv_grid.setSpacing(8)

        adv_fields = [
            ("Flash Attention", "flash_attn", "bool", True),
            ("Memory Lock (mlock)", "mlock", "bool", False),
            ("Continuous Batching", "cont_batching", "bool", True),
            ("Disable mmap", "mmap", "bool", False),
            ("No KV Offload", "no_kv_offload", "bool", False),
            ("自动重启", "auto_restart", "bool", False),
            ("检测方式", "detect_method", "combo", ["api", "log"]),
            ("重启延迟(s)", "restart_interval", "int", 3),
        ]
        self._add_grid_fields(adv_grid, adv_fields, 0)
        config_vbox.addWidget(group_adv)

        # ---------- E. 额外参数 ----------
        group_extra = QGroupBox("📝 自定义参数 (空格分隔)")
        extra_layout = QHBoxLayout(group_extra)
        self.c_extra_args = QLineEdit()
        self.c_extra_args.setPlaceholderText("例如: --rope-scaling linear --rope-freq-base 10000")
        extra_layout.addWidget(self.c_extra_args)
        self.controls["extra_args"] = self.c_extra_args

        self.c_tensor_split = QLineEdit()
        self.c_tensor_split.setPlaceholderText("Tensor Split (多GPU): 0,0,1")
        extra_layout.addWidget(self.c_tensor_split)
        self.controls["tensor_split"] = self.c_tensor_split
        config_vbox.addWidget(group_extra)

        config_scroll.setWidget(config_container)
        main_layout.addWidget(config_scroll, 1)  # give stretch

        # ===== 3. 底部控制与日志 =====
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("🚀 启动服务")
        self.btn_start.setFixedHeight(40)
        self.btn_start.clicked.connect(self.handle_start)
        
        self.btn_stop = QPushButton("🛑 停止服务")
        self.btn_stop.setFixedHeight(40)
        self.btn_stop.clicked.connect(self.handle_stop)
        self.btn_stop.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        bottom_layout.addLayout(btn_layout)
        
        self.log_window = QPlainTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setPlaceholderText("服务日志将在此显示...")
        self.log_window.setFont(QFont("Consolas", 10))
        self.log_window.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border-radius: 5px;")
        self.log_window.setMaximumBlockCount(1000)
        bottom_layout.addWidget(self.log_window)
        
        main_layout.addWidget(bottom_frame)

        # 加载配置并自动扫描模型
        self.load_config_to_ui()
        saved_model_dir = self.controls["model_dir"].text()
        if saved_model_dir:
            self.scan_and_fill_models(saved_model_dir)

    # ========== 辅助方法 ==========

    def _make_card_frame(self):
        f = QFrame()
        f.setFrameShape(QFrame.StyledPanel)
        f.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 10px;")
        return f

    def _add_grid_fields(self, grid, fields, start_row):
        """将字段列表添加到网格布局（2列）"""
        for i, (label_text, key, ctrl_type, default) in enumerate(fields):
            row = start_row + i // 2
            col = i % 2
            
            lbl = QLabel(label_text)
            ctrl = None
            
            if ctrl_type == "text":
                ctrl = QLineEdit()
                grid.addWidget(lbl, row, col * 2)
                grid.addWidget(ctrl, row, col * 2 + 1)
            elif ctrl_type == "int":
                ctrl = QSpinBox()
                ctrl.setRange(0, 1000000)
                grid.addWidget(lbl, row, col * 2)
                grid.addWidget(ctrl, row, col * 2 + 1)
            elif ctrl_type == "bool":
                ctrl = QCheckBox()
                grid.addWidget(lbl, row, col * 2)
                grid.addWidget(ctrl, row, col * 2 + 1)
            elif ctrl_type == "combo":
                ctrl = QComboBox()
                ctrl.addItems(default)
                grid.addWidget(lbl, row, col * 2)
                grid.addWidget(ctrl, row, col * 2 + 1)
            
            if ctrl:
                self.controls[key] = ctrl

    def load_config_to_ui(self):
        for key, ctrl in self.controls.items():
            val = self.config_mgr.get(key)
            if isinstance(ctrl, QLineEdit):
                ctrl.setText(str(val))
            elif isinstance(ctrl, QSpinBox):
                ctrl.setValue(int(val))
            elif isinstance(ctrl, QCheckBox):
                ctrl.setChecked(bool(val))
            elif isinstance(ctrl, QComboBox):
                ctrl.setCurrentText(str(val))

    def update_hw_display(self):
        info = self.hw_info.get_all_info()
        cpu = info['cpu']
        mem = info['memory']
        gpu = info['gpu']
        self.cpu_label.setText(f"CPU: {cpu['model']} ({cpu['cores']}C/{cpu['threads']}T)")
        self.mem_label.setText(f"MEM: {mem['total']} {mem['arch']}")
        self.gpu_label.setText(f"GPU: {gpu['name']} ({gpu['vram']})")

    def browse_dir(self, key):
        start_path = self.controls[key].text()
        browser = DirectoryBrowser(start_path, self)
        def on_selected(path):
            self.controls[key].setText(path)
        browser.directory_selected.connect(on_selected)
        browser.exec()

    def browse_and_scan_models(self):
        start_path = self.controls["model_dir"].text()
        browser = DirectoryBrowser(start_path, self)
        def on_selected(path):
            self.controls["model_dir"].setText(path)
            self.scan_and_fill_models(path)
        browser.directory_selected.connect(on_selected)
        browser.exec()

    def scan_and_fill_models(self, directory):
        if not directory or not os.path.isdir(directory):
            return
        
        gguf_files = self.config_mgr.scan_gguf_files(directory)
        
        if not gguf_files:
            self.append_log(f"模型目录下未找到 .gguf 文件: {directory}", "WARN")
            return
        
        model_names = []
        for f in gguf_files:
            rel_path = os.path.relpath(f, directory)
            model_names.append(rel_path)
        
        current_main = self.controls["main_model"].currentText()
        current_vision = self.controls["vision_model"].currentText()
        
        combo_main = self.controls["main_model"]
        combo_main.clear()
        combo_main.addItems(model_names)
        
        combo_vision = self.controls["vision_model"]
        combo_vision.clear()
        combo_vision.addItem("")
        combo_vision.addItems(model_names)
        
        if current_main and current_main in model_names:
            combo_main.setCurrentText(current_main)
        if current_vision and current_vision in model_names:
            combo_vision.setCurrentText(current_vision)
        
        self.append_log(f"已扫描到 {len(model_names)} 个 .gguf 模型文件", "INFO")

    def append_log(self, text, level="INFO"):
        color_map = {"ERROR": "#f44336", "WARN": "#ffeb3b", "SYS": "#9c27b0", "INFO": "#4caf50"}
        color = color_map.get(level, "#d4d4d4")
        self.log_window.appendHtml(f'<span style="color: {color};">{text}</span>')
        self.log_window.moveCursor(QTextCursor.End)

    def handle_start(self):
        updated_config = {}
        for key, ctrl in self.controls.items():
            if isinstance(ctrl, QLineEdit):
                updated_config[key] = ctrl.text()
            elif isinstance(ctrl, QSpinBox):
                updated_config[key] = ctrl.value()
            elif isinstance(ctrl, QCheckBox):
                updated_config[key] = ctrl.isChecked()
            elif isinstance(ctrl, QComboBox):
                updated_config[key] = ctrl.currentText()
        
        self.config_mgr.save_config(updated_config)
        
        if self.proc_mgr.start(updated_config):
            self.btn_start.setEnabled(False)
            self.btn_start.setText("⏳ 运行中...")
            self.btn_stop.setEnabled(True)
            self.append_log("服务启动指令已发送，请等待初始化...", "INFO")
        else:
            self.append_log("启动失败，请检查配置路径。", "ERROR")

    def handle_stop(self):
        if self.proc_mgr.stop():
            self.btn_start.setEnabled(True)
            self.btn_start.setText("🚀 启动服务")
            self.btn_stop.setEnabled(False)
            self.append_log("服务已停止，显存已释放。", "WARN")
        else:
            self.append_log("停止服务失败。", "ERROR")