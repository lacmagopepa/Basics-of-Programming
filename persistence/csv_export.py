# persistence/csv_export.py
from pathlib import Path
from shutil import copy2
from datetime import datetime
import csv

def export_csv():
    src = Path("logs/game.csv")
    out_dir = Path("exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Read first row to extract scenario and policy info
    scenario = "UNKNOWN"
    policy = "UNKNOWN"
    try:
        with open(src, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            first_row = next(reader, None)
            if first_row:
                scenario = first_row.get("scenario", "UNKNOWN")
                policy = first_row.get("policy", "UNKNOWN")
    except Exception:
        pass
    
    # Create filename with policy, scenario, date and time
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"beer_game_{policy}_{scenario}_{ts}.csv"
    dst = out_dir / filename
    
    copy2(src, dst)
    return str(dst)
