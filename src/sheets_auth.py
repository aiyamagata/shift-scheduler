from __future__ import annotations

import pathlib
import pprint
import os
import json
import urllib.request

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from shift_optimizer import optimize_shift, normalize_date

# プロジェクトのベースディレクトリを取得
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]

# OAuthクライアントIDとトークンを置く場所
CREDENTIALS_FILE = BASE_DIR / "credentials" / "credentials.json"
TOKEN_FILE = BASE_DIR / "credentials" / "token.json"

# 必要な権限（Google Sheets の編集権限）
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_credentials() -> Credentials:
    """
    Google認証情報を取得
    優先順位:
    1. 環境変数 GOOGLE_TOKEN_JSON（Heroku用）
    2. ローカルの token.json ファイル
    3. ブラウザで認証フローを実行（ローカル開発用）
    """
    # 環境変数からトークンを取得（Heroku用）
    token_json = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_json:
        try:
            token_data = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            return creds
        except (json.JSONDecodeError, Exception) as e:
            print(f"警告: 環境変数 GOOGLE_TOKEN_JSON の解析に失敗しました: {e}")
    
    # ローカルの token.json ファイルから取得
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        return creds
    
    # ブラウザで認証フローを実行（ローカル開発用）
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"認証情報ファイルが見つかりません: {CREDENTIALS_FILE}\n"
            "ローカル開発の場合は credentials/credentials.json を配置してください。\n"
            "Herokuの場合は環境変数 GOOGLE_TOKEN_JSON を設定してください。"
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    return creds


