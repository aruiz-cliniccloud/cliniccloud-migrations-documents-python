# ClinicCloud — Migration Document Manager

Web tool for listing, renaming, and packaging migration documents.
Built with Python + Flask + Tailwind CSS.

---

## Requirements

- Python 3.11+
- pip

No Node.js required.

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd cliniccoud-migrations-document-python
```

### 2. Create and activate a virtual environment

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

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set the paths for your document directories (see [Configuration](#configuration)).

### 5. Run the development server

```bash
python run.py
```

Open your browser at **http://localhost:5000**

---

## Configuration

All settings are defined in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | `development` or `production` | `development` |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | *(required)* |
| `INPUT_DIR` | Directory where source documents are read from | `input` |
| `OUTPUT_DIR` | Directory where generated packages are saved | `output` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `5000` |

---

## Running tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing
```

---

## Project structure

```
app/
├── domain/          # Value Objects and Repository protocols
├── infrastructure/  # File system and ZIP implementations
├── routes/          # Flask blueprints (HTTP layer)
├── services/        # Application logic (orchestration)
└── templates/       # Jinja2 HTML templates
tests/               # TDD specs mirroring app/ structure
static/              # CSS, JS, icons
```

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
