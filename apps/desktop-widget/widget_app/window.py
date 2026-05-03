from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from widget_app.api import normalize_api_base, verify_widget_token
from widget_app.config import (
    WidgetConfig,
    get_config_file_path,
    load_config,
    mask_token,
    save_config,
)


class WidgetWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Personal System Desktop Widget")
        self.resize(640, 520)
        self.summary_preview_value: QLabel | None = None
        self._build_ui()
        self._load_initial_config()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(16)

        title = QLabel("桌面小工具接入")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        description = QLabel("把桌面端主程序生成的 `widget_basic` 凭证粘贴到这里，然后保存并测试。")
        description.setWordWrap(True)

        form_card = QFrame()
        form_card.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_card)

        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("http://127.0.0.1:8000/api/v1")

        self.widget_name_input = QLineEdit()
        self.widget_name_input.setPlaceholderText("Personal System Widget")

        self.token_input = QPlainTextEdit()
        self.token_input.setPlaceholderText("请粘贴桌面端主程序生成的小工具 Token")
        self.token_input.setMaximumBlockCount(20)
        self.token_input.setFixedHeight(120)

        form_layout.addRow("API 基地址", self.api_base_input)
        form_layout.addRow("小工具名称", self.widget_name_input)
        form_layout.addRow("设备令牌", self.token_input)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("保存配置")
        self.reload_button = QPushButton("重新读取")
        self.verify_button = QPushButton("验证凭证")
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.reload_button)
        button_row.addStretch(1)
        button_row.addWidget(self.verify_button)

        info_card = QFrame()
        info_card.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QFormLayout(info_card)

        self.config_path_value = QLabel()
        self.config_path_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.token_preview_value = QLabel()
        self.token_preview_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.status_value = QLabel("尚未验证")
        self.status_value.setWordWrap(True)

        self.summary_preview_value = QLabel("尚未获取摘要")
        self.summary_preview_value.setWordWrap(True)
        self.summary_preview_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        info_layout.addRow("配置文件", self.config_path_value)
        info_layout.addRow("Token 摘要", self.token_preview_value)
        info_layout.addRow("验证状态", self.status_value)
        info_layout.addRow("摘要预览", self.summary_preview_value)

        root_layout.addWidget(title)
        root_layout.addWidget(description)
        root_layout.addWidget(form_card)
        root_layout.addLayout(button_row)
        root_layout.addWidget(info_card)
        root_layout.addStretch(1)

        self.save_button.clicked.connect(self._save_current_config)
        self.reload_button.clicked.connect(self._load_initial_config)
        self.verify_button.clicked.connect(self._verify_current_token)
        self.token_input.textChanged.connect(self._refresh_token_preview)

    def _load_initial_config(self) -> None:
        config = load_config()
        self.api_base_input.setText(config.api_base_url)
        self.widget_name_input.setText(config.widget_name)
        self.token_input.setPlainText(config.auth_token)
        self.config_path_value.setText(str(get_config_file_path()))
        self.status_value.setText("已加载本地配置，尚未验证")
        if self.summary_preview_value is not None:
            self.summary_preview_value.setText("尚未获取摘要")
        self._refresh_token_preview()

    def _collect_config(self) -> WidgetConfig:
        return WidgetConfig(
            api_base_url=normalize_api_base(self.api_base_input.text()),
            widget_name=self.widget_name_input.text().strip() or "Personal System Widget",
            auth_token=self.token_input.toPlainText().strip(),
        )

    def _refresh_token_preview(self) -> None:
        self.token_preview_value.setText(mask_token(self.token_input.toPlainText()))

    def _save_current_config(self) -> None:
        config = self._collect_config()
        config_path = save_config(config)
        self.status_value.setText("配置已保存")
        self._refresh_token_preview()
        QMessageBox.information(self, "保存成功", f"配置已保存到：\n{config_path}")

    def _verify_current_token(self) -> None:
        config = self._collect_config()
        result = verify_widget_token(
            api_base_url=config.api_base_url,
            token=config.auth_token,
        )
        self.status_value.setText(result.detail)
        if self.summary_preview_value is not None:
            if result.ok:
                self.summary_preview_value.setText(
                    f"当前用户：{result.username or '未知'} | 待办：{result.pending_count} | "
                    f"今日到期：{result.due_today_count} | 已逾期：{result.overdue_count}"
                )
            else:
                self.summary_preview_value.setText("未能获取小工具摘要")
        if result.ok:
            QMessageBox.information(self, "验证成功", result.detail)
            return
        QMessageBox.warning(self, "验证失败", result.detail)
