from gui.airline.view import AirlineFormView
from gui.common.base_form_controller import BaseFormController


class AirlineFormController(BaseFormController):
    def __init__(self, view: AirlineFormView) -> None:
        super().__init__(view)
