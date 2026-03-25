"""ATC Document Name Validator Service.

This service loads an Excel reference list of valid ATC document naming prefixes
and validates filenames against the ATC naming convention.

The expected naming convention is:
    PREFIX_TYPE_PROCESS_001_FR Document name.pdf

Where:
    - PREFIX: e.g. COM, QMS
    - TYPE: document type code
    - PROCESS: process code
    - number: three-digit document identifier
    - language: FR or EN

The reference file is expected to be located in the Django MEDIA_ROOT directory.
"""

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Default file name(s) in the media directory. Override via ATC_REFERENCE_FILE setting.
DEFAULT_ATC_REFERENCE_FILES = [
    "COM_GUI_AQS_002_FR  List des documents ATC (1).xlsx",
    "COM_GUI_AQS_002_FR  List des documents ATC (1) (1).xlsx",
    "List des documents ATC (1) (1).xlsx",
]


class ATCValidationError(Exception):
    pass


@lru_cache(maxsize=1)
def _load_reference_data(reference_path: Optional[str] = None) -> Dict[str, List[str]]:
    """Load ATC reference lists from the Excel file."""
    try:
        import pandas as pd
    except ImportError as ex:
        raise ATCValidationError(
            "pandas is required for ATC name validation; please install it (e.g. `pip install pandas`)."
        ) from ex

    media_root = Path(getattr(settings, "MEDIA_ROOT", settings.BASE_DIR / "media"))

    # Allow overriding via settings, otherwise try a few known filenames.
    override_file = getattr(settings, "ATC_REFERENCE_FILE", None)
    candidates = []
    if override_file:
        candidates.append(override_file)
    candidates.extend(DEFAULT_ATC_REFERENCE_FILES)

    reference_path = None
    for candidate in candidates:
        candidate_path = media_root / candidate
        if candidate_path.exists():
            reference_path = candidate_path
            break

    if reference_path is None or not reference_path.exists():
        raise ATCValidationError(
            "ATC reference file not found. Please add one of the expected XLSX files to MEDIA_ROOT."
        )

    try:
        xls = pd.ExcelFile(reference_path)
    except Exception as ex:
        raise ATCValidationError(f"Failed to read ATC reference Excel file: {ex}")

    refs: List[str] = []
    for sheet in xls.sheet_names:
        try:
            df_ref = pd.read_excel(xls, sheet_name=sheet, header=None)
        except Exception:
            continue
        for col in df_ref.columns:
            vals = df_ref[col].dropna().astype(str).str.strip().str.upper()
            matched = vals[vals.str.match(r"^[A-Z0-9]+_[A-Z0-9]+_[A-Z0-9]+_[0-9]{3}_(FR|EN)$")]
            refs.extend(matched.tolist())

    refs = sorted(set(refs))
    prefixes = sorted({r.split("_")[0] for r in refs})
    types_doc = sorted({r.split("_")[1] for r in refs})
    processus = sorted({r.split("_")[2] for r in refs})
    langues = sorted({r.split("_")[4] for r in refs})

    return {
        "prefixes": prefixes,
        "types": types_doc,
        "processes": processus,
        "langs": langues,
        "refs": refs,
    }


@lru_cache(maxsize=1)
def _build_regex(reference_data: Optional[Dict[str, List[str]]] = None) -> re.Pattern:
    """Build a compiled regex pattern from the reference data."""
    data = reference_data or _load_reference_data()

    if not data.get("prefixes") or not data.get("types") or not data.get("processes") or not data.get("langs"):
        raise ATCValidationError("ATC reference data is incomplete; cannot build validation pattern.")

    prefix_re = "|".join(re.escape(p) for p in data["prefixes"])
    type_re = "|".join(re.escape(t) for t in data["types"])
    process_re = "|".join(re.escape(p) for p in data["processes"])
    lang_re = "|".join(re.escape(l) for l in data["langs"])

    # Accept any file extension (not just PDF) but require a name after the language code.
    pattern = rf"^({prefix_re})_({type_re})_({process_re})_[0-9]{{3}}_({lang_re})\s+.+\.[A-Za-z0-9]+$"
    return re.compile(pattern, re.IGNORECASE)


def validate_filename(filename: str) -> Dict[str, str]:
    """Validate a document filename against the ATC naming convention."""
    if not filename or not isinstance(filename, str):
        return {"status": "NON_COMPLIANT", "reason": "Missing filename.", "filename": filename}

    name = Path(filename).name.strip()
    if not name:
        return {"status": "NON_COMPLIANT", "reason": "Filename is empty.", "filename": filename}

    if '.' not in name:
        return {
            "status": "NON_COMPLIANT",
            "reason": "Filename must include a file extension (e.g. .pdf, .docx).",
            "filename": name,
        }

    try:
        regex = _build_regex()
    except ATCValidationError as ex:
        logger.warning("ATC reference load failed: %s", ex)
        return {
            "status": "NON_COMPLIANT",
            "reason": "ATC reference data not available.",
            "filename": name,
        }

    if regex.match(name):
        return {
            "status": "COMPLIANT",
            "reason": "Filename follows ATC naming convention.",
            "filename": name,
        }

    # Provide a more useful reason if possible
    stem = name.rsplit('.', 1)[0]
    parts = stem.split("_", 4)
    if len(parts) < 5:
        return {
            "status": "NON_COMPLIANT",
            "reason": "Filename must include prefix, type, process, 3-digit identifier, language, and document title.",
            "filename": name,
        }

    prefixes = _load_reference_data()["prefixes"]
    types_doc = _load_reference_data()["types"]
    processes = _load_reference_data()["processes"]
    langs = _load_reference_data()["langs"]

    prefix, doc_type, process, number, rest = parts
    lang = rest.split()[0] if rest else ""

    if prefix not in prefixes:
        reason = f"Invalid prefix '{prefix}'. Expected one of: {', '.join(prefixes)}."
    elif doc_type not in types_doc:
        reason = f"Invalid document type '{doc_type}'. Expected one of: {', '.join(types_doc)}."
    elif process not in processes:
        reason = f"Invalid process '{process}'. Expected one of: {', '.join(processes)}."
    elif not re.match(r"^[0-9]{3}$", number):
        reason = "Document identifier must be a three-digit number (e.g. 001)."
    elif lang not in langs:
        reason = f"Invalid language '{lang}'. Expected one of: {', '.join(langs)}."
    else:
        reason = "Filename does not match the ATC naming convention."

    return {"status": "NON_COMPLIANT", "reason": reason, "filename": name}
