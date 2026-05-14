# Introduction and Overview

This project involves the design and development of a desktop Record Management System for a specialist travel agent. The system manages three categories of records: clients, airline companies, and flights. Client records store customer information such as names, addresses, and contact details, while airline records contain company information. Flight records connect clients with airlines and store journey details including departure city, destination city, and travel date.

The application supports four core record management operations through a Graphical User Interface (GUI): creating, updating, deleting, and searching records. During execution, records are stored in memory as a list of dictionaries and saved to the file system using JSONL format. On startup, the application checks for an existing data file and loads previously saved records. JSONL was selected because it stores records independently, making the data easier to manage and extend.
