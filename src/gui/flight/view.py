from gui.common.base_form_view import BaseFormView
from gui.flight.types import FLIGHT_TEXT_FIELDS


class FlightFormView(BaseFormView):
    def __init__(self) -> None:
        super().__init__(text_fields=FLIGHT_TEXT_FIELDS, group_name="Flight Details")
