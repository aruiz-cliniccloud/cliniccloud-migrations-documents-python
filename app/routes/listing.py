from pathlib import Path
from flask import Blueprint, render_template, request, current_app
from app.services.document_lister import DocumentLister
from app.infrastructure.fs_document_repository import FileSystemDocumentRepository

listing_bp = Blueprint("listing", __name__)

_DEFAULT_LIMIT = 5


def _lister() -> DocumentLister:
    return DocumentLister(FileSystemDocumentRepository())


@listing_bp.get("/documents")
def index():
    default_dir = current_app.config.get("INPUT_DIR", "")
    path_str = request.args.get("path", default_dir).strip()
    show_all = request.args.get("all") == "1"

    if not path_str:
        return render_template("listing.html", path=path_str, documents=None,
                               error=None, default_dir=default_dir,
                               total=0, limited=False)

    directory = Path(path_str)
    try:
        all_documents = _lister().list_documents(directory)
    except ValueError as exc:
        return render_template("listing.html", path=path_str, documents=None,
                               error=str(exc), default_dir=default_dir,
                               total=0, limited=False)

    total = len(all_documents)
    limited = not show_all and total > _DEFAULT_LIMIT
    documents = all_documents if show_all else all_documents[:_DEFAULT_LIMIT]

    return render_template("listing.html", path=path_str, documents=documents,
                           error=None, default_dir=default_dir,
                           total=total, limited=limited)
