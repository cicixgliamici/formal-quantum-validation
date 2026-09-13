"""Coq and SQIR formalization backend for quantum circuit validation."""

from fqv.backend.coq.generator import (
    GeneratedCoqModule,
    generate_coq_module,
    write_coq_module,
)
from fqv.backend.coq.transpilation import (
    generate_transpilation_coq_module,
    write_transpilation_coq_module,
)

__all__ = [
    "GeneratedCoqModule",
    "generate_coq_module",
    "write_coq_module",
    "generate_transpilation_coq_module",
    "write_transpilation_coq_module",
]
