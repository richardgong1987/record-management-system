from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.airline.types import AIRLINE_TEXT_FIELDS


class AirlineFormView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.form_inputs: dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._build_form_group())
        layout.addLayout(self._build_crud_row())

    def _build_form_group(self) -> QGroupBox:
        form = QFormLayout()
        for field in AIRLINE_TEXT_FIELDS:
            line_edit = QLineEdit()
            self.form_inputs[field] = line_edit
            form.addRow(f"{field}:", line_edit)

        group = QGroupBox("Airline Details")
        group.setLayout(form)
        return group

    def _build_crud_row(self) -> QHBoxLayout:
        self.create_btn = QPushButton("Create")
        self.update_btn = QPushButton("Update")
        self.delete_btn = QPushButton("Delete")
        self.clear_btn = QPushButton("Clear")

        row = QHBoxLayout()
        for button in (
            self.create_btn,
            self.update_btn,
            self.delete_btn,
            self.clear_btn,
        ):
            row.addWidget(button)
        row.addStretch()
        return row

    def read_payload(self) -> dict[str, str]:
        return {
            field: widget.text().strip() for field, widget in self.form_inputs.items()
        }

    def clear(self) -> None:
        for widget in self.form_inputs.values():
            widget.clear()
