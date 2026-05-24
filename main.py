import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # 创建 Qt 应用程序
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # 使用统一的 Fusion 风格，确保在所有 Windows 版本上外观一致
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 执行事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
