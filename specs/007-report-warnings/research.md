# Research: Report Data Quality Warnings

**Feature**: 007-report-warnings
**Date**: 2026-01-04

## Executive Summary

All technical unknowns have been resolved through codebase analysis. The feature extends existing infrastructure without requiring new dependencies or architectural changes.

## Research Findings

### 1. PDF Warning Banner Placement

**Decision**: Add warning banner after the summary table on page 1

**Rationale**:
- The existing `_create_summary_section()` method returns elements that are rendered on page 1
- Inserting warning elements after the summary table ensures immediate visibility
- The existing `generate()` method builds sections in order, making insertion straightforward

**Alternatives Considered**:
- Header/footer approach: Rejected because reportlab headers are more complex and less visible
- Floating overlay: Rejected due to complexity and potential layout conflicts

### 2. PDF Aandachtspunten Section Location

**Decision**: Add dedicated section before conclusion (after expense analysis)

**Rationale**:
- The `generate()` method builds sections in sequence: summary → methodology → income → expenses → conclusion
- Adding before conclusion keeps the report flow logical (problems before final assessment)
- Uses same section styling patterns as existing sections (`SectionHeading`, `SubHeading`)

**Alternatives Considered**:
- After conclusion: Rejected because warnings should precede final assessment
- As part of conclusion: Rejected to keep sections modular and testable

### 3. Excel Sheet Organization

**Decision**: Add new "Aandachtspunten" sheet to workbook

**Rationale**:
- Existing P&L sheet already has an inline warning (line 279-282 in report_generator.py)
- Separate sheet allows detailed transaction listings without cluttering P&L
- openpyxl Workbook supports multiple sheets easily

**Alternatives Considered**:
- Inline expansion on P&L sheet: Rejected due to space constraints and readability
- Replace existing warning: Rejected to maintain backwards compatibility

### 4. Verkeerde-rekening Balance Calculation

**Decision**: Calculate net sum of all verkeerde-rekening transactions for the fiscal year

**Rationale**:
- Transactions in this category are already loaded but excluded from P&L
- Net balance = sum of all amounts (negatives are expenses, positives are reimbursements)
- A non-zero balance indicates missing reimbursements or miscategorization

**Alternatives Considered**:
- Match individual transactions: Rejected as too complex and error-prone
- Track separately in config: Rejected to maintain single source of truth

### 5. Warning Styling

**Decision**: Use orange/amber background (#FEF3C7) for warning elements

**Rationale**:
- Consistent with existing HIGHLIGHT_TOP3 color in pdf_report_generator.py
- Orange/amber universally signals "attention needed" without implying error
- Maintains professional appearance while being visually distinct

**Alternatives Considered**:
- Red styling: Rejected as too aggressive for informational warnings
- Blue styling: Rejected as it doesn't convey urgency

### 6. Uncategorized Transaction Identification

**Decision**: Filter transactions where `category is None` or `category == ''`

**Rationale**:
- Existing code already uses `df['category'].isna()` pattern (report_generator.py line 112)
- Consistent with existing uncategorized detection logic
- No need to introduce new "uncategorized" category marker

**Alternatives Considered**:
- Explicit "uncategorized" category: Rejected to avoid pollution of category namespace
- is_uncategorized flag: Rejected as redundant with existing null check

## Dependencies

No new dependencies required. Feature uses:
- reportlab (existing) - PDF generation
- openpyxl (existing) - Excel generation
- pandas (existing) - Data processing

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PDF layout disruption | Low | Medium | Test with various data volumes |
| Excel backward compatibility | Low | Low | New sheet is additive, P&L unchanged |
| Performance with large transaction sets | Very Low | Low | Already handles 500+ transactions |

## Conclusion

All research items resolved. Proceed to Phase 1 (data-model.md, quickstart.md).
