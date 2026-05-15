## Extensibility and Maintainability

The `_RECORD_TYPES` dictionary in `MainWindow` maps each record type to its form view, controller, and column definitions. Adding a new record type requires only a single new entry, after which the corresponding tab is created automatically without modifying other parts of the application.

This approach reflects the Open/Closed Principle from SOLID design, which states that software systems should remain open for extension while closed to modification (Martin, 2000). Centralising configuration in this way also improves maintainability by reducing duplicated setup logic. The JSONL storage format supports similar flexibility at the data layer, since new fields can be added without restructuring the file.
