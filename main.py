import sys
import os
import csv
import traceback

# 添加错误日志
def log_error(msg):
    with open("error.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()

def exc_handler(*args):
    import traceback
    log_error(traceback.format_exc())
    print(traceback.format_exc())

sys.excepthook = exc_handler

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QScrollArea, QFrame, QGridLayout, QFileDialog, QMessageBox, QProgressDialog,
    QTextEdit, QGroupBox, QMenuBar, QMenu, QAction, QStatusBar, QToolBar,
    QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont

from image_manager import ImageManager
from tag_generator import TagGenerator
from search_engine import SearchEngine
from metadata_storage import MetadataStorage
from ui_main import ImageItemWidget, TagSearchPanel, ImagePreviewPanel


class TagWorker(QThread):
    """后台标签生成线程"""
    finished = pyqtSignal(str, list)
    error = pyqtSignal(str, str)
    progress = pyqtSignal(int, int, str)

    def __init__(self, image_paths: list, api_url: str, model_name: str):
        super().__init__()
        self.image_paths = image_paths
        self.generator = TagGenerator(api_url, model_name)

    def run(self):
        total = len(self.image_paths)

        for i, path in enumerate(self.image_paths):
            # 先发出进度
            self.progress.emit(i + 1, total, os.path.basename(path))
            try:
                tags = self.generator.generate_tags(path)
            except Exception as e:
                print(f"生成标签出错: {e}")
                tags = []
            self.finished.emit(path, tags)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.root_folder = ""
        self.image_manager = ImageManager()
        self.storage = MetadataStorage()
        self.search_engine = SearchEngine()
        self.current_images = []  # 当前显示的图片列表
        self.selected_image_info = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("图片标签处理工具")
        self.setGeometry(100, 100, 1200, 800)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建工具栏
        self.create_toolbar()

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 搜索面板
        self.search_panel = TagSearchPanel()
        self.search_panel.search_triggered.connect(self.do_search)
        main_layout.addWidget(self.search_panel)

        # 主内容区域（左右分栏）
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：图片列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("图片列表"))
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(160, 140))
        self.image_list.setSpacing(10)
        self.image_list.itemClicked.connect(self.on_image_clicked)
        left_layout.addWidget(self.image_list)

        splitter.addWidget(left_widget)

        # 右侧：预览面板
        self.preview_panel = ImagePreviewPanel()
        splitter.addWidget(self.preview_panel)

        splitter.setSizes([600, 500])
        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def create_menu_bar(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        open_action = QAction("打开文件夹", self)
        open_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_action)

        export_action = QAction("导出CSV报告", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 操作菜单
        action_menu = menubar.addMenu("操作")

        import_action = QAction("导入图片", self)
        import_action.triggered.connect(self.import_images)
        action_menu.addAction(import_action)

        process_action = QAction("生成标签", self)
        process_action.triggered.connect(self.process_images)
        action_menu.addAction(process_action)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_btn = QPushButton("打开文件夹")
        open_btn.clicked.connect(self.open_folder)
        toolbar.addWidget(open_btn)

        import_btn = QPushButton("导入图片")
        import_btn.clicked.connect(self.import_images)
        toolbar.addWidget(import_btn)

        process_btn = QPushButton("生成标签")
        process_btn.clicked.connect(self.process_images)
        toolbar.addWidget(process_btn)

        toolbar.addSeparator()

        self.status_label = QLabel("未选择文件夹")
        toolbar.addWidget(self.status_label)

    def open_folder(self):
        """打开文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.root_folder = folder
            self.status_label.setText(f"当前: {folder}")
            self.load_images()

    def import_images(self):
        """导入图片"""
        if not self.root_folder:
            QMessageBox.warning(self, "警告", "请先选择一个文件夹！")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片",
            self.root_folder,
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp)"
        )

        if files:
            imported = 0
            for file_path in files:
                filename = os.path.basename(file_path)
                folder = self.root_folder
                dest_path = os.path.join(folder, filename)
                # 如果文件不存在则复制
                if not os.path.exists(dest_path):
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    imported += 1
                else:
                    # 文件已存在，也计入已处理
                    imported += 1

            QMessageBox.information(self, "完成", f"已加载 {imported} 张图片")
            self.load_images()

    def load_images(self):
        """加载图片列表"""
        self.image_list.clear()
        self.current_images = []

        if not self.root_folder:
            return

        all_images = []

        # 首先检查根文件夹本身是否有图片
        root_images = self.image_manager.get_images_in_folder(self.root_folder)
        if root_images:
            folder_name = os.path.basename(self.root_folder)
            for img in root_images:
                # 直接从图片EXIF读取标签
                info = self.storage.get_all_info(img["full_path"])
                tags = info.get("tags", []) if info else []

                img_info = {
                    "filename": img["filename"],
                    "folder": self.root_folder,
                    "folder_name": folder_name,
                    "full_path": img["full_path"],
                    "tags": tags,
                    "processed_at": info.get("processed_at", "") if info else "",
                    "model": info.get("model", "") if info else ""
                }
                all_images.append(img_info)

        # 遍历所有子文件夹
        for folder in self.image_manager.get_all_folders(self.root_folder):
            folder_name = os.path.basename(folder)
            folder_images = self.image_manager.get_images_in_folder(folder)

            for img in folder_images:
                # 直接从图片EXIF读取标签
                info = self.storage.get_all_info(img["full_path"])
                tags = info.get("tags", []) if info else []

                img_info = {
                    "filename": img["filename"],
                    "folder": folder,
                    "folder_name": folder_name,
                    "full_path": img["full_path"],
                    "tags": tags,
                    "processed_at": info.get("processed_at", "") if info else "",
                    "model": info.get("model", "") if info else ""
                }
                all_images.append(img_info)

        self.current_images = all_images

        # 显示图片
        for img_info in all_images:
            if os.path.exists(img_info["full_path"]):
                item = QListWidgetItem()
                widget = ImageItemWidget(img_info)
                widget.clicked.connect(self.on_image_clicked)
                item.setSizeHint(QSize(170, 200))
                self.image_list.addItem(item)
                self.image_list.setItemWidget(item, widget)

        # 统计已处理和未处理数量
        processed_count = sum(1 for img in all_images if img["tags"])
        total_count = len(all_images)
        self.status_bar.showMessage(f"共 {total_count} 张图片，已处理 {processed_count} 张")

    def on_image_clicked(self, full_path):
        """图片点击事件"""
        # 找到对应的图片信息
        for img_info in self.current_images:
            if img_info["full_path"] == full_path:
                self.preview_panel.show_image(img_info)
                self.selected_image_info = img_info
                break

    def process_images(self):
        """处理图片生成标签"""
        if not self.root_folder:
            QMessageBox.warning(self, "警告", "请先选择一个文件夹！")
            return

        # 获取所有未处理的图片
        all_images = []

        # 首先检查根文件夹
        root_images = self.image_manager.get_images_in_folder(self.root_folder)
        for img in root_images:
            # 从图片EXIF读取标签
            info = self.storage.get_all_info(img["full_path"])
            existing_tags = info.get("tags", []) if info else []
            if not existing_tags:
                all_images.append(img["full_path"])

        # 然后检查子文件夹
        for folder in self.image_manager.get_all_folders(self.root_folder):
            folder_images = self.image_manager.get_images_in_folder(folder)
            for img in folder_images:
                # 从图片EXIF读取标签
                info = self.storage.get_all_info(img["full_path"])
                existing_tags = info.get("tags", []) if info else []
                if not existing_tags:
                    all_images.append(img["full_path"])

        if not all_images:
            QMessageBox.information(self, "提示", "所有图片都已处理完成！")
            return

        # 显示进度对话框
        progress = QProgressDialog("正在生成标签...", "取消", 0, len(all_images), self)
        progress.setWindowModality(Qt.NonModal)
        progress.setAutoClose(False)
        progress.setMinimumDuration(0)

        def on_progress(current, total, filename):
            progress.setLabelText(f"正在处理: {filename}")
            progress.setValue(current - 1)
            # 让UI更新
            QApplication.processEvents()

        def on_finished(path, tags):
            # 将标签写入图片EXIF
            self.storage.save_tags(path, tags)
            current = progress.value() + 1
            progress.setValue(current)
            QApplication.processEvents()
            if current >= len(all_images):
                progress.close()
                self.load_images()  # 刷新显示

        # 启动工作线程
        worker = TagWorker(all_images, "http://localhost:1234/v1", "qwen3.5-9b")
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.start()

        progress.show()

    def do_search(self, query_tags: list, logic: str):
        """执行搜索"""
        if not self.root_folder:
            QMessageBox.warning(self, "警告", "请先选择一个文件夹！")
            return

        results = self.search_engine.search(self.root_folder, query_tags, logic)

        # 显示搜索结果
        self.image_list.clear()

        for img_info in results:
            if os.path.exists(img_info["full_path"]):
                item = QListWidgetItem()
                widget = ImageItemWidget(img_info)
                widget.clicked.connect(self.on_image_clicked)
                item.setSizeHint(QSize(170, 200))
                self.image_list.addItem(item)
                self.image_list.setItemWidget(item, widget)

        self.status_bar.showMessage(f"找到 {len(results)} 张图片")

    def export_csv(self):
        """导出CSV报告"""
        if not self.root_folder:
            QMessageBox.warning(self, "警告", "请先选择一个文件夹！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件",
            os.path.join(self.root_folder, "tags_report.csv"),
            "CSV文件 (*.csv)"
        )

        if not file_path:
            return

        # 收集所有图片信息
        all_images = []
        for folder_info in self.storage.scan_folders(self.root_folder):
            for img in folder_info["images"]:
                all_images.append({
                    "filename": img["filename"],
                    "folder": folder_info["folder_name"],
                    "tags": ", ".join(img.get("tags", [])),
                    "processed_at": img.get("processed_at", ""),
                    "model": img.get("model", "")
                })

        # 写入CSV
        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["filename", "folder", "tags", "processed_at", "model"])
                writer.writeheader()
                writer.writerows(all_images)

            QMessageBox.information(self, "完成", f"已导出 {len(all_images)} 条记录到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
