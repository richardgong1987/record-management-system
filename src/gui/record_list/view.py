from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.styles import search_icon


class RecordListView(QWidget):
    def __init__(self, columns: list[str]) -> None:
        super().__init__()
        self._columns = columns
        self._build_widgets()
        self._compose_layout()

    def _build_widgets(self) -> None:
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.addAction(search_icon(), QLineEdit.LeadingPosition)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("primary")
        self.show_all_btn = QPushButton("Show All")

        self.table = QTableWidget(0, len(self._columns))
        self.table.setHorizontalHeaderLabels(self._columns)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setDefaultSectionSize(30)

        self.prev_btn = QPushButton("‹ Previous")
        self.next_btn = QPushButton("Next ›")
        self.page_lbl = QLabel("Page 1")
        self.page_lbl.setStyleSheet("color: #52606D; font-weight: 600;")

    def _compose_layout(self) -> None:
        inner = QVBoxLayout()
        inner.setContentsMargins(8, 4, 8, 8)
        inner.setSpacing(10)
        inner.addLayout(self._build_search_row())
        inner.addWidget(self.table)
        inner.addLayout(self._build_pager_row())

        group = QGroupBox("Record List")
        group.setLayout(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(group)

    def _build_search_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.search_input, stretch=1)
        row.addWidget(self.search_btn)
        row.addWidget(self.show_all_btn)
        return row

    def _build_pager_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self.prev_btn)
        row.addStretch()
        row.addWidget(self.page_lbl, alignment=Qt.AlignCenter)
        row.addStretch()
        row.addWidget(self.next_btn)
        return row

    def current_query(self) -> str:
        return self.search_input.text().strip()

    def set_rows(self, rows: list[dict[str, str]]) -> None:
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, col in enumerate(self._columns):
                item = QTableWidgetItem(str(row.get(col, "")))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(r, c, item)

    def set_page_label(self, current: int, total: int) -> None:
        self.page_lbl.setText(f"Page {current} of {total}")
