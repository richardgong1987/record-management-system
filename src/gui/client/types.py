CLIENT_TEXT_FIELDS = [
    "ID",
    "Name",
    "Phone Number",
    "Address Line 1",
    "Address Line 2",
    "Address Line 3",
    "City",
    "State",
    "Zip Code",
]

CLIENT_TABLE_COLUMNS = CLIENT_TEXT_FIELDS + ["Country"]

# Placeholder is the first item so the validator (future) can reject it on submit.
COUNTRIES = ["-- select --", "USA", "UK", "Canada"]
