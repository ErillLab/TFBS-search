"""
Cancellation flag shared across all pipeline modules.
 
Kept in a separate module to avoid circular imports between
update_pipeline.py and annotation.py.
"""
 
_cancel_flag = False
 
 
class PipelineCancelledError(Exception):
    """Raised when the user requests cancellation between pipeline stages."""
    pass
 
 
def set_cancel_flag(value: bool):
    """Set or clear the cancellation flag. Called from JS via Pyodide."""
    global _cancel_flag
    _cancel_flag = value
 
 
def check_cancel():
    """Raise PipelineCancelledError if cancellation has been requested."""
    if _cancel_flag:
        raise PipelineCancelledError("Pipeline cancelled by user.")