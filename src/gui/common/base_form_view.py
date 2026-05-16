from PySide6.QtCore import Qt
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

_BUTTON_MIN_WIDTH = 84


class BaseFormView(QWidget):
    def __init__(self, text_fields: list[str], group_name: str) -> None:
        super().__init__()
        self.text_fields = text_fields
        self.group_name = group_name
        self.form_inputs: dict[str, QWidget] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_form_group())
        layout.addLayout(self._build_crud_row())
        layout.addStretch()

    def setup_extra_fields(self, form: QFormLayout) -> None:
        pass

    def _build_form_group(self) -> QGroupBox:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        for field in self.text_fields:
            line_edit = QLineEdit()
            if field == "Date":
                line_edit.setPlaceholderText("YYYY-MM-DDTHH:MM:SS")
            self.form_inputs[field] = line_edit
            form.addRow(f"{field}:", line_edit)

        self.setup_extra_fields(form)

        group = QGroupBox(self.group_name)
        group.setLayout(form)
        return group

    def _build_crud_row(self) -> QHBoxLayout:
        self.create_btn = QPushButton("Create")
        self.create_btn.setObjectName("primary")
        self.update_btn = QPushButton("Update")
        self.delete_btn = QPushButton("Delete")
        self.clear_btn = QPushButton("Clear")

        row = QHBoxLayout()
        row.setSpacing(8)
        for button in (
            self.create_btn,
            self.update_btn,
            self.delete_btn,
            self.clear_btn,
        ):
            button.setMinimumWidth(_BUTTON_MIN_WIDTH)
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

    def populate(self, record: dict) -> None:
        for field, widget in self.form_inputs.items():
            value = "" if record.get(field) is None else str(record.get(field, ""))
            if isinstance(widget, QComboBox):
                # Fall back to the placeholder (index 0) when the stored value
                # isn't one of the combo's options — avoids silently keeping
                # whatever was selected before.
                idx = widget.findText(value)
                widget.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                widget.setText(value)

    def clear(self) -> None:
        for widget in self.form_inputs.values():
            if isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            else:
                widget.clear()
