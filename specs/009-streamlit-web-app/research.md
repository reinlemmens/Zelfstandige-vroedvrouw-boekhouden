# Research: PLV Web Interface

**Feature**: 009-streamlit-web-app
**Date**: 2026-01-04

## Research Tasks Completed

### 1. Streamlit File Upload Handling

**Decision**: Use `st.file_uploader` with `accept_multiple_files=True`

**Rationale**:
- Native Streamlit component with drag-and-drop support
- Returns `UploadedFile` objects with `.read()` method for byte content
- Handles MIME type filtering via `type` parameter
- Maximum file size controlled by Streamlit Cloud (default 200MB)

**Alternatives Considered**:
- Custom HTML/JS uploader: Rejected - adds complexity, loses Streamlit integration
- Single file upload with loop: Rejected - poor UX, multiple clicks required

**Implementation Pattern**:
```python
uploaded_files = st.file_uploader(
    "Upload bank statements",
    type=['csv', 'pdf'],
    accept_multiple_files=True
)
for file in uploaded_files:
    if file.name.endswith('.csv'):
        # Process CSV
    elif file.name.endswith('.pdf'):
        # Process PDF
```

### 2. Session State Management

**Decision**: Use `st.session_state` for transaction storage within session

**Rationale**:
- Built-in Streamlit feature, no external dependencies
- Persists across reruns within same session
- Automatically cleared when session ends (matches spec requirement)
- Supports arbitrary Python objects (Transaction list, Report objects)

**Alternatives Considered**:
- Browser localStorage: Rejected - requires custom JS, limited size
- Redis/database: Rejected - adds cost and complexity, not needed for session scope
- File-based temp storage: Rejected - doesn't survive Streamlit reruns

**Implementation Pattern**:
```python
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# After import:
st.session_state.transactions.extend(new_transactions)
```

### 3. Memory-Efficient File Processing

**Decision**: Process files sequentially with immediate cleanup; limit displayed rows

**Rationale**:
- 1GB RAM limit requires careful memory management
- Streamlit Community Cloud enforces memory limits
- Typical monthly statements (50-100 transactions) well within limits
- Display pagination prevents UI slowdown for large datasets

**Implementation Pattern**:
```python
# Process each file, don't hold all in memory
for uploaded_file in files:
    bytes_data = uploaded_file.read()
    # Process immediately
    transactions = process_file(bytes_data)
    st.session_state.transactions.extend(transactions)
    # bytes_data goes out of scope, eligible for GC
```

**Memory Budget**:
| Component | Estimated Memory |
|-----------|-----------------|
| Streamlit overhead | ~100MB |
| 500 transactions | ~5MB |
| PDF parsing (1 file) | ~50MB peak |
| Report generation | ~30MB peak |
| **Total Peak** | **~200MB** |

### 4. Streamlit Cloud Deployment Requirements

**Decision**: Deploy to Streamlit Community Cloud with GitHub integration

**Rationale**:
- Free tier matches budget requirement
- One-click deployment from GitHub repo
- Automatic HTTPS and URL provisioning
- No server management required

**Requirements**:
1. `requirements.txt` at repo root with all dependencies
2. `streamlit_app.py` as entry point (or configure via `.streamlit/config.toml`)
3. Public GitHub repository (or private with Pro plan)
4. `.streamlit/config.toml` for theme customization

**Deployment Files**:
```
# requirements.txt
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
pdfplumber>=0.10.0
PyYAML>=6.0
reportlab>=4.0.0
plotly>=5.18.0
```

```toml
# .streamlit/config.toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
maxUploadSize = 50
```

### 5. Integration with Existing Services

**Decision**: Import existing services directly; wrap for in-memory file handling

**Rationale**:
- Existing importers work with file paths, need adaptation for in-memory bytes
- Categorizer and report generators work with Transaction objects (unchanged)
- Configuration files loaded from `data/{company}/config/` paths

**Changes Required**:

1. **CSV Importer**: Accept `io.BytesIO` or `io.StringIO` instead of file path
   ```python
   # Wrapper for Streamlit uploaded files
   def import_from_bytes(self, file_content: bytes, filename: str) -> List[Transaction]:
       content = io.StringIO(file_content.decode('utf-8'))
       # Use existing parsing logic
   ```

2. **PDF Importer**: Accept bytes via `pdfplumber.open(io.BytesIO(bytes))`
   ```python
   def import_from_bytes(self, file_content: bytes, filename: str) -> List[Transaction]:
       with pdfplumber.open(io.BytesIO(file_content)) as pdf:
           # Existing parsing logic
   ```

3. **Config Loading**: Read from `data/{company}/config/` based on selected company
   - Categories: `data/{company}/config/categories.yaml`
   - Rules: `data/{company}/config/rules.yaml`

4. **Report Generation**: No changes needed - works with Transaction and Report objects

### 6. Error Handling Strategy

**Decision**: Graceful degradation with clear user feedback

**Implementation**:
```python
try:
    transactions = importer.import_from_bytes(content, filename)
    st.success(f"Imported {len(transactions)} transactions from {filename}")
except Exception as e:
    st.error(f"Failed to import {filename}: {str(e)}")
    # Continue with other files
```

**Error Categories**:
| Error Type | User Message | Action |
|------------|--------------|--------|
| Invalid file format | "Please upload CSV or PDF files only" | Skip file, continue |
| Empty file | "No transactions found in {filename}" | Skip file, continue |
| Parse error | "Could not read {filename}: {details}" | Skip file, log details |
| Memory limit | "File too large. Please upload smaller batches." | Stop processing |

## Unresolved Items

None - all technical decisions made. Ready for Phase 1 design.

## References

- [Streamlit File Uploader](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [pdfplumber with BytesIO](https://github.com/jsvine/pdfplumber/issues/192)
