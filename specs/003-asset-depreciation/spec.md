# Feature Specification: Asset Depreciation Tracking

**Feature Branch**: `003-asset-depreciation`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "When we buy larger items (bike, iPhone) we write them off over multiple years. In the Excel file on tab Resultaat, lines 28 and 29 show the write-offs for this year."

## Clarifications

### Session 2026-01-02

- Q: First-year depreciation method: pro-rated or full year? → A: Full year from purchase year (no pro-rating) - matches current Excel practice
- Q: Is Excel import ongoing or one-time? → A: One-time migration; assets stored in persistent file for future purchases
- Q: Disposal year depreciation: pro-rated or full year? → A: Full year for disposal year, then stop (consistent with no-proration approach)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register Depreciable Asset (Priority: P1)

As a self-employed midwife, I want to register a larger purchase (e.g., bike, phone) as a depreciable asset so that the system knows to spread the expense over multiple years rather than deducting it all at once.

**Why this priority**: Without registering assets, no depreciation calculations can happen. This is the foundation for the entire feature.

**Independent Test**: Register a new asset (Orbea bike, €4179.05, 3 years) and verify it appears in the asset list with correct values.

**Acceptance Scenarios**:

1. **Given** I have purchased a new business asset, **When** I register it with name, purchase date, amount, and depreciation period, **Then** the system stores the asset and calculates the annual depreciation amount.

2. **Given** I am registering an asset, **When** I specify a 3-year depreciation period for €900, **Then** the annual depreciation is calculated as €300 per year.

3. **Given** I have an existing asset registered, **When** I try to register a duplicate (same name and purchase date), **Then** the system warns me about the potential duplicate.

---

### User Story 2 - View Annual Depreciation Schedule (Priority: P1)

As a self-employed midwife, I want to see the depreciation amounts for each year so I can include the correct write-off amounts in my annual tax filing.

**Why this priority**: Seeing the calculated depreciation is essential for tax filing. Without this, the user cannot determine what to report.

**Independent Test**: View the depreciation schedule for 2025 and see both the phone (€256.33) and bike (€1393.02) write-offs listed.

**Acceptance Scenarios**:

1. **Given** I have registered assets with multi-year depreciation, **When** I view the depreciation schedule for a specific year, **Then** I see all assets with active depreciation and their write-off amounts for that year.

2. **Given** an asset was purchased in 2023 with 3-year depreciation, **When** I view the 2026 schedule, **Then** the asset no longer appears (fully depreciated).

3. **Given** an asset was purchased mid-2024, **When** I view the 2024 schedule, **Then** I see the full annual depreciation amount (no pro-rating).

---

### User Story 3 - Include Depreciation in P&L Report (Priority: P2)

As a self-employed midwife, I want the annual depreciation amounts to be included in my P&L totals so that my tax-deductible expenses are correctly calculated.

**Why this priority**: Integration with the existing P&L/categorization system makes depreciation seamlessly part of the financial picture, but the core tracking must work first.

**Independent Test**: Generate a P&L summary for 2025 and verify the "afschrijvingen" (depreciation) category shows €1649.35 total (€256.33 + €1393.02).

**Acceptance Scenarios**:

1. **Given** I have depreciation amounts for 2025, **When** I view the P&L summary for 2025, **Then** depreciation appears as a separate expense category totaling all write-offs for that year.

2. **Given** depreciation is included in P&L, **When** I export the P&L report, **Then** depreciation expenses are correctly categorized as tax-deductible.

---

### User Story 4 - Import Existing Assets from Excel (Priority: P2)

As a self-employed midwife, I want to import my existing depreciable assets from the Excel file so I don't have to re-enter historical data manually.

**Why this priority**: Convenience for migration, but manual entry is an acceptable fallback.

**Independent Test**: Import assets from the Resultaat sheet and verify both the phone and bike appear with their correct remaining depreciation periods.

**Acceptance Scenarios**:

