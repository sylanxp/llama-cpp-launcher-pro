import os
import platform
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, Signal

class DirectoryBrowser(QDialog):
    """
    高级目录浏览器：支持盘符检测、逐级导航、手动跳转
    """
    directory_selected = Signal(str)

    def __init__(self, start_path="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择目录")
        self.setMinimumSize(600, 400)
        self.current_path = start_path or os.path.expanduser("~")
        
        self.init_ui()
        self.update_list()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 顶部路径栏
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.current_path)
        self.btn_go = QPushButton("跳转")
        self.btn_go.clicked.connect(self.go_to_path)
        self.btn_back = QPushButton("⬅ 上一级")
        self.btn_back.clicked.connect(self.go_back)
        
        path_layout.addWidget(QLabel("路径:"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.btn_go)
        path_layout.addWidget(self.btn_back)
        layout.addLayout(path_layout)

        # 目录列表
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # 底部确认栏
        bottom_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("确认选择")
        self.btn_confirm.clicked.connect(self.confirm_selection)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addWidget(self.btn_confirm)
        layout.addLayout(bottom_layout)

    def get_root_drives(self):
        """获取 Windows 盘符"""
        if platform.system() == "Windows":
            import string
            drives = []
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
            return drives
        return ["/"]

    def update_list(self):
        """刷新当前目录下的内容"""
        self.list_widget.clear()
        
        # 1. 处理根目录/盘符
        if self.current_path in self.get_root_drives() or self.current_path == "/":
            # 如果在根目录，添加一个“返回根”的选项（如果需要）
            pass
        
        try:
            # 添加 ".." 返回上级
            item_back = QListWidgetItem(".. (上一级)")
            item_back.setData(Qt.UserRole, "BACK")
            self.list_widget.addItem(item_back)

            # 列出当前目录
            entries = os.listdir(self.current_path)
            # 排序：文件夹优先，然后按名称
            entries.sort(key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower()))
            
            for entry in entries:
                full_path = os.path.join(self.current_path, entry)
                icon_prefix = "📁 " if os.path.isdir(full_path) else "📄 "
                item = QListWidgetItem(f"{icon_prefix}{entry}")
                item.setData(Qt.UserRole, full_path)
                self.list_widget.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取目录: {e}")
            self.go_back()

    def on_item_double_clicked(self, item):
        path = item.data(Qt.UserRole)
        if path == "BACK":
            self.go_back()
        elif os.path.isdir(path):
            self.current_path = path
            self.path_edit.setText(self.current_path)
            self.update_list()
        else:
            # 点击文件时，自动选择该文件所在的目录
            self.current_path = os.path.dirname(path)
            self.path_edit.setText(self.current_path)
            self.update_list()

    def go_to_path(self):
        path = self.path_edit.text().strip()
        if os.path.exists(path) and os.path.isdir(path):
            self.current_path = path
            self.update_list()
        else:
            QMessageBox.warning(self, "无效路径", "请输入一个存在的目录路径")

    def go_back(self):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.current_path = parent
            self.path_edit.setText(self.current_path)
            self.update_list()

    def confirm_selection(self):
        self.directory_selected.emit(self.current_path)
        self.accept()
