# シフト提案ツール カスタマイズガイド

## 1. シフトの必要条件を修正する場合

### 1-1. 必要人数の変更

**現在の設定:**
- 平日・土曜: 6名
- 日曜: 4名
- 水曜（店休日）: 0名

**修正箇所:** `src/shift_optimizer.py` の `get_required_staff_count()` 関数

**修正手順:**
1. `src/shift_optimizer.py` を開く
2. `get_required_staff_count()` 関数を探す（約150行目付近）
3. 以下の部分を修正：

```python
def get_required_staff_count(date_str: str) -> int:
    """日付から必要人数を取得"""
    if is_wednesday(date_str):  # 水曜日は店休
        return 0
    elif is_weekend(date_str):  # 土日
        if get_weekday(date_str) == 6:  # 日曜日
            return 4  # ← ここを変更
        else:  # 土曜日
            return 6  # ← ここを変更
    else:  # 平日
        return 6  # ← ここを変更
```

**例: 平日5名、土曜4名、日曜3名に変更する場合:**
```python
def get_required_staff_count(date_str: str) -> int:
    """日付から必要人数を取得"""
    if is_wednesday(date_str):  # 水曜日は店休
        return 0
    elif is_weekend(date_str):  # 土日
        if get_weekday(date_str) == 6:  # 日曜日
            return 3  # 変更
        else:  # 土曜日
            return 4  # 変更
    else:  # 平日
        return 5  # 変更
```

### 1-2. 休日日数の変更（月8〜9日休み）

**現在の設定:**
- 最低8日、最大9日の休み（店休日含む）

**修正箇所:** `src/shift_optimizer.py` の約276-304行目

**修正手順:**
1. `src/shift_optimizer.py` を開く
2. 約276行目の「制約5: 月8〜9日の休み」の部分を探す
3. 以下の部分を修正：

```python
# 約290行目付近
mandatory_off_count = len(mandatory_off)
required_additional_off = max(0, 8 - mandatory_off_count)  # ← 8を変更
required_additional_off = min(required_additional_off, len(flexible_dates))

# 約303行目付近
max_rest_allowed = max(9, len(mandatory_off))  # ← 9を変更
```

**例: 最低10日、最大12日の休みに変更する場合:**
```python
mandatory_off_count = len(mandatory_off)
required_additional_off = max(0, 10 - mandatory_off_count)  # 10に変更
required_additional_off = min(required_additional_off, len(flexible_dates))

# ...
max_rest_allowed = max(12, len(mandatory_off))  # 12に変更
```

### 1-3. 連続勤務日数の制約変更

**現在の設定:**
- 最大6日連続勤務（推奨、警告のみ）

**修正箇所:** `src/shift_optimizer.py` の約318-335行目

**修正手順:**
1. 約318行目の「制約5: 最大連続勤務6日」の部分を探す
2. 以下の部分を修正：

```python
# 約333行目付近
model.Add(window_sum <= 5 + overwork_var)  # ← 5を変更（5+1=6日連続まで）
```

**例: 最大4日連続勤務に変更する場合:**
```python
model.Add(window_sum <= 3 + overwork_var)  # 3+1=4日連続まで
```

### 1-4. 店休日の変更（水曜日以外）

**現在の設定:**
- 水曜日が店休日

**修正箇所:** `src/shift_optimizer.py` の複数箇所

**修正手順:**
1. `is_wednesday()` 関数を新しい店休日に合わせて変更、または新しい関数を作成
2. 約215行目の「制約1: 水曜日は全員休み」の部分を修正
3. 約228行目、約271行目など、`is_wednesday()` を使っている箇所を確認

**例: 月曜日を店休日に変更する場合:**
```python
def is_store_closed(date_str: str) -> bool:
    """店休日かどうかを判定（月曜日）"""
    return get_weekday(date_str) == 0  # 0=月曜日

# 制約1の部分を修正
for date in dates:
    if is_store_closed(date):  # is_wednesday() を is_store_closed() に変更
        for emp_id in employee_ids:
            model.Add(shifts[(emp_id, date)] == 0)
```

### 1-5. 勤務日数の下限制約の変更

**現在の設定:**
- 平均勤務日数 - 1日を下限

**修正箇所:** `src/shift_optimizer.py` の約272-316行目

**修正手順:**
1. 約274行目の `minimum_work_floor` の計算部分を修正
2. 約311行目の `min_work_days_for_emp` の計算部分を修正

**例: 平均勤務日数 - 2日を下限にする場合:**
```python
minimum_work_floor = max(0, int(average_work_target) - 2)  # -1 を -2 に変更
```

---

## 2. 時間の希望を追加する場合

### 2-1. データ構造の変更

**必要な変更:**
1. `Requests` シートの列を拡張（`OFF`/`WORK` に加えて時間帯を追加）
2. データ読み取り処理の変更
3. 最適化ロジックの変更
4. 結果出力の変更

### 2-2. スプレッドシート構造の変更

**`Requests` シートの列を拡張:**

現在:
- `Date`, `Day`, `従業員ID1`, `従業員ID2`, ...

変更後:
- `Date`, `Day`, `従業員ID1`, `従業員ID1_Time`, `従業員ID2`, `従業員ID2_Time`, ...

