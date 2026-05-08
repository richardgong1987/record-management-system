from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.client.types import CLIENT_TEXT_FIELDS, COUNTRIES


class ClientFormView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.form_inputs: dict[str, QWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._build_form_group())
        layout.addLayout(self._build_crud_row())

    def _build_form_group(self) -> QGroupBox:
        form = QFormLayout()
        for field in CLIENT_TEXT_FIELDS:
            line_edit = QLineEdit()
            self.form_inputs[field] = line_edit
            form.addRow(f"{field}:", line_edit)

        country = QComboBox()
        country.addItems(COUNTRIES)
        self.form_inputs["Country"] = country
        form.addRow("Country:", country)

        group = QGroupBox("Client Details")
        group.setLayout(form)
        return group

    def _build_crud_row(self) -> QHBoxLayout:
        self.create_btn = QPushButton("Create")
        self.update_btn = QPushButton("Update")
        self.delete_btn = QPushButton("Delete")
        self.clear_btn = QPushButton("Clear")

        row = QHBoxLayout()
        for button in (self.create_btn, self.update_btn, self.delete_btn, self.clear_btn):
            row.addWidget(button)
        row.addStretch()
        return row

    def read_payload(self) -> dict[str, str]:
        payload: dict[str, str] = {}
        for field, widget in self.form_inputs.items():
            if isinstance(widget, QComboBox):
                payload[field] = widget.currentText()
            else:
                payload[field] = widget.text().strip()
        return payload

    def clear(self) -> None:
        for widget in self.form_inputs.values():
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            else:
                widget.clear()
