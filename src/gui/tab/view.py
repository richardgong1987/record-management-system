from PySide6.QtWidgets import QHBoxLayout, QWidget

from gui.record_list.view import RecordListView


class TabView(QWidget):
    def __init__(self, form: QWidget, record_list: RecordListView) -> None:
        super().__init__()
        self.form = form
        self.record_list = record_list

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        layout.addWidget(form, stretch=1)
        layout.addWidget(record_list, stretch=2)
