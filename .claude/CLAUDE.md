# Proyecto: ClinicCloud - Gestión de Documentos de Migración

## Descripción

Herramienta web en Python para gestionar documentos de migración de ClinicCloud.
Permite listar, renombrar y empaquetar documentos a través de una interfaz web en el navegador.

## Stack tecnológico

- **Backend:** Python 3.11+ con Flask
- **Frontend:** HTML + Jinja2 templates + htmx para interactividad sin frameworks JS pesados
- **CSS:** Tailwind CSS — utility-first, sin CSS personalizado salvo casos excepcionales
- **Sin base de datos:** el estado vive en el sistema de ficheros
- **Dependencias:** mínimas, listadas en `requirements.txt`

## Estructura del proyecto

```
cliniccoud-migrations-document-python/
├── .claude/
│   ├── CLAUDE.md              ← este archivo
│   └── agents/                ← agentes personalizados (si se añaden)
├── app/
│   ├── __init__.py            ← fábrica de la app Flask
│   ├── routes/                ← capa presentación: blueprints Flask
│   │   ├── listing.py
│   │   ├── rename.py
│   │   └── packaging.py
│   ├── services/              ← capa aplicación: orquesta dominio e infraestructura
│   │   ├── document_lister.py
│   │   ├── document_renamer.py
│   │   └── package_builder.py
│   ├── domain/                ← Value Objects y protocolos (sin dependencias externas)
│   │   ├── document.py        ← DocumentName (Value Object)
│   │   └── repositories.py    ← DocumentRepository (Protocol)
│   ├── infrastructure/        ← implementaciones concretas
│   │   ├── fs_document_repository.py   ← acceso al sistema de ficheros
│   │   └── zip_package_writer.py       ← creación de ZIPs
│   └── templates/             ← HTML Jinja2
│       ├── base.html
│       ├── listing.html
│       ├── rename.html
│       └── packaging.html
├── tests/                     ← specs TDD (espeja estructura de app/)
│   ├── domain/
│   │   └── test_document_name.py
│   ├── services/
│   │   ├── test_document_lister.py
│   │   ├── test_document_renamer.py
│   │   └── test_package_builder.py
│   ├── infrastructure/
│   │   ├── test_fs_document_repository.py
│   │   └── test_zip_package_writer.py
│   └── conftest.py
├── static/                    ← CSS, JS, iconos
├── config.py                  ← rutas INPUT_DIR / OUTPUT_DIR
├── run.py                     ← punto de entrada: `python run.py`
└── requirements.txt
```

## Arquitectura: DDD-lite

Adoptamos los patrones útiles de Domain-Driven Design sin la maquinaria pesada, en coherencia con KISS.

### Lo que aplicamos

**Ubiquitous Language** — términos del dominio consistentes en todo el código:

| Término | Significado |
|---------|-------------|
| `Document` | Un fichero de migración individual |
| `DocumentName` | El nombre con extensión de un documento (Value Object) |
| `Package` | Un conjunto de documentos agrupados en un ZIP |
| `DocumentRepository` | Abstracción para acceder a documentos en el sistema de ficheros |

**Value Objects** — objetos inmutables que encapsulan validación:
```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DocumentName:
    value: str

    def __post_init__(self) -> None:
        if not self.value or "/" in self.value or "\\" in self.value:
            raise ValueError(f"Invalid document name: {self.value!r}")

    @property
    def stem(self) -> str:
        return Path(self.value).stem

    @property
    def suffix(self) -> str:
        return Path(self.value).suffix
```

**Repository pattern** — abstrae el acceso al sistema de ficheros:
```python
from typing import Protocol
from pathlib import Path

class DocumentRepository(Protocol):
    def find_all(self, directory: Path) -> list[Path]: ...
    def rename(self, source: Path, new_name: DocumentName) -> Path: ...
```

### Lo que NO aplicamos (over-engineering para este dominio)

- Aggregates con invariantes complejas
- Domain Events
- Application Services separados de Domain Services
- Bounded Contexts / Anti-Corruption Layers

### Estructura de capas resultante

```
routes/        ← capa de presentación (Flask, HTTP)
    ↓
services/      ← capa de aplicación + dominio (lógica pura)
    ↓
domain/        ← Value Objects y protocolos del dominio
    ↓
infrastructure/← implementaciones concretas (FileSystem, ZIP)
```

---

## Filosofía de desarrollo

### KISS — Keep It Simple, Stupid
- La solución más simple que funcione correctamente es la correcta.
- Si se puede hacer en una función, no crear una clase. Si se puede hacer en un módulo, no crear un paquete.
- No anticipar requisitos futuros: implementar solo lo que se pide ahora.
- Tres líneas similares son mejores que una abstracción prematura.
- Preferir legibilidad sobre cleverness.

### SOLID aplicado a este proyecto

