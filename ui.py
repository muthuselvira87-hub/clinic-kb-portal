import runpy
from pathlib import Path

# Delegates execution to the full multi-page Clinic Helpdesk application
app_path = Path(__file__).parent / "frontend" / "app.py"
runpy.run_path(str(app_path), run_name="__main__")