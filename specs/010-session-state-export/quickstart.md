# Quickstart: Session State Export/Import

**Feature**: 010-session-state-export
**Phase**: 1 (Design)
**Date**: 2026-01-05

## Overview

The PLV web app allows you to export your current work session to a file and import it later to continue. This is useful when you want to:
- Pause your bookkeeping work and continue another day
- Back up your session before making changes
- Transfer your work to a different computer

## Exporting Your Session

### When to Export

Export your session when:
- You've done significant categorization work
- You want to save your progress before closing the browser
- You need to continue on a different device

### How to Export

1. **Work on your transactions** - Import files, run categorization, edit categories
2. **Find the export section** in the sidebar (appears when transactions exist)
3. **Enter a company name** (optional) - Used in the filename
4. **Check "Bronbestanden toevoegen"** if you want to include original CSV/PDF files
5. **Click "Exporteer sessie"**
6. **Save the ZIP file** that downloads to your browser

### Export File Contents

The exported ZIP file contains:

| File | Always Included | Description |
|------|-----------------|-------------|
| `state.json` | Yes | Your transactions, categories, and settings |
| `rules.yaml` | Only if uploaded | Custom categorization rules |
| `categories.yaml` | Only if uploaded | Custom category definitions |
| `source_files/` | Only if checkbox checked | Original CSV and PDF files |

### Filename Format

The export filename follows this pattern:
```
plv-{company_name}-{fiscal_year}.zip
```

Examples:
- `plv-goedele-2025.zip` (company name: "goedele", year: 2025)
- `plv-mijn-praktijk-2025.zip` (company name: "Mijn Praktijk", year: 2025)
- `plv-sessie-2025.zip` (no company name entered)

## Importing a Session

### Before You Import

- **Existing data will be replaced** - Import overwrites your current session
- **Confirm before importing** - The app will ask you to confirm if you have existing data

### How to Import

1. **Open the PLV web app** in your browser
2. **Find "Importeer sessie"** in the sidebar
3. **Click to upload** and select your PLV session ZIP file
4. **Confirm replacement** if you have existing data
5. **Wait for import** - A success message shows transaction count

### What Gets Restored

After import, your session includes:
- All transactions with their categories
- Fiscal year setting
- Categorization status
- Custom rules (if included in export)
- Custom categories (if included in export)

### Handling Older Files

If you import a session file from an older app version:
- The app automatically upgrades the file format
- You'll see a message: "Sessiebestand wordt geüpgraded van v1.0 naar v1.1"
- No action needed - the import continues normally

## Troubleshooting

### "Ongeldig sessiebestand: state.json niet gevonden"

**Cause**: The ZIP file doesn't contain a `state.json` file.

**Solution**: Make sure you're uploading a PLV session export, not just any ZIP file.

### "Ongeldig sessiebestand: corrupte data"

**Cause**: The `state.json` file is corrupted or not valid JSON.

**Solution**: Try re-exporting from your previous session. If the file was edited manually, check for JSON syntax errors.

### "Upload een .zip bestand"

**Cause**: You uploaded a file that isn't a ZIP archive.

**Solution**: Make sure you're uploading the `.zip` file from your PLV export, not just the CSV or PDF source files.

### Session data seems incomplete

**Cause**: The export may be from an older version without all fields.

**Solution**: The app migrates older files automatically. If data is still missing, try exporting fresh from the original session.

### Can't find the export button

**Cause**: Export only appears when you have transactions.

**Solution**: Import some bank statements first. The export section appears in the sidebar after you have at least one transaction.

## Best Practices

### Regular Backups

Export your session:
- After importing new bank statements
- After significant categorization work
- Before running "Hercategoriseer alle"
- At the end of each work session

### Naming Convention

Use descriptive company names:
- `goedele` - Short and clear
- `vroedvrouw-goedele` - More specific
- `praktijk-leuven` - Location-based

### Storage

Keep your session exports:
- In a dedicated folder (e.g., `Boekhouding/PLV-Sessies/`)
- With backup copies (e.g., Google Drive, iCloud)
- Don't delete until tax filing is complete

### Version Control

Keep multiple exports if unsure:
- `plv-goedele-2025-draft.zip` - Work in progress
- `plv-goedele-2025-final.zip` - Completed categorization

## Technical Details

### File Size

Typical session exports:
- 50 transactions: ~10KB compressed
- 200 transactions: ~30KB compressed
- 500 transactions: ~75KB compressed
- With source files: Add ~50-500KB per file

### Compatibility

Session files work:
- Across browser sessions (Chrome, Firefox, Safari, Edge)
- Across computers (Mac, Windows, Linux)
- With future app versions (automatic migration)

### Privacy

Session exports contain:
- Transaction data (amounts, counterparties, descriptions)
- Category assignments
- Company name (user-entered)

**Note**: No personal login data or API keys are stored. Files can be safely shared with your accountant if needed.
