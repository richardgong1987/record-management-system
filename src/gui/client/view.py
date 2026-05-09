from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
)

from gui.client.types import CLIENT_TEXT_FIELDS, COUNTRIES
from gui.common.base_form_view import BaseFormView


class ClientFormView(BaseFormView):
    def __init__(self) -> None:
        super().__init__(text_fields=CLIENT_TEXT_FIELDS, group_name="Client Details")

    def setup_extra_fields(self, form: QFormLayout) -> None:
        country = QComboBox()
        country.addItems(COUNTRIES)
        self.form_inputs["Country"] = country
        form.addRow("Country:", country)