| Principio | Aplicación práctica |
|-----------|---------------------|
| **S** — Single Responsibility | Cada clase/función hace una sola cosa. `DocumentLister` lista; no renombra ni empaqueta. |
| **O** — Open/Closed | Extender comportamiento via nuevas clases/funciones, no modificando las existentes. Usar protocolos/interfaces cuando haya variantes. |
| **L** — Liskov Substitution | Si se usan clases base o protocolos, las implementaciones deben ser intercambiables sin romper el código cliente. |
| **I** — Interface Segregation | Interfaces pequeñas y específicas. No obligar a implementar métodos que no se usan. |
| **D** — Dependency Inversion | Los servicios dependen de abstracciones (protocolos Python), no de implementaciones concretas. Facilita testing y extensión. |

Ejemplo de D correcto:
```python
# Abstracción
from typing import Protocol
class DocumentRepository(Protocol):
    def list_documents(self, directory: Path) -> list[Path]: ...

# Implementación concreta
class FileSystemDocumentRepository:
    def list_documents(self, directory: Path) -> list[Path]:
        return sorted(directory.iterdir())

# Servicio depende de la abstracción, no de la implementación
class DocumentLister:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository
```

## Convenciones de código

### Idioma
- **Todo el código en inglés**: variables, funciones, clases, comentarios, docstrings, nombres de fichero.
- Los textos visibles al usuario en la UI pueden estar en el idioma del cliente (español).

### Nomenclatura — estándares Python (PEP 8 + convenciones de dominio)

| Elemento | Estilo | Ejemplo |
|----------|--------|---------|
| Variables y funciones | `snake_case` | `document_path`, `list_documents()` |
| Clases | `PascalCase` | `DocumentLister`, `PackageBuilder` |
| Constantes de módulo | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE`, `DEFAULT_OUTPUT_DIR` |
| Módulos y ficheros | `snake_case` | `document_lister.py`, `file_renamer.py` |
| Protocolos/interfaces | `PascalCase` + sufijo `Protocol` omitido si el nombre ya es abstracto | `DocumentRepository`, `FilePackager` |
| Parámetros booleanos | prefijo `is_`, `has_`, `should_` | `is_recursive`, `has_extension` |
| Métodos que devuelven bool | prefijo `is_`, `has_`, `can_` | `is_valid_extension()` |

### Reglas adicionales
- Funciones en `services/` no importan Flask; son puras y testeables.
- Las rutas en `routes/` solo validan entrada, llaman a services y devuelven respuesta.
- Sin comentarios obvios. Solo comentar el WHY cuando no sea evidente del código.
- Docstrings solo en clases públicas y funciones con lógica no trivial (una línea basta si es suficiente).
- Type hints en todas las firmas de funciones públicas.

## Tareas principales

| Tarea       | Ruta web         | Service         |
|-------------|------------------|-----------------|
| Listar docs | `GET /`          | `lister.py`     |
| Renombrar   | `POST /rename`   | `renamer.py`    |
| Empaquetar  | `POST /package`  | `packager.py`   |

## Configuración de rutas

Editar `config.py` para ajustar:
- `INPUT_DIR`: carpeta donde están los documentos fuente
- `OUTPUT_DIR`: carpeta donde se depositan los paquetes generados

## Comandos habituales

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests (siempre antes de arrancar)
pytest

# Tests con cobertura
pytest --cov=app --cov-report=term-missing

# Arrancar servidor de desarrollo
python run.py

# La UI abre en http://localhost:5000
```

## TDD — Test First

**Regla absoluta: ninguna implementación sin su test escrito antes.**

### Ciclo obligatorio (Red → Green → Refactor)

1. **Red** — escribir el test que describe el comportamiento esperado. Debe fallar.
2. **Green** — escribir el mínimo código que hace pasar el test.
3. **Refactor** — limpiar sin romper los tests.

Nunca saltarse el paso Red. Un test escrito después de la implementación no es TDD.

### Framework y estructura

- **pytest** como framework de testing.
- Los tests viven en `tests/` espejando la estructura de `app/`:

```
tests/
├── domain/
│   └── test_document_name.py       ← specs de Value Objects
├── services/
│   ├── test_document_lister.py
│   ├── test_document_renamer.py
│   └── test_package_builder.py
├── infrastructure/
│   ├── test_fs_document_repository.py
│   └── test_zip_package_writer.py
└── conftest.py                     ← fixtures compartidos
```

### Nomenclatura de tests

- Ficheros: `test_<módulo>.py`
- Funciones: `test_<método>_<escenario>_<resultado_esperado>()`

```python
# Bien — describe exactamente qué, cuándo y qué resultado
def test_document_name_with_slash_raises_value_error(): ...
def test_document_lister_returns_sorted_list_when_directory_has_files(): ...
def test_package_builder_creates_zip_with_correct_internal_paths(): ...

# Mal — no dice qué se espera
def test_document_name(): ...
def test_lister(): ...
```

### Qué testear por capa

| Capa | Tipo de test | Estrategia |
|------|-------------|------------|
| `domain/` | Unitario puro | Sin mocks, sin I/O. Los Value Objects son funciones puras. |
| `services/` | Unitario con mocks | Mockear el Repository (Protocol). Testear orquestación. |
| `infrastructure/` | Integración | Usar `tmp_path` de pytest para ficheros reales temporales. |
| `routes/` | Integración HTTP | Flask test client. Mockear services. |

