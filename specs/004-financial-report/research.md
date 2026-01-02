# Research: Financial Report Generation

## Decision: Use `pandas` for report generation and `openpyxl` for Excel styling.

- **Rationale**: `pandas` is already a project dependency and is the industry standard in Python for data manipulation and analysis. It can easily group transactions by category and perform the necessary aggregations. `openpyxl` is also a dependency and provides fine-grained control over Excel worksheet styling, which will be necessary to meet the requirement for a "clean and professional" layout with formatted currency values and formulas.

- **Alternatives considered**:
  - **Manual CSV/Excel generation**: Using Python's built-in `csv` module or a simpler library like `XlsxWriter`. Rejected because `pandas` provides a much higher-level API for the required data aggregation, reducing the amount of boilerplate code. `XlsxWriter` is a good alternative to `openpyxl`, but since `openpyxl` is already in use by `pandas`, it's simpler to use it directly for styling.
  - **HTML report**: Generating an HTML report. Rejected because the spec explicitly requires an Excel output for sharing with an accountant, which is a standard practice.
