## Extensibility and Maintainability

The `RECORD_TYPES` dictionary in `src/gui/tab_registry.py` maps each record type to its form view, form controller, and column definitions, and the `build_tab` factory in the same module turns one entry into a fully wired tab. Adding a new record type requires only a single new entry, after which `MainWindow` picks it up automatically without changes to its own code.

This approach reflects the Open/Closed Principle from SOLID design, which states that software systems should remain open for extension while closed to modification (Martin, 2000). Centralising configuration in this way also improves maintainability by reducing duplicated setup logic. The JSONL storage format supports similar flexibility at the data layer, since new fields can be added without restructuring the file.
