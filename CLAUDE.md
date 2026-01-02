# Claude Code Project Guide

## Running Python Code

This project uses macOS with an externally-managed Python environment. To run Python code:

### Option 1: Virtual Environment (Recommended)
```bash
# Create a virtual environment
python3 -m venv /tmp/venv

# Activate and install dependencies
source /tmp/venv/bin/activate
pip install pandas pdfplumber

# Run Python code
python3 your_script.py
```

### Option 2: One-liner for scripts
```bash
cd /tmp && source venv/bin/activate && python3 << 'PYEOF'
# Your Python code here
PYEOF
```

## Project Structure

- `data/2025/` - Source financial data (CSV bank statements, PDF Mastercard statements)
- `specs/` - Feature specifications and implementation plans
- `.specify/` - Speckit templates and scripts

## MCP Integrations

- **Google Drive MCP**: Available for file operations (sheets, docs, etc.)
- **Google Calendar MCP**: Available for calendar operations

## Data Processing Notes

- CSV files use semicolon delimiter (`;`) and European number format (comma as decimal)
- PDF Mastercard statements require `pdfplumber` for extraction
- All amounts are in EUR
