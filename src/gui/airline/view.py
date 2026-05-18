from gui.airline.types import AIRLINE_TEXT_FIELDS
from gui.common.base_form_view import BaseFormView


class AirlineFormView(BaseFormView):
    def __init__(self) -> None:
        super().__init__(
            text_fields=AIRLINE_TEXT_FIELDS,
            group_name="Airline Details",
            read_only_fields=["ID"],
        )
