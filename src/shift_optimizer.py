from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set

from ortools.sat.python import cp_model


def normalize_date(date_str: str) -> str:
    """日付文字列を YYYY-MM-DD 形式に正規化"""
    if not date_str:
        return ""
    
    date_str = str(date_str).strip()
    
    # スラッシュ区切りをハイフン区切りに変換して試す
    date_str_slash = date_str.replace("/", "-")
    for fmt in ["%Y-%m-%d", "%Y/%m/%d"]:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # スラッシュをハイフンに変換したバージョンも試す
    try:
        date_obj = datetime.strptime(date_str_slash, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    return date_str  # 変換できない場合はそのまま返す


def get_weekday(date_str: str) -> int:
    """日付文字列から曜日を取得（0=月曜日, 6=日曜日）"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.weekday()


def get_weekday_japanese(date_str: str) -> str:
    """日付文字列から曜日を日本語で取得"""
    weekday = get_weekday(date_str)
    weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
    return weekday_names[weekday]


def is_weekend(date_str: str) -> bool:
    """土曜日または日曜日かどうかを判定"""
    weekday = get_weekday(date_str)
    return weekday == 5 or weekday == 6  # 5=土曜日, 6=日曜日


def is_wednesday(date_str: str) -> bool:
    """水曜日かどうかを判定（店休日）"""
    return get_weekday(date_str) == 2


def parse_fixed_pattern(value) -> Dict[str, Set[int]]:
    """
    FixedPattern 列の内容を解析し、勤務すべき曜日・休むべき曜日を返す
    
    フォーマット例:
        WORK:Mon,Tue,Thu,Fri,Sun;OFF:Wed,Sat
        WORK:月,火,木,金,日;OFF:水,土
    
    Args:
        value: セルの値
    
    Returns:
        {"work": set([weekday_index, ...]), "off": set([...])}
    """
    work_days: Set[int] = set()
    off_days: Set[int] = set()
    
    if not value:
        return {"work": work_days, "off": off_days}
    
    weekday_map = {
        "mon": 0, "monday": 0, "月": 0,
        "tue": 1, "tuesday": 1, "火": 1,
        "wed": 2, "wednesday": 2, "水": 2,
        "thu": 3, "thursday": 3, "木": 3,
        "fri": 4, "friday": 4, "金": 4,
        "sat": 5, "saturday": 5, "土": 5,
        "sun": 6, "sunday": 6, "日": 6,
    }
    
    text = str(value).replace("；", ";")
    segments = [segment.strip() for segment in text.split(";") if segment.strip()]
    
    for segment in segments:
        if ":" not in segment:
            continue
        prefix, days_str = segment.split(":", 1)
        prefix_clean = prefix.strip().lower()
        days = [day.strip().lower() for day in days_str.split(",") if day.strip()]
        
        mapped_days = {weekday_map[day] for day in days if day in weekday_map}
        
        if prefix_clean == "work":
            work_days |= mapped_days
        elif prefix_clean == "off":
            off_days |= mapped_days
    
    return {"work": work_days, "off": off_days}


def is_store_closed(date_str: str) -> bool:
    """店舗休日かどうかを判定（水曜日、または12月の29,30,31日）"""
    if is_wednesday(date_str):
        return True
    # 12月の29,30,31日をチェック
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        if date_obj.month == 12 and date_obj.day in [29, 30, 31]:
            return True
    except ValueError:
        pass
    return False


def get_required_staff_count(date_str: str) -> int:
    """日付に応じた必要人数を返す"""
    if is_store_closed(date_str):
        return 0  # 店休日
    elif get_weekday(date_str) == 6:  # 日曜日
        return 3  # 最低3名
    else:  # 平日（月・火・木・金・土）
        return 3  # 最低3名


def optimize_shift(
    employees: Dict[str, Dict],
    requests: List[Dict],
    start_date: str,
    end_date: str,
) -> List[Dict]:
    """
    シフトを最適化して返す
    
    Args:
        employees: 従業員データ（EmployeeIDをキーにした辞書）
        requests: 希望休データ（日付と従業員IDの組み合わせ）
        start_date: 開始日（YYYY-MM-DD形式）
        end_date: 終了日（YYYY-MM-DD形式）
    
    Returns:
        シフト結果のリスト（各要素は {"Date": "YYYY-MM-DD", "Shift1": "E01", ...}）
    """
    # 日付リストを生成
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    # 従業員IDのリスト
    employee_ids = list(employees.keys())
    num_employees = len(employee_ids)
    num_days = len(dates)
    
    # 希望休を辞書形式に変換（高速検索用）
    # {(date, employee_id): True} の形式
    request_dict = {}
    off_requests = []
    
    # 必須休暇・必須勤務日の管理用セット
    mandatory_off_dates_per_emp: Dict[str, Set[str]] = {
        emp_id: set() for emp_id in employee_ids
    }
    mandatory_work_dates_per_emp: Dict[str, Set[str]] = {
        emp_id: set() for emp_id in employee_ids
    }
    for req in requests:
        date_raw = req.get("Date", "")
        date = normalize_date(date_raw)  # 日付フォーマットを正規化
        if not date:
            continue
        
        # 店休日は希望を無視する
        if is_store_closed(date):
            continue
        
        # Requestsシートのすべての列をチェック（従業員ID列を探す）
        for key in req.keys():
            key_str = str(key).strip()
            # 従業員ID列かどうかを確認
            if key_str in employee_ids:
                emp_id = key_str
                raw_value = req.get(key, "")
                value = str(raw_value).strip().upper()
                if value == "OFF":
                    request_dict[(date, emp_id)] = True
                    off_requests.append((emp_id, date))
                    mandatory_off_dates_per_emp[emp_id].add(date)
            else:
                # 従業員IDで始まる列名の場合（例: "2005 名前"）
                for emp_id in employee_ids:
                    if key_str.startswith(emp_id):
                        raw_value = req.get(key, "")
                        value = str(raw_value).strip().upper()
                        if value == "OFF":
                            request_dict[(date, emp_id)] = True
                            off_requests.append((emp_id, date))
                            mandatory_off_dates_per_emp[emp_id].add(date)
                        break
    
    # 固定勤務者の情報を取得（FixedPattern を解析）
    fixed_patterns: Dict[str, Dict[str, Set[int]]] = {}
    for emp_id, emp_data in employees.items():
        pattern = parse_fixed_pattern(emp_data.get("FixedPattern"))
        if pattern["work"] or pattern["off"]:
            fixed_patterns[emp_id] = pattern
    
    fixed_employees = list(fixed_patterns.keys())
    
    # CP-SATモデルを作成
    model = cp_model.CpModel()
    
    # 決定変数: shifts[(employee_id, date)] = 1 ならその従業員がその日に勤務
    shifts = {}
    for emp_id in employee_ids:
        for date in dates:
            shifts[(emp_id, date)] = model.NewBoolVar(f"shift_{emp_id}_{date}")
    
    # 目的関数用に平日・土日（店休日以外）のシフト変数をまとめる
    all_shift_vars = [
        shifts[(emp_id, date)]
        for emp_id in employee_ids
        for date in dates
        if not is_store_closed(date)
    ]
    
    # 制約1: 店休日（水曜日、12月29-31日）は全員休み
    for date in dates:
        if is_store_closed(date):
            for emp_id in employee_ids:
                model.Add(shifts[(emp_id, date)] == 0)
                mandatory_off_dates_per_emp[emp_id].add(date)
    
    # 制約2: 従業員2005と2010は、どちらかが休みの場合はどちらかは必ず出勤
    emp_2005 = "2005"
    emp_2010 = "2010"
    if emp_2005 in employee_ids and emp_2010 in employee_ids:
        for date in dates:
            if not is_store_closed(date):
                # どちらかが休みなら、どちらかは必ず出勤
                # shifts[2005] + shifts[2010] >= 1 を満たす必要がある
                model.Add(shifts[(emp_2005, date)] + shifts[(emp_2010, date)] >= 1)
    
    # 制約3: 土曜日は2008以外全員出勤
    emp_2008 = "2008"
    if emp_2008 in employee_ids:
        for date in dates:
            if get_weekday(date) == 5:  # 土曜日
                if not is_store_closed(date):
                    for emp_id in employee_ids:
                        if emp_id != emp_2008:
                            model.Add(shifts[(emp_id, date)] == 1)
                            mandatory_work_dates_per_emp[emp_id].add(date)
    
    # 制約4: 各日の必要人数を満たす（不足分のみペナルティ、過剰配置は許容）
    shortage_vars = {}
    for date in dates:
        if is_store_closed(date):
            continue  # 店休日は既に処理済み
        
        required = get_required_staff_count(date)
        if required > 0:
            working_on_day = [
                shifts[(emp_id, date)] for emp_id in employee_ids
            ]
            shortage_var = model.NewIntVar(0, required, f"shortage_{date.replace('-', '')}")
            total_work = cp_model.LinearExpr.Sum(working_on_day)
            model.Add(total_work + shortage_var >= required)
            model.Add(shortage_var >= required - total_work)
            shortage_vars[date] = shortage_var
    
    # 制約5: 希望休（OFF）を強制的に休みにする
    for emp_id, date in off_requests:
        # 従業員IDが存在することを確認
        if emp_id not in employee_ids:
            print(f"警告: 従業員ID '{emp_id}' はEmployeesシートに存在しません。スキップします。")
            continue
        if (emp_id, date) not in shifts:
            print(f"警告: 従業員ID '{emp_id}' と日付 '{date}' の組み合わせが無効です。スキップします。")
            continue
        model.Add(shifts[(emp_id, date)] == 0)
        mandatory_off_dates_per_emp[emp_id].add(date)
    
    # 制約6: 固定勤務者の勤務パターン（必須、ただし希望休があれば休みにする）
    for fixed_emp, pattern in fixed_patterns.items():
        work_days = pattern["work"]
        off_days = pattern["off"]
        
        for date in dates:
            weekday = get_weekday(date)
            has_off_request = (date, fixed_emp) in request_dict
            
            if is_store_closed(date):  # 店休日
                model.Add(shifts[(fixed_emp, date)] == 0)
                mandatory_off_dates_per_emp[fixed_emp].add(date)
            elif weekday in off_days:
                model.Add(shifts[(fixed_emp, date)] == 0)
                mandatory_off_dates_per_emp[fixed_emp].add(date)
            elif weekday in work_days:
                if has_off_request:
                    model.Add(shifts[(fixed_emp, date)] == 0)
                    mandatory_off_dates_per_emp[fixed_emp].add(date)
                else:
                    model.Add(shifts[(fixed_emp, date)] == 1)
                    mandatory_work_dates_per_emp[fixed_emp].add(date)
            else:
                if has_off_request:
                    model.Add(shifts[(fixed_emp, date)] == 0)
                    mandatory_off_dates_per_emp[fixed_emp].add(date)
    
    # 男女バランスを最適化に組み込む
    # 従業員の性別を取得
    employee_sex = {}
    for emp_id in employee_ids:
        emp_data = employees.get(emp_id, {})
        sex = str(emp_data.get("Sex", "")).strip().upper()
        employee_sex[emp_id] = sex
    
    # 男女バランスのペナルティ変数
    gender_balance_vars = []
    
    non_store_closed_dates = [date for date in dates if not is_store_closed(date)]
    total_required_work = sum(get_required_staff_count(date) for date in dates)
    average_work_target = total_required_work / num_employees if num_employees > 0 else 0
    minimum_work_floor = max(0, int(average_work_target) - 1)  # 1日ぶんのゆとり
    
    # 制約7: 週休2日（水曜の店舗休みを含めた、週休2日）
    for emp_id in employee_ids:
        mandatory_off = mandatory_off_dates_per_emp.get(emp_id, set())
        mandatory_work = mandatory_work_dates_per_emp.get(emp_id, set())
        
        # 店休日以外で柔軟に調整できる日を抽出
        flexible_dates = [
            date for date in dates
            if not is_store_closed(date)
            and date not in mandatory_off
            and date not in mandatory_work
        ]
        
        # 週ごとに週休2日を確保
        # 各週（月曜日から日曜日まで）で、最低2日は休みにする
        weeks = {}
        for date in dates:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            # ISO週番号を使用（月曜日が週の始まり）
            week_num = date_obj.isocalendar()[1]
            year = date_obj.year
            week_key = f"{year}-W{week_num:02d}"
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(date)
        
        for week_key, week_dates in weeks.items():
            # その週の店休日以外の日付
            week_workable_dates = [date for date in week_dates if not is_store_closed(date)]
            if len(week_workable_dates) >= 2:
                # その週で最低2日は休みにする
                week_work_vars = [
                    shifts[(emp_id, date)] for date in week_workable_dates
                    if date not in mandatory_off and date not in mandatory_work
                ]
                if week_work_vars:
                    # 週休2日を確保（店休日を含む）
                    # 店休日以外で最低2日は休み
                    model.Add(
                        sum(week_work_vars) <= len(week_workable_dates) - 2
                    )
        
        mandatory_off_count = len(mandatory_off)
        required_additional_off = max(0, 8 - mandatory_off_count)
        required_additional_off = min(required_additional_off, len(flexible_dates))
        
        if flexible_dates and required_additional_off > 0:
            model.Add(
                sum(shifts[(emp_id, date)] for date in flexible_dates)
                <= len(flexible_dates) - required_additional_off
            )
        
        # 合計休日日数（店休日を含む）を計算
        rest_terms = [1 - shifts[(emp_id, date)] for date in dates]
        rest_total_expr = cp_model.LinearExpr.Sum(rest_terms)
        # 月休みの上限を 9 日に設定（店休含む）
        max_rest_allowed = max(9, len(mandatory_off))
        model.Add(rest_total_expr <= max_rest_allowed)
        
        # 最低勤務日数の下限（平均勤務日数 - 1 を目安に）
        mandatory_off_non_store_closed = {
            date for date in mandatory_off if not is_store_closed(date)
        }
        total_possible_work = len(non_store_closed_dates) - len(mandatory_off_non_store_closed)
        min_work_days_for_emp = min(total_possible_work, minimum_work_floor)
        if min_work_days_for_emp > 0:
            model.Add(
                sum(shifts[(emp_id, date)] for date in non_store_closed_dates)
                >= min_work_days_for_emp
            )
    
    # 制約8: 最大連続勤務6日（店休日を除く）- 可能な限り満たす
    # この制約は削除し、後で結果をチェックして警告を出す
    
    weekly_overwork_vars = []
    for emp_id in employee_ids:
        for start_idx in range(len(dates) - 6):
            window_dates = dates[start_idx:start_idx + 7]
            work_vars = [
                shifts[(emp_id, date)]
                for date in window_dates
                if not is_store_closed(date)
            ]
            if not work_vars:
                continue
            window_sum = cp_model.LinearExpr.Sum(work_vars)
            overwork_var = model.NewIntVar(0, 7, f"week_over_{emp_id}_{start_idx}")
            model.Add(window_sum <= 5 + overwork_var)
            weekly_overwork_vars.append(overwork_var)
    
    # 制約9: 男女バランスを最適化（各日の男女比を均等に近づける）
    for date in dates:
        if is_store_closed(date):
            continue
        
        # その日の男性・女性の勤務者数を計算
        male_workers = []
        female_workers = []
        for emp_id in employee_ids:
            sex = employee_sex.get(emp_id, "")
            if sex in ["男", "M", "MALE", "男性"]:
                male_workers.append(shifts[(emp_id, date)])
            elif sex in ["女", "F", "FEMALE", "女性"]:
                female_workers.append(shifts[(emp_id, date)])
        
        if male_workers and female_workers:
            male_count = cp_model.LinearExpr.Sum(male_workers) if male_workers else 0
            female_count = cp_model.LinearExpr.Sum(female_workers) if female_workers else 0
            # 男女の差を最小化するためのペナルティ変数
            gender_diff = model.NewIntVar(0, num_employees, f"gender_diff_{date.replace('-', '')}")
            model.Add(gender_diff >= male_count - female_count)
            model.Add(gender_diff >= female_count - male_count)
            gender_balance_vars.append(gender_diff)

    # 目的関数: 不足人数・週次超過勤務を最小化しつつ、可能な限り勤務人数を最大化
    total_possible_shifts = len(all_shift_vars)
    total_shifts_expr = cp_model.LinearExpr.Sum(all_shift_vars) if all_shift_vars else 0
    rest_expr = total_possible_shifts - total_shifts_expr if all_shift_vars else 0
    
    if shortage_vars:
        shortage_sum = cp_model.LinearExpr.Sum(list(shortage_vars.values()))
        weekly_overwork_sum = cp_model.LinearExpr.Sum(weekly_overwork_vars) if weekly_overwork_vars else 0
        gender_balance_sum = cp_model.LinearExpr.Sum(gender_balance_vars) if gender_balance_vars else 0
        # 余剰配置をより促進するため、休みの重みを強める
        # 男女バランスのペナルティも追加（優先度は中程度）
        model.Minimize(shortage_sum * 1000 + weekly_overwork_sum * 100 + gender_balance_sum * 50 + rest_expr * 10)
    else:
        if weekly_overwork_vars:
            gender_balance_sum = cp_model.LinearExpr.Sum(gender_balance_vars) if gender_balance_vars else 0
            model.Minimize(cp_model.LinearExpr.Sum(weekly_overwork_vars) * 100 + gender_balance_sum * 50 + rest_expr * 10)
        else:
            gender_balance_sum = cp_model.LinearExpr.Sum(gender_balance_vars) if gender_balance_vars else 0
            model.Minimize(gender_balance_sum * 50 + rest_expr * 10)
    
    # ソルバーを実行
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0  # タイムアウト設定
    status = solver.Solve(model)
    
    # デバッグ情報を出力
    if status == cp_model.INFEASIBLE:
        print(f"警告: 制約条件が矛盾しています。")
        print(f"  - 従業員数: {num_employees}名")
        print(f"  - 期間: {start_date} ～ {end_date} ({num_days}日)")
        print(f"  - 希望休の数: {len(request_dict)}件")
        fixed_label = ", ".join(fixed_employees) if fixed_employees else "なし"
        print(f"  - 固定勤務者: {fixed_label}")
        
        # 固定勤務者の勤務日数を確認
        if fixed_employees:
            for fixed_emp in fixed_employees:
                pattern = fixed_patterns[fixed_emp]
                work_days = pattern["work"]
                fixed_work_days = sum(
                    1 for date in dates
                    if get_weekday(date) in work_days and not is_store_closed(date)
                )
                print(f"  - 固定勤務者（{fixed_emp}）の勤務日数: {fixed_work_days}日（水曜除く）")
        
        # 各従業員の希望休みの数を確認
        print(f"\n  各従業員の希望休み数:")
        for emp_id in employee_ids:
            if emp_id in fixed_employees:
                continue
            employee_off_requests = sum(
                1 for (date, eid) in request_dict.keys() 
                if eid == emp_id
            )
            monthly_available = sum(1 for date in dates if not is_store_closed(date))
            print(f"    - {emp_id}: 希望休み {employee_off_requests}日 / 月間利用可能日数 {monthly_available}日")
        
        # 各日の必要人数と希望休の数を確認
        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        print(f"\n  各日の必要人数と利用可能人数:")
        for date in dates[:14]:  # 最初の2週間を表示
            required = get_required_staff_count(date)
            weekday = get_weekday(date)
            off_count = sum(1 for (d, e) in request_dict.keys() if d == date)
            # 固定勤務者がその日に勤務するかどうか
            fixed_working = 0
            if fixed_employees:
                weekday_num = get_weekday(date)
                for fixed_emp in fixed_employees:
                    pattern = fixed_patterns[fixed_emp]
                    work_days = pattern["work"]
                    off_days = pattern["off"]
                    
                    if is_store_closed(date):
                        continue
                    if weekday_num in off_days:
                        continue
                    if weekday_num in work_days and (date, fixed_emp) not in request_dict:
                        fixed_working += 1
            
            available = num_employees - off_count - fixed_working
            if is_store_closed(date):
                print(f"  - {date} ({weekday_names[weekday]}): 店休（必要人数0名）")
            else:
                fixed_status = "勤務" if fixed_working else "休み"
                if fixed_working > 1:
                    fixed_status = f"{fixed_working}名勤務"
                print(f"  - {date} ({weekday_names[weekday]}): 必要人数 {required}名 / 希望休 {off_count}名 / 固定勤務者 {fixed_status} / 利用可能 {available}名")
                if available < required:
                    print(f"    ⚠️ 利用可能人数が不足しています！")
    
    # 結果を取得
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result = []
        warnings = []  # 警告メッセージを格納
        insufficient_days = []  # 必要人数を満たせていない日を記録
        unmet_requests = {}  # 希望休が叶わなかった日を記録 {(date, emp_id): True}
        
        # 結果を構築（各従業員の列を持つ形式）
        # 従業員IDの順序を保持するために、Dateを最初に、その後従業員IDを順番に
        for date in dates:
            day_shifts = {}
            day_shifts["Date"] = date
            day_shifts["Day"] = get_weekday_japanese(date)  # 曜日を追加
            
            # 各従業員について、その日の勤務状況を記録（従業員IDの順序を保持）
            work_count = 0
            for emp_id in employee_ids:
                if is_store_closed(date):
                    # 店休日は全員OFF
                    day_shifts[emp_id] = "OFF"
                elif solver.Value(shifts[(emp_id, date)]) == 1:
                    # 勤務している場合
                    # 希望休があったのに勤務している場合は、希望が叶わなかった
                    if (date, emp_id) in request_dict:
                        day_shifts[emp_id] = "WORK"  # 緑文字で表示するため、特別な値にする
                        unmet_requests[(date, emp_id)] = True
                    else:
                        day_shifts[emp_id] = "WORK"
                    work_count += 1
                else:
                    day_shifts[emp_id] = "OFF"
            
            # 必要人数を満たせているかチェック
            if not is_store_closed(date):
                required = get_required_staff_count(date)
                if work_count < required:
                    insufficient_days.append(date)
                    warnings.append(
                        f"⚠️ {date}: 必要人数 {required}名に対して {work_count}名しか配置されていません"
                    )
            
            result.append(day_shifts)
        
        # 不足している日と希望が叶わなかった日をメタデータとして追加
        metadata = {}
        if insufficient_days:
            metadata["_insufficient_days"] = insufficient_days
        if unmet_requests:
            metadata["_unmet_requests"] = unmet_requests
        if metadata:
            result.append(metadata)
        
        # 月8日休みと連続勤務の制約をチェック
        print("\n=== 制約チェック結果 ===")
        
        # 月8日休みのチェック（月間で最低8日以上休む）
        for emp_id in employee_ids:
            monthly_work_days = sum(
                1 for date in dates 
                if solver.Value(shifts[(emp_id, date)]) == 1
            )
            monthly_rest_days = len(dates) - monthly_work_days
            
            if monthly_rest_days < 8:
                warnings.append(
                    f"⚠️ {emp_id}: 月8日休みの条件を満たしていません "
                    f"（月間休み: {monthly_rest_days}日 / 必要: 8日以上）"
                )
        
        # 連続勤務のチェック（7連勤以上を避ける）
        for emp_id in employee_ids:
            if emp_id in fixed_employees:
                continue  # 固定勤務者は除外
            
            max_consecutive = 0
            current_consecutive = 0
            consecutive_start_date = None
            
            for i, date in enumerate(dates):
                if is_store_closed(date):
                    current_consecutive = 0  # 店休日でリセット
                    continue
                
                if solver.Value(shifts[(emp_id, date)]) == 1:
                    current_consecutive += 1
                    if current_consecutive == 1:
                        consecutive_start_date = date
                    if current_consecutive > max_consecutive:
                        max_consecutive = current_consecutive
                else:
                    if current_consecutive >= 7:
                        warnings.append(
                            f"⚠️ {emp_id}: {consecutive_start_date}から{current_consecutive}日連続勤務 "
                            f"（推奨: 最大6日連続）"
                        )
                    current_consecutive = 0
            
            # 最後の連続勤務もチェック
            if current_consecutive >= 7:
                warnings.append(
                    f"⚠️ {emp_id}: {consecutive_start_date}から{current_consecutive}日連続勤務 "
                    f"（推奨: 最大6日連続）"
                )
        
        # 固定勤務者のチェック（必須制約なので、違反があればエラー）
        # 注意: 固定勤務者は必須制約なので、通常は違反しないはず
        if fixed_employees:
            for fixed_emp in fixed_employees:
                pattern = fixed_patterns[fixed_emp]
                work_days = pattern["work"]
                off_days = pattern["off"]
                
                fixed_warnings = []
                for date in dates:
                    weekday = get_weekday(date)
                    is_working = solver.Value(shifts[(fixed_emp, date)]) == 1
                    has_off_request = (date, fixed_emp) in request_dict
                    
                    if is_store_closed(date):  # 店休日
                        if is_working:
                            fixed_warnings.append(f"{date}（店休日）に勤務しています（必須: 休み）")
                    elif weekday in off_days:
                        if is_working:
                            fixed_warnings.append(f"{date}（{get_weekday_japanese(date)}曜）に勤務しています（必須: 休み）")
                    elif weekday in work_days:
                        # 固定パターンが勤務日でも、希望OFFがあれば警告しない
                        if not is_working and not has_off_request:
                            fixed_warnings.append(f"{date}（{get_weekday_japanese(date)}曜）が休みです（必須: 勤務）")
                
                if fixed_warnings:
                    warnings.append(f"⚠️ 固定勤務者（{fixed_emp}）の必須パターンと異なる箇所: {len(fixed_warnings)}件")
                    for w in fixed_warnings[:5]:  # 最初の5件のみ表示
                        warnings.append(f"  - {w}")
        
        # 警告を出力
        if warnings:
            print("以下の制約が満たされていません:")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("✅ すべての制約が満たされています")
        
        return result
    else:
        print(f"警告: シフトの最適解が見つかりませんでした（ステータス: {status}）")
        return []

