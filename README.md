# ClinicCloud — Migration Document Manager

Web tool for listing and exporting migration documents to Excel.
Built with Python + Flask + Tailwind CSS.

---

## Requirements

- Python 3.11+
- pip
- `make` (optional but recommended — Windows: `choco install make`)

No Node.js required.

---

## Installation

### Quick start (recommended)

```bash
make install
make dev
```

### Manual

#### 1. Clone the repository

```bash
git clone <repository-url>
cd cliniccoud-migrations-document-python
```

#### 2. Create and activate a virtual environment

**Mac / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set the paths for your document directories (see [Configuration](#configuration)).

#### 5. Run the development server

```bash
python run.py
```

Open your browser at **http://localhost:5000**

---

## Make commands

| Command | Description |
|---------|-------------|
| `make install` | Create virtualenv and install dependencies |
| `make dev` | Start the development server |
| `make stop` | Stop the running server |
| `make restart` | Stop and restart the server |
| `make status` | Check if the server is responding (`GET /health`) |
| `make test` | Run the test suite |
| `make coverage` | Run tests and show coverage report |
| `make clean` | Remove cache, build, and coverage files |
| `make reset` | Full clean + reinstall from scratch |

---

## Configuration

All settings are defined in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | `development` or `production` | `development` |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | *(required)* |
| `INPUT_DIR` | Default directory to scan for documents | `input` |
| `OUTPUT_DIR` | Directory where exported files are saved | `output` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `5000` |

---

## Features

### Document listing (`GET /documents`)

Recursively scans a directory and lists all files. By default shows the first 5 results; click **"Show all"** to load the full list.

The source directory can be:
- Typed manually in the path field.
- Selected via the **native OS folder picker** (opens a system dialog).

### Excel export (`GET /documents/export`)

Exports the full document list to an `.xlsx` file. The file is:
- Returned as a download in the browser.
- Also saved to `OUTPUT_DIR` with a timestamp (`documents_YYYYMMDD_HHMMSS.xlsx`).

Columns: `ruta` (absolute path), `ruta_relativa` (relative path, anchored at `uploaded_files/` when present), `nombre_fichero`, `extension`.

### Operation log

All listing and export operations are logged to `output/operations.txt` with timestamps.

### Internationalisation

The UI supports Spanish (`es`) and English (`en`). Language is switched via the selector in the top bar and stored in the session.

### Health check (`GET /health`)

Returns `{"status": "ok"}`. Used by `make status` and monitoring tools.

---

## Running tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing

# Single layer
pytest tests/domain/
```

---

## Project structure

```
app/
├── domain/          # Value Objects and Repository protocols
├── infrastructure/  # File system access and operation logger
├── routes/          # Flask blueprints (HTTP layer)
├── services/        # Application logic (listing, Excel export, i18n)
├── templates/       # Jinja2 HTML templates
└── translations/    # i18n JSON files (es.json, en.json)
output/              # Generated Excel exports and operations log
tests/               # TDD specs mirroring app/ structure
static/              # CSS, JS, icons
```

### Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page |
| `/documents` | GET | List documents in a directory |
| `/documents/export` | GET | Export document list to Excel |
| `/browse-folder` | GET | Open native OS folder picker dialog |
| `/health` | GET | Health check |

---

## Production build (Tailwind CSS)

In development, Tailwind is loaded via CDN automatically.
For production, compile an optimized CSS bundle using the Tailwind CLI standalone (no Node.js needed):

**Mac (Apple Silicon)**
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64
./tailwindcss-macos-arm64 -i static/css/input.css -o static/css/main.css --minify
```

**Mac (Intel)**
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-x64
chmod +x tailwindcss-macos-x64
./tailwindcss-macos-x64 -i static/css/input.css -o static/css/main.css --minify
```

**Linux**
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64
./tailwindcss-linux-x64 -i static/css/input.css -o static/css/main.css --minify
```

**Windows**
```powershell
Invoke-WebRequest -Uri "https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe" -OutFile "tailwindcss.exe"
.\tailwindcss.exe -i static/css/input.css -o static/css/main.css --minify
```

Then set `FLASK_ENV=production` in your `.env`.
