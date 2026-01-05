# Quickstart: PLV Web Interface

**Feature**: 009-streamlit-web-app
**Updated**: 2026-01-05

## Prerequisites

- Python 3.11+
- Git
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Local Development Setup

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/[org]/PLVroedvrouwGoedele.git
cd PLVroedvrouwGoedele

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application

```bash
# Start Streamlit server
streamlit run streamlit_app.py

# Opens browser automatically at http://localhost:8501
```

### 3. Basic Workflow

1. **Open the app** in browser at http://localhost:8501
2. **Select fiscal year**: Defaults to 2025 in Jan-Mar 2026
3. **Upload files**: Drag CSV bank statements and/or PDF Mastercard statements
4. **Click "Importeren"**: View imported transactions in the table
5. **Filter transactions**: Use search, date range, amount range, or category filters
6. **Click "Automatisch categoriseren"**: Apply rules to categorize transactions
7. **Edit categories**: Select a transaction to view details and change its category
8. **View P&L summary**: See income, expenses, and net profit
9. **Download reports**: Excel, PDF Jaarverslag, or CSV export

## Project Structure

```
PLVroedvrouwGoedele/
├── streamlit_app.py      # Main Streamlit application
├── requirements.txt      # Dependencies for deployment
├── .streamlit/
│   └── config.toml       # Streamlit theme configuration
├── src/
│   ├── models/           # Data models (Transaction, Rule, etc.)
│   ├── services/         # Business logic (importers, categorizer)
│   └── lib/              # Utilities (belgian_numbers)
├── data/
│   └── {company}/        # Company-specific data
│       ├── config/       # categories.yaml, rules.yaml
│       └── input/        # Input files (CSV, PDF)
└── specs/
    └── 009-streamlit-web-app/
        ├── spec.md
        ├── plan.md
        └── quickstart.md (this file)
```

## Stateless Architecture

The web app is fully stateless:

- **No preloaded companies**: Upload your own files each session
- **Embedded defaults**: 30 Belgian expense categories and 48 categorization rules are built-in
- **Optional config upload**: Upload custom `rules.yaml` or `categories.yaml` in sidebar
- **Session-only data**: Cleared when browser tab is closed

### Default Categories

The app includes standard Belgian expense categories:
- **Income**: omzet
- **Fully deductible**: sociale-bijdragen, bankkosten, telefonie, medisch-materiaal, etc.
- **Partially deductible**: restaurant (69%), onthaal (50%), relatiegeschenken (50%)
- **Excluded**: prive-opname, verkeerde-rekening, mastercard, etc.

### Default Rules

The app includes 48 patterns for Belgian midwives:
- RIZIV/INAMI payments → omzet (therapeutic)
- Mutualiteiten (CM, Solidaris, Partena, etc.) → omzet
- Acerta, Liantis, Xerius → sociale-bijdragen
- Proximus, Telenet, Orange → telefonie
- And more...

## Custom Configuration

### Upload Custom Rules

To use your own categorization rules:

1. Create a `rules.yaml` file (see `data/goedele/config/rules.yaml` for format)
2. In the sidebar, click "Upload rules.yaml (optioneel)"
3. Upload your file - rules are immediately applied

### Upload Custom Categories

To use your own categories:

1. Create a `categories.yaml` file (see `data/goedele/config/categories.yaml` for format)
2. In the sidebar, click "Upload categories.yaml (optioneel)"
3. Upload your file - categories replace defaults

## Transaction Filtering

The transaction table supports powerful filtering:

| Filter | How to Use |
|--------|------------|
| **Text search** | Type in "Zoeken in tegenpartij/omschrijving" |
| **Date range** | Set "Van datum" and "Tot datum" |
| **Amount range** | Set "Min bedrag" and "Max bedrag" |
| **Category** | Select from "Categorie" dropdown |
| **Source** | Select from "Bron" dropdown (CSV/PDF) |
| **Uncategorized** | Check "Alleen niet-gecategoriseerd" |
| **Income only** | Check "Alleen inkomsten" |
| **Expenses only** | Check "Alleen uitgaven" |

## Editing Transaction Categories

1. In the transaction table, check the "Selecteer" checkbox for a transaction
2. The **Transactie Details** panel appears below
3. Left side shows full transaction info
4. Right side shows **Categorie Aanpassen** panel:
   - Select new category from dropdown
   - Click "Categorie opslaan"
   - Category description and deductibility info shown

## Development Workflow

### Hot Reload

Streamlit auto-reloads when source files change. Just save and the browser updates.

### Debugging

```python
# Add to streamlit_app.py for debugging
st.write("Debug:", some_variable)

# Or use sidebar expander for debug info
with st.sidebar.expander("Debug Info"):
    st.json(st.session_state)
```

## Deployment to Streamlit Cloud

### First-Time Setup

1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select repository, branch (`009-streamlit-web-app`), and main file (`streamlit_app.py`)
5. Click "Deploy"

### Updating Deployment

Push changes to GitHub; Streamlit Cloud auto-deploys:

```bash
git add .
git commit -m "Update: description of changes"
git push origin 009-streamlit-web-app
```

## Testing

### Unit Tests (Existing Services)

```bash
# Run existing test suite
pytest tests/unit/

# Run specific test
pytest tests/unit/test_categorizer.py
```

### Manual Testing Checklist

- [ ] Upload single CSV file
- [ ] Upload single PDF file
- [ ] Upload multiple files at once
- [ ] Change fiscal year
- [ ] Upload custom rules.yaml
- [ ] Upload custom categories.yaml
- [ ] Filter by text search
- [ ] Filter by date range
- [ ] Filter by amount range
- [ ] Filter by category
- [ ] Filter uncategorized only
- [ ] Select transaction to view details
- [ ] Edit transaction category
- [ ] Run auto-categorization
- [ ] Check "Hercategoriseer alle" and re-run
- [ ] View P&L summary
- [ ] Download Excel report
- [ ] Download PDF Jaarverslag
- [ ] Export transactions CSV
- [ ] Upload invalid file (should show error)
- [ ] Upload duplicate file (should skip duplicates)

## Troubleshooting

### "Module not found" error

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### No transactions imported

- Check fiscal year matches your data (e.g., 2025 data needs fiscal year 2025)
- In Jan-Mar, default is previous year; change if needed
- Check file format is Belfius CSV or Mastercard PDF

### Memory issues with large files

- Streamlit Community Cloud has 1GB RAM limit
- Upload files in smaller batches
- Close other browser tabs

### PDF parsing fails

- Ensure PDF is a Belfius Mastercard statement
- Check for password protection (not supported)
- Try individual pages if multi-page fails

### Session data lost

Normal behavior - Streamlit clears session when:
- Browser tab closed
- Session timeout (configurable)
- Server restart

Re-upload files to continue.

## Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [PLV CLI Documentation](../001-2025-transaction-import/spec.md)
- [Categorization Rules Format](../../data/goedele/config/rules.yaml)
- [Categories Format](../../data/goedele/config/categories.yaml)