def read_sheet_data(service, spreadsheet_id: str, sheet_name: str, range_name: str) -> list:
    """指定したシートからデータを取得して返す"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!{range_name}",
        ).execute()
        return result.get("values", [])
    except Exception as e:
        print(f"エラー: シート '{sheet_name}' の読み取りに失敗しました: {e}")
        return []


def parse_employees_data(values: list) -> dict:
    """従業員データを辞書形式に整形（EmployeeIDをキーに）"""
    if not values or len(values) < 2:
        return {}
    
    headers = values[0]
    employees = {}
    for row in values[1:]:
        if row:  # 空行をスキップ
            emp_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            emp_id = emp_dict.get("EmployeeID", "")
            if emp_id:
                employees[emp_id] = emp_dict
    return employees


def parse_requests_data(values: list) -> list:
    """希望休データを辞書形式に整形"""
    if not values or len(values) < 2:
        return []
    
    headers = values[0]
    requests = []
    for row in values[1:]:
        if row:  # 空行をスキップ
            request_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            requests.append(request_dict)
    return requests


def write_schedule_data(service, spreadsheet_id: str, sheet_name: str, data: list, employees: dict = None):
    """
    シフト結果をシートに書き込む
    
    Args:
        service: Google Sheets API サービス
        spreadsheet_id: スプレッドシートID
        sheet_name: シート名
        data: シフトデータ（各日付ごとの辞書のリスト）
        employees: 従業員データ（EmployeeIDをキーにした辞書、名前を取得するために使用）
    """
    try:
        sheet = service.spreadsheets()
        
        # 不足している日と希望が叶わなかった日を取得（メタデータから）
        insufficient_days = []
        unmet_requests = {}
        schedule_data = []
        for row in data:
            if isinstance(row, dict):
                if "_insufficient_days" in row:
                    insufficient_days = row["_insufficient_days"]
                elif "_unmet_requests" in row:
                    unmet_requests = row["_unmet_requests"]
                elif "_insufficient_days" not in row and "_unmet_requests" not in row:
                    schedule_data.append(row)
            else:
                schedule_data.append(row)
        
        # データを2次元配列に変換
        values = []
        total_columns = 0

        if schedule_data and isinstance(schedule_data[0], dict):
            # ヘッダー行を作成（Date + 各従業員ID）
            # 従業員IDの順序を固定（employees辞書の順序を使用、なければデータから取得）
            if employees:
                # employees辞書の順序を使用（Requestsシートと同じ順序にするため）
                employee_ids = list(employees.keys())
            else:
                # employeesが提供されていない場合は、データから取得
                first_row = schedule_data[0]
                employee_ids = [key for key in first_row.keys() if key not in ["Date", "Day"]]
                employee_ids.sort()  # 順序を固定するためにソート
            
            # ヘッダー行: Date + Day + 従業員ID（名前付き）
            header_row = ["Date", "Day"]
            for emp_id in employee_ids:
                if employees and emp_id in employees:
                    # 従業員IDと名前を組み合わせて表示
                    emp_name = employees[emp_id].get("Name", "")
                    header_row.append(f"{emp_id}\n{emp_name}" if emp_name else emp_id)
                else:
                    header_row.append(emp_id)
            
            values.append(header_row)
            total_columns = len(header_row)
            
            # データ行を追加
            for row in schedule_data:
                data_row = [row.get("Date", ""), row.get("Day", "")]
                for emp_id in employee_ids:
                    val = row.get(emp_id, "")
                    # "WORK" を "出勤" に変換（表示用）
                    if val == "WORK":
                        data_row.append("出勤")
                    else:
                        data_row.append(val)
                values.append(data_row)
        else:
            values = schedule_data
            if values and isinstance(values[0], list):
                total_columns = len(values[0])
        
        body = {
            "values": values
        }
        
        result = sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="USER_ENTERED",  # ユーザーが入力した形式で書き込む
            body=body
        ).execute()
        
        # シートIDを取得
        sheet_metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = None
        for s in sheet_metadata.get("sheets", []):
            if s["properties"]["title"] == sheet_name:
                sheet_id = s["properties"]["sheetId"]
                break
        
        if sheet_id:
            format_requests = []
            total_rows = len(values)

            if total_rows > 0 and total_columns > 0:
                format_requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": total_rows,
                            "startColumnIndex": 0,
                            "endColumnIndex": total_columns,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {
                                    "foregroundColor": {
                                        "red": 0.0,
                                        "green": 0.0,
                                        "blue": 0.0,
                                    }
                                }
                            }
                        },
                        "fields": "userEnteredFormat.textFormat.foregroundColor",
                    }
                })
            
            # 不足している日のDate列を赤字で表示
            if insufficient_days:
                for i, row in enumerate(schedule_data, start=2):  # ヘッダー行を考慮して2から開始
                    date = row.get("Date", "")
                    if date in insufficient_days:
                        # Date列（A列）のみを赤字にする（範囲を明確に指定）
                        format_requests.append({
                            "repeatCell": {
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": i - 1,  # 0ベース（ヘッダー行を除く）
                                    "endRowIndex": i,
                                    "startColumnIndex": 0,  # A列（Date列）
                                    "endColumnIndex": 1  # A列のみ
                                },
                                "cell": {
                                    "userEnteredFormat": {
                                        "textFormat": {
                                            "foregroundColor": {
                                                "red": 1.0,
                                                "green": 0.0,
                                                "blue": 0.0
                                            }
                                        }
                                    }
                                },
                                "fields": "userEnteredFormat.textFormat.foregroundColor"
                            }
                        })
            
            # 希望が叶わなかった日を緑文字で表示（WORKのセルを緑色にする）
            if unmet_requests:
                # 従業員IDの列インデックスを取得
                emp_id_to_col = {}
                for idx, emp_id in enumerate(employee_ids, start=2):  # Date(0), Day(1)の後から
                    emp_id_to_col[emp_id] = idx
                
                for i, row in enumerate(schedule_data, start=2):  # ヘッダー行を考慮して2から開始
                    date = row.get("Date", "")
                    for emp_id in employee_ids:
                        if (date, emp_id) in unmet_requests:
                            col_idx = emp_id_to_col.get(emp_id)
                            if col_idx is not None:
                                # セルの値を"WORK"から"出勤"に変更（表示用）
                                # ただし、色付けは別途行う
                                format_requests.append({
                                    "repeatCell": {
                                        "range": {
                                            "sheetId": sheet_id,
                                            "startRowIndex": i - 1,  # 0ベース
                                            "endRowIndex": i,
                                            "startColumnIndex": col_idx,
                                            "endColumnIndex": col_idx + 1
                                        },
                                        "cell": {
                                            "userEnteredFormat": {
                                                "textFormat": {
                                                    "foregroundColor": {
                                                        "red": 0.0,
                                                        "green": 0.8,
                                                        "blue": 0.0
                                                    }
                                                }
                                            }
                                        },
                                        "fields": "userEnteredFormat.textFormat.foregroundColor"
                                    }
                                })
            
            # バッチ更新で色を変更
            if format_requests:
                batch_update_body = {
                    "requests": format_requests
                }
                sheet.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=batch_update_body
                ).execute()
                if insufficient_days:
                    print(f"不足している日 {len(insufficient_days)} 日のDate列を赤字で表示しました")
                if unmet_requests:
                    print(f"希望が叶わなかった日 {len(unmet_requests)} 件を緑文字で表示しました")
        
        print(f"書き込み完了: {result.get('updatedCells')} セル更新")
        
        # 追加: Summary シートの作成・更新
        try:
            summary = []
            # 従業員ID順を確定
            if employees:
                employee_ids = list(employees.keys())
            else:
                # Scheduleデータから抽出
                if schedule_data:
                    keys = list(schedule_data[0].keys())
                    employee_ids = [k for k in keys if k not in ["Date", "Day"]]
                else:
                    employee_ids = []
            
            # 未反映希望リストの復元
            unmet_set = set()
            if unmet_requests:
                for k, v in unmet_requests.items():
                    # k は "('YYYY-MM-DD', 'ID')" の形式で渡ってくる場合があるため両対応
                    try:
                        date, emp_id = k
                    except Exception:
                        # 文字列から安全に復元できない場合はスキップ
                        continue
                    unmet_set.add((date, emp_id))
            
            # 集計
            by_emp = {emp_id: {"Work": 0, "Off": 0, "Unmet": 0} for emp_id in employee_ids}
            for row in schedule_data:
                date = row.get("Date", "")
                for emp_id in employee_ids:
                    val = str(row.get(emp_id, "")).strip().upper()
                    if val == "OFF":
                        by_emp[emp_id]["Off"] += 1
                    elif val in ["WORK", "出勤"]:
                        by_emp[emp_id]["Work"] += 1
                    if (date, emp_id) in unmet_set:
                        by_emp[emp_id]["Unmet"] += 1
            
            # 2次元配列へ
            summary_values = [["EmployeeID", "Name", "WorkDays", "OffDays", "UnmetRequests"]]
            for emp_id in employee_ids:
                name = ""
                if employees and emp_id in employees:
                    name = employees[emp_id].get("Name", "")
                summary_values.append([
                    emp_id,
                    name,
                    by_emp[emp_id]["Work"],
                    by_emp[emp_id]["Off"],
                    by_emp[emp_id]["Unmet"],
                ])
            
            # Summary シートに書き込み（シートが無ければ作成）
            sheets_meta = sheet.get(spreadsheetId=spreadsheet_id).execute()
            sheet_titles = [s["properties"]["title"] for s in sheets_meta.get("sheets", [])]
            if "Summary" not in sheet_titles:
                sheet.batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={"requests":[{"addSheet":{"properties":{"title":"Summary"}}}]}
                ).execute()
            
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range="Summary!A1",
                valueInputOption="USER_ENTERED",
                body={"values": summary_values}
            ).execute()
            print("Summary シートを更新しました")
        except Exception as e:
            print(f"Summary シート更新時にエラー: {e}")
        
        # 追加: Slack Webhook への通知（環境変数 SLACK_WEBHOOK_URL が設定されている場合）
        try:
            webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
            if webhook:
                total_days = len(schedule_data)
                unmet_count = len(unmet_set) if 'unmet_set' in locals() else 0
                insufficient_count = len(insufficient_days)
                sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                
                lines = []
                lines.append("*シフト生成結果*")
                if schedule_data:
                    first_date = schedule_data[0].get("Date", "")
                    last_date = schedule_data[-1].get("Date", "")
                    lines.append(f"期間: {first_date} 〜 {last_date}（{total_days}日）")
                lines.append(f"不足日: {insufficient_count} 日")
                lines.append(f"希望未反映: {unmet_count} 件")
                lines.append(f"スプレッドシート: {sheet_url}")
                
                payload = {"text": "\n".join(lines)}
                req = urllib.request.Request(
                    webhook,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    _ = resp.read()
                print("Slack に投稿しました")
            else:
                print("Slack Webhook 未設定のため投稿をスキップしました（環境変数 SLACK_WEBHOOK_URL）")
        except Exception as e:
            print(f"Slack 投稿時にエラー: {e}")
        
        return result
    except Exception as e:
        print(f"エラー: シート '{sheet_name}' への書き込みに失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return None

def detect_month_from_requests(requests: list) -> str | None:
    """
    Requestsシートから月（YYYY-MM）を自動検出
    
    Args:
        requests: 希望休データのリスト
    
    Returns:
        検出された月（YYYY-MM形式）、検出できない場合はNone
    """
    from collections import Counter
    from datetime import datetime
    
    months = []
    for req in requests:
        date_raw = req.get("Date", "")
        if not date_raw:
            continue
        
        date_str = normalize_date(str(date_raw))
        if not date_str:
            continue
        
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month_str = date_obj.strftime("%Y-%m")
            months.append(month_str)
        except ValueError:
            continue
    
    if not months:
        return None
    
    # 最も多く出現する月を選択
    month_counter = Counter(months)
    most_common_month = month_counter.most_common(1)[0][0]
    return most_common_month


def generate_schedule(
    spreadsheet_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    employees_range: str = "A1:E10",
    requests_range: str = "A1:Z32",
) -> bool:
    """
    シフトを生成してScheduleシートに書き込む
    
    Args:
        spreadsheet_id: スプレッドシートID
        start_date: 開始日（YYYY-MM-DD形式）。Noneの場合はRequestsシートから自動検出
        end_date: 終了日（YYYY-MM-DD形式）。Noneの場合はRequestsシートから自動検出
        employees_range: Employeesシートの読み取り範囲
        requests_range: Requestsシートの読み取り範囲
    
    Returns:
        (成功したらTrue、失敗したらFalse, 検出された月（YYYY-MM形式、Noneの場合は指定された月）)
    """
    try:
        from datetime import date
        import calendar
        
        # 認証とサービス取得
        creds = get_credentials()
        service = build("sheets", "v4", credentials=creds)

        # Employees シートからデータを取得
        print("=== Employees シートを読み取り中 ===")
        employees_values = read_sheet_data(service, spreadsheet_id, "Employees", employees_range)
        employees = parse_employees_data(employees_values)
        print(f"従業員数: {len(employees)}")
        
        if not employees:
            print("エラー: 従業員データが見つかりませんでした")
            return False, None

        # Requests シートからデータを取得
        print("\n=== Requests シートを読み取り中 ===")
        requests_values = read_sheet_data(service, spreadsheet_id, "Requests", requests_range)
        requests = parse_requests_data(requests_values)
        print(f"希望データ数: {len(requests)}")
        
        # 開始日・終了日が指定されていない場合は、Requestsシートから自動検出
        detected_month = None
        if start_date is None or end_date is None:
            detected_month = detect_month_from_requests(requests)
            if detected_month:
                print(f"\n=== Requestsシートから月を自動検出: {detected_month} ===")
                year, mon = map(int, detected_month.split("-"))
                first_day = date(year, mon, 1)
                last_day = date(year, mon, calendar.monthrange(year, mon)[1])
                start_date = first_day.strftime("%Y-%m-%d")
                end_date = last_day.strftime("%Y-%m-%d")
                print(f"対象期間: {start_date} ～ {end_date}")
            else:
                print("エラー: Requestsシートから月を検出できませんでした")
                return False, None

        # シフト最適化を実行
        print("\n=== シフト最適化を実行中 ===")
        schedule_result = optimize_shift(employees, requests, start_date, end_date)
        
        if not schedule_result:
            print("エラー: シフトの生成に失敗しました")
            return False, detected_month

        print(f"生成されたシフト: {len(schedule_result)} 日分")

        # Schedule シートに書き込み
        print("\n=== Schedule シートに書き込み中 ===")
        write_schedule_data(service, spreadsheet_id, "Schedule", schedule_result, employees)
        
        # 検出された月を返す（指定されていた場合はstart_dateから計算）
        if detected_month is None and start_date:
            from datetime import datetime
            date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            detected_month = date_obj.strftime("%Y-%m")
        
        print("シフト生成完了！")
        return True, detected_month

    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print("詳細なエラー情報:")
        traceback.print_exc()
        return False, None


def main():
    """テストでシートを読み取り・書き込みするサンプル"""
    import argparse
    from datetime import date
    import calendar
    
    def month_bounds(ym: str):
        # ym: "YYYY-MM"
        year, mon = map(int, ym.split("-"))
        first_day = date(year, mon, 1)
        last_day = date(year, mon, calendar.monthrange(year, mon)[1])
        return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
    
    # デフォルト: 次月
    today = date.today()
    next_year = today.year + (1 if today.month == 12 else 0)
    next_month = 1 if today.month == 12 else today.month + 1
    default_ym = f"{next_year:04d}-{next_month:02d}"
    
    parser = argparse.ArgumentParser(description="Generate schedule from Google Sheets")
    parser.add_argument("--spreadsheet-id", type=str, default="1oOygBUXkXrVSw_To4d9snlYBsW9lBcFwXJ0YkmnYHVc", help="Google Spreadsheet ID")
    parser.add_argument("--month", type=str, default=default_ym, help='Target month in "YYYY-MM" (default: next month)')
    args = parser.parse_args()
    
    start_date, end_date = month_bounds(args.month)
    
    print("=== シフト生成テスト ===")
    success, detected_month = generate_schedule(
        spreadsheet_id=args.spreadsheet_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    if success:
        month_str = detected_month if detected_month else args.month
        print(f"\n✅ シフト生成が正常に完了しました！（対象月: {month_str}）")
    else:
        print("\n❌ シフト生成に失敗しました")

if __name__ == "__main__":
    main()