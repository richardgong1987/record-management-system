from gui.common.base_form_controller import BaseFormController
from gui.flight.view import FlightFormView


class FlightFormController(BaseFormController):
    def __init__(self, view: FlightFormView) -> None:
        super().__init__(view)
