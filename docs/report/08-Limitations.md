## Limitations

The current version has several limitations:

- Client data is stored in a plain-text JSONL file with no encryption or access control, making the system unsuitable for live deployment environments handling sensitive personal information.

- All records are loaded into memory during application startup. While suitable for small datasets, this approach may become inefficient as record volumes increase and could affect scalability and performance.
