from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem, QScrollArea,
    QFrame, QGridLayout, QFileDialog, QMessageBox, QProgressDialog,
    QTextEdit, QGroupBox, QCheckBox, QSplitter, QStatusBar, QMenuBar,
    QMenu, QAction, QToolBar
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont
from PIL import Image
import os


class ImageItemWidget(QWidget):
    """图片列表项组件"""
    clicked = pyqtSignal(str)

    def __init__(self, image_info: dict, parent=None):
        super().__init__(parent)
        self.image_info = image_info
        self.full_path = image_info["full_path"]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 图片预览
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(150, 120)
        self.image_label.setMaximumSize(150, 120)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.load_thumbnail()
        layout.addWidget(self.image_label)

        # 文件名
        name_label = QLabel(self.image_info["filename"])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(name_label)

        # 标签预览
        tags = self.image_info.get("tags", [])
        if tags:
            tags_text = ", ".join(tags[:3])
            if len(tags) > 3:
                tags_text += "..."
            tags_label = QLabel(tags_text)
            tags_label.setAlignment(Qt.AlignCenter)
            tags_label.setStyleSheet("font-size: 9px; color: #666;")
            tags_label.setWordWrap(True)
            layout.addWidget(tags_label)

        self.setLayout(layout)
        self.setFixedWidth(160)

    def load_thumbnail(self):
        """加载缩略图"""
        try:
            pixmap = QPixmap(self.full_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(150, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("无法加载")
        except Exception as e:
            self.image_label.setText("加载失败")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.full_path)
        super().mousePressEvent(event)


class TagSearchPanel(QWidget):
    """标签搜索面板"""
    search_triggered = pyqtSignal(list, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_conditions = []  # 存储搜索条件
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索输入行
        input_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入标签搜索...")
        self.search_input.returnPressed.connect(self.add_condition)
        input_layout.addWidget(self.search_input)

        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["AND", "OR"])
        input_layout.addWidget(self.logic_combo)

        add_btn = QPushButton("+")
        add_btn.setFixedWidth(30)
        add_btn.clicked.connect(self.add_condition)
        input_layout.addWidget(add_btn)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.do_search)
        input_layout.addWidget(search_btn)

        layout.addLayout(input_layout)

        # 搜索条件显示
        self.conditions_label = QLabel("当前条件: (无)")
        self.conditions_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.conditions_label)

        # 清除按钮
        clear_btn = QPushButton("清除条件")
        clear_btn.clicked.connect(self.clear_conditions)
        layout.addWidget(clear_btn)

        self.setLayout(layout)

    def add_condition(self):
        """添加搜索条件"""
        tag = self.search_input.text().strip()
        if tag:
            if tag not in self.search_conditions:
                self.search_conditions.append(tag)
                self.update_conditions_label()
            self.search_input.clear()

    def update_conditions_label(self):
        """更新条件显示"""
        if self.search_conditions:
            logic = self.logic_combo.currentText()
            self.conditions_label.setText(
                f"当前条件: {' ' + logic + ' '.join(self.search_conditions)}"
            )
        else:
            self.conditions_label.setText("当前条件: (无)")

    def clear_conditions(self):
        """清除所有条件"""
        self.search_conditions.clear()
        self.update_conditions_label()

    def do_search(self):
        """执行搜索"""
        if self.search_conditions:
            logic = self.logic_combo.currentText()
            self.search_triggered.emit(self.search_conditions, logic)


class ImagePreviewPanel(QWidget):
    """图片预览面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_image = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # 大图预览
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("border: 1px solid #ddd; background: #f9f9f9;")
        self.preview_label.setText("点击图片查看预览")
        layout.addWidget(self.preview_label)

        # 标签显示
        tags_group = QGroupBox("标签")
        tags_layout = QVBoxLayout()

        self.tags_label = QLabel("")
        self.tags_label.setWordWrap(True)
        tags_layout.addWidget(self.tags_label)

        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)

        # 图片信息
        info_group = QGroupBox("信息")
        info_layout = QVBoxLayout()

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 11px; color: #666;")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        self.setLayout(layout)

    def show_image(self, image_info: dict):
        """显示图片信息"""
        self.current_image = image_info

        # 加载图片
        full_path = image_info["full_path"]
        try:
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                # 缩放到合适大小
                scaled = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled)
        except Exception as e:
            self.preview_label.setText(f"加载失败: {e}")

        # 显示标签
        tags = image_info.get("tags", [])
        if tags:
            self.tags_label.setText(", ".join(tags))
        else:
            self.tags_label.setText("(未打标签)")

        # 显示信息
        filename = image_info.get("filename", "")
        folder = image_info.get("folder_name", "")
        processed = image_info.get("processed_at", "")
        info_text = f"文件名: {filename}\n"
        info_text += f"文件夹: {folder}\n"
        if processed:
            info_text += f"处理时间: {processed}"
        self.info_label.setText(info_text)

    def clear(self):
        """清空预览"""
        self.preview_label.clear()
        self.preview_label.setText("点击图片查看预览")
        self.tags_label.setText("")
        self.info_label.setText("")
        self.current_image = None
