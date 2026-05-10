from gui.client.view import ClientFormView
from gui.common.base_form_controller import BaseFormController


class ClientFormController(BaseFormController):
    def __init__(self, view: ClientFormView) -> None:
        super().__init__(view)
