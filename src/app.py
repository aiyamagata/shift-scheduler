from __future__ import annotations

from datetime import date
import calendar
import sys
from pathlib import Path
from flask import Flask, jsonify, request

# Add src directory to Python path for Heroku deployment
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Support both "python src/app.py" and "FLASK_APP=src.app flask run"
try:
    # When executed as a module (FLASK_APP=src.app)
    from .sheets_auth import generate_schedule
except Exception:  # pragma: no cover - fallback for direct script runs
    # When executed as a script: python src/app.py
    from sheets_auth import generate_schedule


def month_bounds(ym: str) -> tuple[str, str]:
    """YYYY-MM → (YYYY-MM-01, YYYY-MM-<last>)"""
    year, mon = map(int, ym.split("-"))
    first_day = date(year, mon, 1)
    last_day = date(year, mon, calendar.monthrange(year, mon)[1])
    return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")


app = Flask(__name__)


@app.get("/health")
def health() -> tuple[dict, int]:
    return {"status": "ok"}, 200


@app.post("/generate_schedule")
def api_generate_schedule():
    """
    Request JSON:
      {
        "spreadsheet_id": "...",     # required
        "month": "YYYY-MM"           # optional (default: Requestsシートから自動検出)
      }
    """
    try:
        data = request.get_json(silent=True) or {}
        spreadsheet_id = (data.get("spreadsheet_id") or "").strip()
        if not spreadsheet_id:
            return jsonify({"error": "spreadsheet_id is required"}), 400

        ym = (data.get("month") or "").strip()
        if ym:
            # 月が指定されている場合はその月を使用
            start_date, end_date = month_bounds(ym)
        else:
            # 月が指定されていない場合は、Requestsシートから自動検出
            start_date = None
            end_date = None

        ok, detected_month = generate_schedule(
            spreadsheet_id=spreadsheet_id,
            start_date=start_date,
            end_date=end_date,
        )
        if not ok:
            month_str = detected_month if detected_month else (ym if ym else "自動検出")
            return jsonify({"status": "failed", "month": month_str}), 500
        
        # 成功時も検出された月を返す
        month_str = detected_month if detected_month else (ym if ym else "自動検出")
        return jsonify({"status": "success", "month": month_str}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


