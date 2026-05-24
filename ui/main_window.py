import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, 
    QCheckBox, QPlainTextEdit, QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont, QColor, QTextCursor

from core.config import ConfigManager
from core.hardware import HardwareInfo
from core.process_manager import ProcessManager
from ui.file_browser import DirectoryBrowser

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Llama.cpp Launcher Pro")
        self.setMinimumSize(900, 700)
        
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
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- 1. 硬件信息卡片 ---
        hw_frame = QFrame()
        hw_frame.setFrameShape(QFrame.StyledPanel)
        hw_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 10px;")
        hw_layout = QHBoxLayout(hw_frame)
        
        self.cpu_label = QLabel("CPU: 检测中...")
        self.mem_label = QLabel("MEM: 检测中...")
        self.gpu_label = QLabel("GPU: 检测中...")
        self.btn_refresh_hw = QPushButton("刷新")
        self.btn_refresh_hw.setFixedWidth(60)
        self.btn_refresh_hw.clicked.connect(self.update_hw_display)
        
        hw_layout.addWidget(self.cpu_label)
        hw_layout.addWidget(self.mem_label)
        hw_layout.addWidget(self.gpu_label)
        hw_layout.addStretch()
        hw_layout.addWidget(self.btn_refresh_hw)
        
        main_layout.addWidget(hw_frame)

        # --- 2. 参数配置区 ---
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setFrameShape(QFrame.NoFrame)
        
        config_container = QWidget()
        config_grid = QGridLayout(config_container)
        config_grid.setSpacing(10)

        self.controls = {}

        # 第一行：Llama.cpp 目录 (带浏览)
        row = 0
        lbl = QLabel("Llama.cpp 目录")
        ctrl = QLineEdit()
        btn_browse = QPushButton("浏览")
        btn_browse.setFixedWidth(60)
        btn_browse.clicked.connect(lambda: self.browse_dir("llama_dir"))
        hbox = QHBoxLayout()
        hbox.addWidget(ctrl)
        hbox.addWidget(btn_browse)
        config_grid.addWidget(lbl, row, 0)
        config_grid.addLayout(hbox, row, 1)
        self.controls["llama_dir"] = ctrl

        # 第二行：模型目录 (带浏览，选择后自动扫描 .gguf)
        row = 1
        lbl = QLabel("模型目录")
        ctrl = QLineEdit()
        btn_browse = QPushButton("浏览")
        btn_browse.setFixedWidth(60)
        btn_browse.clicked.connect(lambda: self.browse_and_scan_models())
        hbox = QHBoxLayout()
        hbox.addWidget(ctrl)
        hbox.addWidget(btn_browse)
        config_grid.addWidget(lbl, row, 0)
        config_grid.addLayout(hbox, row, 1)
        self.controls["model_dir"] = ctrl

        # 第三行：主模型 (下拉选择)
        row = 2
        lbl = QLabel("主模型")
        ctrl = QComboBox()
        ctrl.setEditable(True)
        ctrl.setPlaceholderText("请先选择模型目录...")
        config_grid.addWidget(lbl, row, 0)
        config_grid.addWidget(ctrl, row, 1)
        self.controls["main_model"] = ctrl

        # 第四行：视觉模型 (下拉选择)
        row = 3
        lbl = QLabel("视觉模型")
        ctrl = QComboBox()
        ctrl.setEditable(True)
        ctrl.setPlaceholderText("请先选择模型目录...")
        config_grid.addWidget(lbl, row, 0)
        config_grid.addWidget(ctrl, row, 1)
        self.controls["vision_model"] = ctrl

        # 其他参数：两列网格
        fields = [
            ("Context Size", "ctx_size", "int", 4096),
            ("GPU Layers (ngl)", "ngl", "int", 99),
            ("CPU Threads", "threads", "int", 4),
            ("Batch Size", "batch", "int", 512),
            ("UBatch Size", "ubatch", "int", 512),
            ("Parallel (np)", "np", "int", 1),
            ("Cache K Type", "cache_k", "combo", ["f16", "q8_0", "q4_0"]),
            ("Cache V Type", "cache_v", "combo", ["f16", "q8_0", "q4_0"]),
            ("Image Tokens", "img_tokens", "int", 1024),
            ("Server Port", "port", "int", 8080),
            ("监听模式", "listen_mode", "combo", ["local", "lan", "custom"]),
            ("自定义 Host", "custom_host", "text", "127.0.0.1"),
            ("附加参数", "extra_args", "text", ""),
            ("自动重启", "auto_restart", "bool", False),
            ("检测方式", "detect_method", "combo", ["api", "log"]),
            ("重启延迟(s)", "restart_interval", "int", 3),
            ("Memory Lock", "mlock", "bool", False),
            ("Flash Attention", "flash_attn", "bool", True),
        ]

        start_row = 4
        for i, (label_text, key, ctrl_type, default) in enumerate(fields):
            row = start_row + i // 2
            col = i % 2
            
            lbl = QLabel(label_text)
            ctrl = None
            
            if ctrl_type == "text":
                ctrl = QLineEdit()
                config_grid.addWidget(lbl, row, col * 2)
                config_grid.addWidget(ctrl, row, col * 2 + 1)
                
            elif ctrl_type == "int":
                ctrl = QSpinBox()
                ctrl.setRange(0, 1000000)
                config_grid.addWidget(lbl, row, col * 2)
                config_grid.addWidget(ctrl, row, col * 2 + 1)
                
            elif ctrl_type == "bool":
                ctrl = QCheckBox()
                config_grid.addWidget(lbl, row, col * 2)
                config_grid.addWidget(ctrl, row, col * 2 + 1)
                
            elif ctrl_type == "combo":
                ctrl = QComboBox()
                ctrl.addItems(default)
                config_grid.addWidget(lbl, row, col * 2)
                config_grid.addWidget(ctrl, row, col * 2 + 1)
            
            if ctrl:
                self.controls[key] = ctrl

        config_scroll.setWidget(config_container)
        main_layout.addWidget(config_scroll)

        # --- 3. 底部控制与日志 ---
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
        bottom_layout.addWidget(self.log_window)
        
        main_layout.addWidget(bottom_frame)
        
        # 加载保存的配置
        self.load_config_to_ui()
        
        # 如果已有模型目录，自动扫描模型
        saved_model_dir = self.controls["model_dir"].text()
        if saved_model_dir:
            self.scan_and_fill_models(saved_model_dir)

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
        """选择模型目录后自动扫描 .gguf 文件"""
        start_path = self.controls["model_dir"].text()
        browser = DirectoryBrowser(start_path, self)
        
        def on_selected(path):
            self.controls["model_dir"].setText(path)
            self.scan_and_fill_models(path)
        
        browser.directory_selected.connect(on_selected)
        browser.exec()

    def scan_and_fill_models(self, directory):
        """扫描目录并填充主模型和视觉模型下拉框"""
        if not directory or not os.path.isdir(directory):
            return
        
        gguf_files = self.config_mgr.scan_gguf_files(directory)
        
        if not gguf_files:
            self.append_log(f"模型目录下未找到 .gguf 文件: {directory}", "WARN")
            return
        
        # 提取相对路径（相对于模型目录）
        model_names = []
        for f in gguf_files:
            rel_path = os.path.relpath(f, directory)
            model_names.append(rel_path)
        
        # 保存当前选中的值
        current_main = self.controls["main_model"].currentText()
        current_vision = self.controls["vision_model"].currentText()
        
        # 填充主模型下拉框
        combo_main = self.controls["main_model"]
        combo_main.clear()
        combo_main.addItems(model_names)
        
        # 填充视觉模型下拉框
        combo_vision = self.controls["vision_model"]
        combo_vision.clear()
        combo_vision.addItem("")  # 空选项表示不使用视觉模型
        combo_vision.addItems(model_names)
        
        # 恢复之前选中的值
        if current_main and current_main in model_names:
            combo_main.setCurrentText(current_main)
        if current_vision and current_vision in model_names:
            combo_vision.setCurrentText(current_vision)
        
        self.append_log(f"已扫描到 {len(model_names)} 个 .gguf 模型文件", "INFO")

    def append_log(self, text, level="INFO"):
        color = "#d4d4d4"
        if level == "ERROR": color = "#f44336"
        elif level == "WARN": color = "#ffeb3b"
        elif level == "SYS": color = "#9c27b0"
        elif level == "INFO": color = "#4caf50"
        
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
            self.btn_start.setText("运行中...")
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