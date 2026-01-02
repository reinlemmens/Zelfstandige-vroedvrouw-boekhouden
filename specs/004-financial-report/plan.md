# Implementation Plan: Financial Report Generation

**Branch**: `004-financial-report` | **Date**: 2026-01-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/rein/dev/PLVroedvrouwGoedele/specs/004-financial-report/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature will introduce a `plv report` command to generate a Profit & Loss (P&L) statement for a given fiscal year. The report will be based on existing transaction and depreciation data, and will be exportable to a formatted Excel file, similar to the `Resultatenrekening 2024.xlsx` example.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pandas, openpyxl, click, PyYAML
**Storage**: N/A (data is read from existing JSON files and exported)
**Testing**: pytest
**Target Platform**: CLI (macOS, Linux)
**Project Type**: Single project (CLI tool)
**Performance Goals**: Report generation for a year with ~500 transactions should complete in under 10 seconds.
**Constraints**: The Excel output format should be clean, professional, and easily digestible by an accountant.
**Scale/Scope**: The report will handle up to a few thousand transactions per year.

## Constitution Check

*This project does not have a formal constitution. Adhering to existing patterns and practices.*

- **Simplicity**: The solution will reuse existing services (`PersistenceService`, `DepreciationService`) and well-known libraries (`pandas`) to minimize new complexity.
- **CLI Interface**: The feature will be exposed as a new command within the existing `click`-based CLI.
- **Testability**: The reporting logic will be separated into a distinct service, allowing for unit testing with predictable inputs.

## Project Structure

### Documentation (this feature)

```text
specs/004-financial-report/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
src/
├── models/
│   └── report.py        # New: Data models for the report
├── services/
│   └── report_generator.py # New: Service to generate the P&L report
├── cli/
│   └── main.py          # Modified: Add the 'report' command
└── lib/

tests/
├── unit/
│   └── test_report_generator.py # New: Unit tests for the report generator
└── fixtures/
```

**Structure Decision**: The project will follow the existing single project structure. A new `report.py` model will be added to `src/models/`, and the core logic will be encapsulated in a new `report_generator.py` service in `src/services/`. The existing CLI entry point `src/cli/main.py` will be modified to include the new command.

## Complexity Tracking

N/A - No violations of project principles.