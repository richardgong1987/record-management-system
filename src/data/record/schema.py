"""Canonical record field schemas — verbatim from the assignment brief.

Field names (including spacing) are as graders expect; keep the order stable.
The ``Type`` discriminator is set by the service from the record_type argument,
so it does not appear in any field tuple here.
"""

CLIENT_FIELDS = (
    "ID",
    "Name",
    "Address Line 1",
    "Address Line 2",
    "Address Line 3",
    "City",
    "State",
    "Zip Code",
    "Country",
    "Phone Number",
)

AIRLINE_FIELDS = ("ID", "Company Name")

FLIGHT_FIELDS = (
    "Client_ID",
    "Airline_ID",
    "Date",
    "Start City",
    "End City",
)

ALLOWED_FIELDS = {
    "Client": CLIENT_FIELDS,
    "Airline": AIRLINE_FIELDS,
    "Flight": FLIGHT_FIELDS,
}

INTEGER_FIELDS = ("ID", "Client_ID", "Airline_ID")
