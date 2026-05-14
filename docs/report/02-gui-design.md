## GUI Design

Before development began, the team considered three interface designs for the Record Management System.

Option 1 used a single-window layout with a record-type dropdown, form panel, records table, colour-coded buttons, and status bar. Although compact, combining all record types within one shared workspace risked reducing clarity and making navigation confusing.

Option 2 proposed a dashboard-style interface with a dark sidebar, navigation trail, status badges, city filters, and export functionality. However, this design exceeded the intended scope of a desktop Python application.

The team therefore selected Option 3, which uses separate tabs for Client, Airline, and Flight records. Each tab contains an input form beside a paginated records table, with a status bar positioned beneath the interface.

PySide6 was chosen over Tkinter because its built-in widgets, including `QTabWidget`, `QTableWidget`, `QFormLayout`, and `QStatusBar`, simplified implementation while supporting a cleaner and more structured interface for both developers and users during routine system interaction.