### Fixtures y datos de prueba

- Usar `tmp_path` (fixture nativa de pytest) para tests que tocan el sistema de ficheros. Nunca rutas absolutas en tests.
- Datos de prueba mínimos: el test debe ser legible sin contexto externo.
- Un `conftest.py` por nivel si los fixtures se reutilizan entre módulos del mismo nivel.

### Cobertura

- Objetivo: **100 % en `domain/`** (lógica pura, sin excusa).
- Objetivo: **≥ 90 % en `services/`**.
- `infrastructure/` y `routes/`: cubrir el happy path y los errores esperados.

### Comandos

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=term-missing

# Solo una capa
pytest tests/domain/
```

---

## Compatibilidad multiplataforma (Mac · Linux · Windows)

El proyecto debe producir los mismos resultados en los tres sistemas operativos.
Aplicar siempre estas reglas, sin excepciones:

### Rutas de ficheros
- Usar **`pathlib.Path`** para toda manipulación de rutas. Nunca concatenar strings con `/` o `\`.
- `Path(a) / b` en lugar de `os.path.join(a, b)`.
- Para abrir un fichero: `path.open()` o `open(path)`, nunca `open("carpeta/fichero.txt")` con slash hardcodeado.

### Sistema de ficheros
- Nombres de fichero en **minúsculas** siempre que se generen desde código (evita el comportamiento case-insensitive de Windows/Mac vs case-sensitive de Linux).
- No asumir que el separador es `/`; usar `Path.parts`, `Path.stem`, `Path.suffix`.

### Subprocesos y shell
- Nunca usar `os.system()`. Usar `subprocess.run([...])` con lista de argumentos (no shell string), y `check=True`.
- No depender de comandos de shell específicos del OS (`ls`, `dir`, `cp`, `move`). Toda operación de ficheros con `pathlib` / `shutil`.

### Empaquetado (zip)
- Usar `zipfile` de la stdlib. No llamar a `zip` o `tar` como subproceso.
- Separador interno del zip siempre `/` (estándar ZIP), independiente del OS.

### Configuración de rutas de entrada/salida
- En `config.py`, resolver rutas con `Path(os.environ.get("INPUT_DIR", "input")).resolve()`.
- Nunca rutas absolutas hardcodeadas.

### Servidor Flask
- Arrancar con `flask run` o `python run.py`; ambos funcionan igual en los tres OS.
- No usar `0.0.0.0` en producción; en desarrollo sí es aceptable.

### Dependencias
- Listar en `requirements.txt` con versiones fijas (`==`).
- No incluir dependencias exclusivas de un OS.
- Probar instalación en entorno limpio con `pip install -r requirements.txt`.

### Ejemplo de patrón correcto

```python
# Bien
from pathlib import Path
docs_dir = Path("input") / "documentos"
for doc in docs_dir.iterdir():
    print(doc.name)

# Mal
import os
docs_dir = "input/documentos"
for doc in os.listdir(docs_dir):
    print(doc)
```

## Frontend: Tailwind CSS

### Estrategia por entorno

**Desarrollo** — CDN script en `base.html`, cero configuración:
```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Producción** — Tailwind CLI standalone (binario único, sin Node.js):
```bash
# Descargar el CLI (una sola vez)
# Mac/Linux:
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64 && mv tailwindcss-macos-arm64 tailwindcss

# Compilar CSS optimizado (solo clases usadas en templates)
./tailwindcss -i static/css/input.css -o static/css/main.css --minify
```

`static/css/input.css` contiene únicamente:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Convenciones de UI

- Clases Tailwind directamente en el HTML. No crear clases CSS propias salvo que se reutilicen más de tres veces.
- Para componentes repetidos (botones, badges, cards) usar `@apply` en `input.css`, no duplicar clases en el HTML.
- Diseño mobile-first: usar breakpoints `sm:`, `md:`, `lg:` según necesidad.
- Paleta de colores definida en `tailwind.config.js` (si se usa CLI) para mantener coherencia.

### Estructura de ficheros estáticos

```
static/
├── css/
│   ├── input.css    ← fuente Tailwind (solo para CLI)
│   └── main.css     ← CSS compilado (producción)
└── js/
    └── htmx.min.js  ← htmx local (opcional, o via CDN)
```

### Detección del entorno en Flask

```python
# config.py
import os
USE_CDN = os.environ.get("FLASK_ENV", "development") == "development"
```

```html
<!-- base.html -->
{% if config.USE_CDN %}
  <script src="https://cdn.tailwindcss.com"></script>
{% else %}
  <link rel="stylesheet" href="/static/css/main.css">
{% endif %}
```

---

## Lo que NO hacer

- No añadir frameworks JS pesados (React, Vue, Alpine) salvo petición explícita.
- No usar base de datos si el sistema de ficheros es suficiente.
- No introducir abstracciones antes de necesitarlas.
- No duplicar lógica entre routes y services.
- No usar rutas con slashes hardcodeados ni `os.system()`.
