"""
Cancellation flag shared across all pipeline modules.
 
Kept in a separate module to avoid circular imports between
update_pipeline.py and annotation.py.
 
Two cancellation modes depending on environment:
    - SharedArrayBuffer (local dev): Python reads shared memory synchronously,
  works mid-loop even while the worker event loop is blocked.
    - Fallback flag (GitHub Pages / no COOP headers): set_cancel_flag() is called
  via postMessage between pipeline stages; cannot interrupt mid-loop.
"""
 
_cancel_flag = False
_cancel_view = None
 
 
class PipelineCancelledError(Exception):
    """Raised when the user requests cancellation between pipeline stages."""
    pass
 

def set_cancel_view(view):
    """
    Receive the JS Uint8Array backed by SharedArrayBuffer.
    Called once per pipeline run from the worker before execution starts.
    Pass None to disable shared-memory cancellation and use the flag fallback.
    """
    global _cancel_view
    try:
        _ = view[0]
        _cancel_view = view
    except (TypeError, IndexError):
        _cancel_view = None

def set_cancel_flag(value: bool):
    """
    Fallback: set the cancel flag directly.
    Used if SharedArrayBuffer is unavailable (e. g. GitHub Pages).
    """
    # if _cancel_view is not None:
    #     _cancel_view[0] = 1 if value else 0
    global _cancel_flag
    _cancel_flag = value


def check_cancel():
    """
    Check whether cancellation has been requested and raise if so.
 
    Reads from SharedArrayBuffer when available (works mid-loop),
    otherwise reads the boolean fallback flag (works between stages only).
    """
    if _cancel_view is not None:
        try:
            if _cancel_view[0] == 1:
                raise PipelineCancelledError("Pipeline cancelled by the user.")
        except (TypeError, IndexError):
            pass
    elif _cancel_flag:
        raise PipelineCancelledError("Pipeline cancelled by the user.")