**入力例:**
- `従業員ID1` 列: `OFF` または `WORK`
- `従業員ID1_Time` 列: `11:00-15:00` または `15:00-20:00` など

### 2-3. コードの修正箇所

#### ステップ1: データ読み取り処理の変更

**ファイル:** `src/sheets_auth.py`

**修正箇所:** `parse_requests_data()` 関数（約67-78行目）

**変更内容:**
```python
def parse_requests_data(values: list) -> list:
    """希望休データを辞書形式に整形（時間帯対応）"""
    if not values or len(values) < 2:
        return []
    
    headers = values[0]
    requests = []
    for row in values[1:]:
        if row:  # 空行をスキップ
            request_dict = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            requests.append(request_dict)
    return requests
```

#### ステップ2: 最適化ロジックの変更

**ファイル:** `src/shift_optimizer.py`

**修正箇所:** 
1. `optimize_shift()` 関数の引数に時間帯情報を追加
2. 決定変数を拡張（勤務時間帯ごとに変数を作成）
3. 制約条件に時間帯の制約を追加

**変更例:**
```python
# 決定変数を拡張（時間帯ごと）
shifts = {}
for emp_id in employee_ids:
    for date in dates:
        # 時間帯ごとの変数を作成
        shifts[(emp_id, date, "morning")] = model.NewBoolVar(f"shift_{emp_id}_{date}_morning")
        shifts[(emp_id, date, "afternoon")] = model.NewBoolVar(f"shift_{emp_id}_{date}_afternoon")
        shifts[(emp_id, date, "full")] = model.NewBoolVar(f"shift_{emp_id}_{date}_full")
        
        # 1日1つの時間帯のみ勤務可能
        model.Add(
            shifts[(emp_id, date, "morning")] + 
            shifts[(emp_id, date, "afternoon")] + 
            shifts[(emp_id, date, "full")] <= 1
        )
```

#### ステップ3: 結果出力の変更

**ファイル:** `src/sheets_auth.py`

**修正箇所:** `write_schedule_data()` 関数（約81-200行目）

**変更内容:**
- 時間帯情報を含めて出力
- 例: `WORK (11:00-15:00)` のように表示

### 2-4. 実装の優先順位

1. **フェーズ1: データ構造の拡張**
   - `Requests` シートに時間帯列を追加
   - データ読み取り処理を変更

2. **フェーズ2: 最適化ロジックの拡張**
   - 時間帯ごとの決定変数を作成
   - 時間帯の制約を追加

3. **フェーズ3: 結果出力の拡張**
   - 時間帯情報を含めて出力
   - スプレッドシートに時間帯を表示

---

## 3. 修正後のデプロイ手順

### 3-1. ローカルでテスト

```bash
cd "/Users/yamagataai/Desktop/シフト提案ツール"
source venv/bin/activate
python src/sheets_auth.py --month 2025-12
```

### 3-2. GitHubにコミット

```bash
git add .
git commit -m "カスタマイズ内容の説明"
git push origin main
```

### 3-3. Herokuにデプロイ

```bash
git push heroku main
```

### 3-4. 動作確認

```bash
curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule \
  -H 'Content-Type: application/json' \
  -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":"2025-12"}'
```

---

## 4. よくあるカスタマイズ例

### 例1: 必要人数を曜日ごとに細かく設定

```python
def get_required_staff_count(date_str: str) -> int:
    """日付から必要人数を取得（曜日ごとに細かく設定）"""
    weekday = get_weekday(date_str)
    weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
    
    if weekday == 2:  # 水曜日は店休
        return 0
    elif weekday == 0:  # 月曜日
        return 5
    elif weekday == 1:  # 火曜日
        return 6
    elif weekday == 3:  # 木曜日
        return 6
    elif weekday == 4:  # 金曜日
        return 7
    elif weekday == 5:  # 土曜日
        return 6
    elif weekday == 6:  # 日曜日
        return 4
    return 6
```

### 例2: 特定の従業員に最低勤務日数を設定

```python
# 制約5の部分に追加
min_work_days_per_employee = {
    "2008": 20,  # 特定の従業員に最低20日勤務を要求
    "2009": 18,
}

for emp_id, min_days in min_work_days_per_employee.items():
    if emp_id in employee_ids:
        model.Add(
            sum(shifts[(emp_id, date)] for date in non_wednesday_dates)
            >= min_days
        )
```

---

## 5. トラブルシューティング

### 問題1: 制約が矛盾して解が見つからない

**原因:**
- 必要人数が多すぎる
- 希望休が多すぎる
- 固定勤務パターンと希望休の組み合わせが矛盾

**解決策:**
- ログを確認して、どの制約が矛盾しているか確認
- 必要人数や希望休の数を調整
- 固定勤務パターンを見直す

### 問題2: 修正後、エラーが発生する

**確認事項:**
1. 構文エラーがないか確認
2. インポートエラーがないか確認
3. ローカルでテストしてからデプロイ

**解決策:**
```bash
# 構文チェック
python -m py_compile src/shift_optimizer.py

# ローカルでテスト
python src/sheets_auth.py --month 2025-12
```

---

**最終更新日**: 2025年11月16日

