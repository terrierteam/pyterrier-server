import os
import pyterrier as pt


def load_pipeline():
    """Load a PyTerrier pipeline from the ``PYTERRIER_SERVE_PIPELINE`` environment variable.

    Environment variables:
        ``PYTERRIER_SERVE_PIPELINE``: PyTerrier pipeline expression (if type is 'expr')

    Returns:
        :class:`pyterrier.Transformer`: PyTerrier pipeline
    """
    # Load from a PyTerrier expression
    pipeline_expr = os.environ.get('PYTERRIER_SERVE_PIPELINE')
    if not pipeline_expr:
        raise ValueError("PYTERRIER_SERVE_PIPELINE environment variable not set")
    
    _globals = {'pt': pt}
    _locals = {}
    exec(pipeline_expr, _globals, _locals)
    for key in ['pipeline', 'p']:
        if key in _locals:
            return _locals[key]
    raise ValueError("pipeline not set in PYTERRIER_SERVE_PIPELINE")
