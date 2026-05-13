"""tools/pdf is deprecated — moved to tools/output in v0.3.2.

This shim re-exports the modules for backward compatibility with v0.3.1
code that imports from tools.pdf.
"""
import sys
import warnings

from tools.output import reportlab_compose  # noqa: F401
from tools.output import weasyprint_compose  # noqa: F401

# Expose submodule names so `from tools.pdf.weasyprint_compose import X` works.
sys.modules.setdefault("tools.pdf.reportlab_compose", reportlab_compose)
sys.modules.setdefault("tools.pdf.weasyprint_compose", weasyprint_compose)

warnings.warn(
    "tools.pdf is deprecated; use tools.output (v0.3.2)",
    DeprecationWarning,
    stacklevel=2,
)
