"""
Cancellation flag shared across all pipeline modules.
 
Kept in a separate module to avoid circular imports between
update_pipeline.py and annotation.py.
"""
 
_cancel_flag = False
_cancel_view = None
 
 
class PipelineCancelledError(Exception):
    """Raised when the user requests cancellation between pipeline stages."""
    pass
 

def set_cancel_view(View):
    """
    Receive the JS Uint8Array backed by SharedArrayBuffer.
    Called once per pipeline run from the worker before execution starts.
    """
    global _cancel_view
    _cancel_view = View

def set_cancel_flag(value: bool):
    """
    Fallback: set the cancel flag directly (used if SharedArrayBuffer is unavailable).
    """
    if _cancel_view is not None:
        _cancel_view[0] = 1 if value else 0
    # global _cancel_flag


def check_cancel():
    """Raise PipelineCancelledError if cancellation has been requested."""
    # if _cancel_flag:
    #     raise PipelineCancelledError("Pipeline cancelled by user.")
    if _cancel_view is not None and _cancel_view[0] == 1:
        raise PipelineCancelledError("Pipeline cancelled by user.")