# Implementation Plan: Asset Depreciation Tracking

**Branch**: `003-asset-depreciation` | **Date**: 2026-01-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-asset-depreciation/spec.md`

## Summary

Add multi-year depreciation tracking for business assets (bike, phone, etc.) to the PLV tool. Assets are registered with purchase date, amount, and depreciation period. The system calculates annual write-offs using straight-line depreciation (full years, no pro-rating) and integrates totals into the P&L "afschrijvingen" category.

Key deliverables:
1. Asset data model and persistence (`data/assets.json`)
2. CLI commands: `plv assets add`, `plv assets list`, `plv assets depreciation`, `plv assets dispose`
3. One-time Excel import from Resultaat sheet
4. P&L integration via depreciation service

## Technical Context

**Language/Version**: Python 3.11+ (matches existing project)
**Primary Dependencies**: Click (CLI), PyYAML (config), openpyxl (Excel import), pandas (data processing)
**Storage**: JSON file (`data/assets.json`) - consistent with transactions.json pattern
**Testing**: pytest (existing setup)
**Target Platform**: macOS/Linux CLI (local execution)
**Project Type**: Single project (extends existing `src/` structure)
**Performance Goals**: Sub-second CLI response for all operations
**Constraints**: All data must be local files, no external services
**Scale/Scope**: ~10-50 assets per user, 3-10 year depreciation periods

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Data Integrity | PASS | Assets reference source (Excel import or manual with notes). Calculations are deterministic (straight-line, full years). |
| II. Belgian Tax Compliance | PASS | Aligns with "Afschrijvingen" category. EUR amounts. Calendar year fiscal periods. Straight-line method per Belgian SME standards. |
| III. Transparency & Auditability | PASS | Asset list shows all fields including purchase_date, depreciation_years. Schedule shows how each write-off is calculated. |
| IV. User Control | PASS | User explicitly registers each asset with description, dates, periods. Disposal requires explicit action. No auto-assumptions. |
| V. Simplicity | PASS | Python CLI, JSON storage, YAML for any config. No new dependencies beyond existing project. |

**Gate Result**: PASS - All principles satisfied. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/003-asset-depreciation/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli.md           # CLI command contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── asset.py         # NEW: Asset dataclass
│   └── ...              # Existing models
├── services/
│   ├── asset_service.py      # NEW: Asset CRUD operations
│   ├── depreciation.py       # NEW: Depreciation calculations
│   ├── asset_importer.py     # NEW: Excel import from Resultaat sheet
│   └── persistence.py        # EXTEND: Add asset load/save methods
├── cli/
│   └── main.py          # EXTEND: Add 'assets' command group
└── lib/
    └── ...              # Existing utilities

data/
├── output/
│   ├── transactions.json    # Existing
│   └── assets.json          # NEW: Asset persistence
└── 2025/                    # Source Excel files

config/
├── categories.yaml      # Existing (includes 'afschrijvingen')
└── ...
```

**Structure Decision**: Extends existing single-project structure. New files for asset model, services, and CLI commands. Persistence service extended to handle assets.

## Complexity Tracking

> No violations - Constitution Check passed without exceptions.
