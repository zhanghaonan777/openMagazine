"""pdf_selector — v0.3.1 backward-compat shim. Use tools.output.output_selector."""
import warnings

from tools.output.output_selector import OutputSelector as PdfSelector  # noqa: F401

warnings.warn(
    "tools.pdf.pdf_selector is deprecated; use tools.output.output_selector",
    DeprecationWarning,
    stacklevel=2,
)
