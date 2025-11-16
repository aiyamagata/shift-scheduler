from __future__ import annotations

from datetime import date
import calendar
from flask import Flask, jsonify, request

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
        "month": "YYYY-MM"           # optional (default: next month)
      }
    """
    try:
        data = request.get_json(silent=True) or {}
        spreadsheet_id = (data.get("spreadsheet_id") or "").strip()
        if not spreadsheet_id:
            return jsonify({"error": "spreadsheet_id is required"}), 400

        ym = (data.get("month") or "").strip()
        if not ym:
            # default: next month
            today = date.today()
            year = today.year + (1 if today.month == 12 else 0)
            mon = 1 if today.month == 12 else today.month + 1
            ym = f"{year:04d}-{mon:02d}"

        start_date, end_date = month_bounds(ym)
        ok = generate_schedule(
            spreadsheet_id=spreadsheet_id,
            start_date=start_date,
            end_date=end_date,
        )
        if not ok:
            return jsonify({"status": "failed", "month": ym}), 500
        return jsonify({"status": "success", "month": ym}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