1. **Given** I have assets listed in my Excel Resultaat sheet, **When** I run the import command, **Then** all depreciable assets are extracted and registered in the system.

2. **Given** assets are imported, **When** I view the asset list, **Then** I see the original purchase amount, depreciation rate, and remaining years correctly populated.

---

### User Story 5 - Edit or Dispose of Asset (Priority: P3)

As a self-employed midwife, I want to mark an asset as sold or disposed of so that depreciation stops from that point forward.

**Why this priority**: Less common scenario, but needed for accuracy when assets are sold or replaced before full depreciation.

**Independent Test**: Mark the phone as disposed in 2025 and verify no depreciation appears for 2026.

**Acceptance Scenarios**:

1. **Given** I have a registered asset, **When** I mark it as disposed with a date, **Then** depreciation stops from that date forward.

2. **Given** an asset is disposed mid-year, **When** I view the depreciation schedule, **Then** I see full-year depreciation for the disposal year, then no further depreciation.

---

### Edge Cases

- What happens when an asset's purchase date is before the system's tracking period? (Show full history from purchase year)
- How does the system handle assets purchased mid-year? (Full-year depreciation applies from purchase year - no pro-rating)
- How does the system handle assets disposed mid-year? (Full-year depreciation for disposal year, then stop)
- What happens if depreciation period is entered as 0 or negative? (Reject with validation error)
- How are already-fully-depreciated assets handled during import? (Show as fully depreciated, €0 remaining)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow registration of depreciable assets with: name, purchase date, purchase amount, depreciation period (years), and optional notes.
- **FR-002**: System MUST calculate annual depreciation using straight-line method (purchase amount / depreciation years).
- **FR-003**: System MUST track remaining book value for each asset (purchase amount minus accumulated depreciation).
- **FR-004**: System MUST apply full-year depreciation starting from the purchase year (no pro-rating for partial years).
- **FR-005**: System MUST display a depreciation schedule showing all active assets and their write-off amounts for any given year.
- **FR-006**: System MUST persist asset data in a dedicated assets file (e.g., `data/assets.json`) separate from transactions, allowing ongoing additions of new assets.
- **FR-007**: System MUST allow marking assets as disposed with a disposal date.
- **FR-008**: System MUST stop calculating depreciation after an asset is fully depreciated or disposed.
- **FR-009**: System MUST integrate depreciation totals into the P&L expense categories.
- **FR-010**: System MUST support importing assets from the existing Excel format (Resultaat sheet structure).
- **FR-011**: System MUST validate that depreciation period is a positive integer (typically 1-10 years for Belgian SME assets).
- **FR-012**: System MUST allow listing all assets with their current depreciation status.

### Key Entities

- **Asset**: A depreciable business purchase with name, purchase_date, purchase_amount, depreciation_years, disposal_date (optional), notes (optional).
- **DepreciationEntry**: Annual depreciation record linking an asset to a fiscal year with the calculated write-off amount.
- **AssetStatus**: Derived state indicating if asset is active, fully_depreciated, or disposed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can register a new asset and see calculated annual depreciation within 30 seconds.
- **SC-002**: Depreciation schedule for any year displays accurate amounts matching Excel calculations (within €0.01 rounding tolerance).
- **SC-003**: P&L report includes depreciation as a separate category with correct totals.
- **SC-004**: Existing assets can be imported from Excel with no manual data entry required.
- **SC-005**: 100% of registered assets have accurate remaining book value tracking.

## Assumptions

- **A-001**: Straight-line depreciation is used (Belgian standard for most small business assets).
- **A-002**: Assets are always depreciated in full years starting from purchase year (no pro-rating).
- **A-003**: All amounts are in EUR.
- **A-004**: Depreciation category already exists in config/categories.yaml as "afschrijvingen" (it does - verified in the 26 predefined categories).
- **A-005**: The Excel Resultaat sheet structure (columns: name, amount, rate, annual amount, notes) is stable for import.
