# シフト提案ツール 開発ロードマップ・仕様・タスク一覧

## 1. プロジェクト概要
- **目的**: 従業員の希望休を考慮しながら、店舗の必要人数を満たすシフト案を自動生成し、Slack で共有できるようにする。
- **技術スタック**: Python, Google Sheets API, OR-Tools, Flask, Slack API/Webhook, Heroku（Scheduler 含む）。
- **データ連携**: Google スプレッドシートを単一のデータソースおよび結果出力先とし、API 経由で読み書きする。

## 2. シフト要件
- シフト時間: 原則 11:00-20:00。
- 固定勤務者: `FixedPattern` 列に `WORK:月,火,木,金,日;OFF:水,土` のように入力し、その曜日指定どおりに必ず勤務／休みを反映。希望休（有給）があれば休みに上書き。
- 水曜は店休日で全員休み。
- 希望休 (`Requests` シート): `OFF` と入力した日は必ず休みにする。やむを得ず勤務になった場合は緑字で「出勤」と表示。
- 土曜：2008村上以外全員出勤
- 平日、日曜日は最低でも3名確保。4名以上になってもOK
- 2005石出：Fixed patternに固定シフトを入力したので反映
- 12月は例外的に12/29,30,31は店舗休日のため全員休み
- 全員、水曜の店舗休みを含めた、週休2日
- 従業員はEmployee IDのみもしくは、Employee ID + 名前でも反映可能（例：2005　石出）
- 従業員2005と2010は、どちらかが休みの場合はどちらかは必ず出勤する
- "Employees"シートにC列（Sex)を追加。性別を男女で表記しているので、男女のバランスができる限り良くなるように調整。
- 満たせない日がある場合は `Schedule` シートで Date 列を赤字表示。

## 3. スプレッドシート構成
| シート名 | 役割 | 主な列 |
| --- | --- | --- |
| `Employees` | 従業員マスタ | `EmployeeID`, `Name`, `FixedPattern` など |
| `Requests` | 希望休入力 | `Date`, `Day`, 従業員 ID 列（`OFF`/`WORK` 等） |
| `Schedule` | 生成結果出力 | `Date`, `Day`, 従業員 ID 列（`WORK`/`OFF`） |

- `Schedule` では不足日を赤字、希望未反映セルを緑字で可視化。

## 4. 現在の実装状況
- Google Sheets 認証 (OAuth) と読み書き処理を実装済み。
- OR-Tools による最適化ロジックを実装し、固定勤務者・希望休・月 8 日休み・必要人数不足の警告を反映。
- 不足日/希望未反映セルの色付け処理を実装済み。
- スクリプト実行で `Schedule` シートに結果を書き出し可能。

## 5. 開発ロードマップ
1. **基盤整備 (完了)**  
   - 仮想環境・ライブラリセットアップ  
   - OAuth 認証フロー・Sheets API 接続  
   - シート読み取り/書き戻し処理
2. **最適化ロジック構築 (進行中)**  
   - OR-Tools モデル実装  
   - 固定シフト/希望休/人数制約の統合  
   - 可視化（赤字・緑字）機能
3. **Slack 連携**  
   - Webhook 設定  
   - 生成シフトをテキスト整形して投稿
4. **Web API 化**  
   - Flask アプリ作成（`/health`, `/generate_schedule`）  
   - ローカル起動テスト（`export FLASK_APP=src/app.py && flask run`）  
   - 認証情報・環境変数管理（`SLACK_WEBHOOK_URL`、Google OAuth `credentials/token.json`）
5. **デプロイ & 自動実行**  
   - GitHub リポジトリ整備  
   - Heroku へデプロイ（Procfile, gunicorn, runtime.txt）  
   - Heroku Scheduler で毎月 20 日実行
6. **運用準備**  
   - エラーハンドリング・ログ整備  
   - 運用マニュアル・README 作成  
   - 追加要望のヒアリングと改善計画

## 6. タスクリスト
- [x] 仮想環境作成・requirements 初版作成
- [x] Sheets API 認証・読み書きテスト
- [x] `sheets_auth.py` によるシート読み書き統合
- [x] `shift_optimizer.py` による制約モデリングと最適化
- [x] `Schedule` シートの色分け実装
- [x] 余剰配置促進（最低人数超の出勤を許容・促進する重み調整）
- [x] Summary シート出力（勤務・休み・希望未反映の集計）
- [x] 対象月指定 `--month YYYY-MM` と次月デフォルトの実装
- [x] Slack Webhook 連携と投稿（環境変数で切替）
- [x] Flask エンドポイント実装（/health, /generate_schedule）
- [x] Heroku 向け設定 (Procfile, runtime, config vars 追加済)
- [ ] Heroku Scheduler 設定と本番テスト
- [ ] 運用マニュアル・README・バックアップ手順作成

## 8. 実行手順（対象月指定・Summaryの見方）
- 対象月を指定して生成  
  ```bash
  cd "/Users/yamagataai/Desktop/シフト提案ツール"
  source venv/bin/activate
  python src/sheets_auth.py --month 2025-12
  ```
  省略時は「次月」が自動選択されます（例：今が11月なら12月）。
- 出力シート  
  - `Schedule`: Date, Day, 各従業員列（出勤/ OFF）。不足日は Date を赤字、希望未反映の出勤セルは緑字。  
  - `Summary`: `EmployeeID, Name, WorkDays, OffDays, UnmetRequests` を集計。

### Web API（ローカル）
```bash
export FLASK_APP=src/app.py
flask run
# 生成実行
curl -s -X POST http://127.0.0.1:5000/generate_schedule \
  -H 'Content-Type: application/json' \
  -d '{"spreadsheet_id":"<ID>","month":"2025-12"}'
```

### デプロイ（Heroku）
- 事前に `Procfile`, `runtime.txt`, `requirements.txt` を用意済み  
```bash
heroku login
heroku create shift-scheduler-<任意>
heroku config:set SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXX/YYY/ZZZ'
git add .
git commit -m "Deploy Flask app"
git push heroku HEAD:main
```
動作確認:
```bash
curl -s -X POST https://<your-app>.herokuapp.com/generate_schedule \
  -H 'Content-Type: application/json' \
  -d '{"spreadsheet_id":"<ID>","month":"2025-12"}'
```

## 9. Slack Webhook 連携
- 概要: 環境変数 `SLACK_WEBHOOK_URL` が設定されている場合、生成完了時にSlackへ要約を投稿します（期間・不足日数・希望未反映件数・シートURL）。
- 設定手順:
  1) SlackのインComing Webhookを作成（ワークスペースのApp設定）  
  2) Webhook URL を控える  
  3) ローカル: `export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXXX/YYY/ZZZ'`  
     Heroku: `heroku config:set SLACK_WEBHOOK_URL=...`  
- 無設定でも動作に支障はなく、投稿のみスキップします。

## 7. 今後のメモ
- 希望休が多い月や不足人数が解消できないケースに備え、手動調整ガイドを作成すると安心。
- Slack 投稿時に不足日・希望未反映セルのリストを添付すると担当者が把握しやすい。
- 将来的に Workload Identity Federation 等を検討し、鍵レス運用にも備える。

