"""Build-time helpers; not imported by the graphical offline runtime."""
import os
import sys

def configure_console():
    os.environ.setdefault('PYTHONUTF8','1')
    for stream in (sys.stdout,sys.stderr):
        if stream is not None and hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8',errors='backslashreplace')
