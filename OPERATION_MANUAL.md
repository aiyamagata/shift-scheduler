# シフト提案ツール 運用マニュアル

## 📋 目次
1. [概要](#概要)
2. [初回セットアップ](#初回セットアップ)
3. [自動実行の設定](#自動実行の設定)
4. [手動実行方法](#手動実行方法)
5. [結果の確認方法](#結果の確認方法)
6. [トラブルシューティング](#トラブルシューティング)
7. [定期メンテナンス](#定期メンテナンス)

---

## 概要

このツールは、Googleスプレッドシートから従業員の希望休を読み取り、最適なシフト案を自動生成して、同じスプレッドシートに書き戻すシステムです。

**主な機能:**
- 従業員の希望休を考慮したシフト自動生成
- 必要人数を満たすシフト案の提案
- 不足日・希望未反映セルの可視化
- Slackへの通知（オプション）

**実行方法:**
- 自動実行：Heroku Schedulerで毎月指定日に実行
- 手動実行：APIエンドポイントを呼び出し

---

## 初回セットアップ

### 1. スプレッドシートIDの確認

GoogleスプレッドシートのURLから、スプレッドシートIDを確認します。

**例:**
```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
```
この場合、スプレッドシートIDは `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` です。

### 2. スプレッドシートの構造確認

以下のシートが存在することを確認してください：

- **`Employees`シート**: 従業員マスタ
  - 必須列: `EmployeeID`, `Name`, `FixedPattern`
- **`Requests`シート**: 希望休入力
  - 必須列: `Date`, `Day`, 各従業員ID列（`OFF`/`WORK`）
- **`Schedule`シート**: 生成結果出力先（自動生成されます）
- **`Summary`シート**: 集計結果出力先（自動生成されます）

### 3. Google認証の確認

Heroku上でGoogle認証が正しく設定されているか確認：

```bash
heroku config:get GOOGLE_TOKEN_JSON
```

JSON形式の文字列が表示されればOKです。

---

## 自動実行の設定

### ステップ1: Heroku Schedulerアドオンを追加

```bash
heroku addons:create scheduler:standard
```

**注意**: Schedulerアドオンは有料プランが必要な場合があります。Eco Dynoプラン（$5/月）で利用可能です。

### ステップ2: スケジュールを設定

```bash
heroku addons:open scheduler
```

ブラウザでHeroku Schedulerの設定画面が開きます。

### ステップ3: ジョブを追加

1. 「Create job」ボタンをクリック
2. 以下のように設定：

   **Run Command:**
   ```
   curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule -H 'Content-Type: application/json' -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":""}'
   ```
   
   **重要**: `あなたのスプレッドシートID` の部分を実際のスプレッドシートIDに置き換えてください。
   
   **Schedule:**
   - `0 10 20 * *` （毎月20日の10:00 UTC = 日本時間19:00）
   - または `0 10 20 * *` を `0 10 20 * *` の形式で設定
   
   **Timezone:**
   - `Asia/Tokyo`（日本時間の場合）

3. 「Save job」をクリック

### ステップ4: テスト実行

設定画面で「Run now」ボタンをクリックして、手動で実行してみます。

実行後、以下を確認：
- Googleスプレッドシートの`Schedule`シートに結果が出力されている
- `Summary`シートに集計結果が表示されている
- エラーが発生していない（Herokuログで確認）

---

## 手動実行方法

### 方法1: curlコマンドで実行

```bash
curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule \
  -H 'Content-Type: application/json' \
  -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":"2025-12"}'
```

**パラメータ:**
- `spreadsheet_id`: 必須。GoogleスプレッドシートID
- `month`: 任意。`YYYY-MM`形式（例: `2025-12`）。省略時は「次月」が自動選択されます

**レスポンス:**
- 成功: `{"status":"success","month":"2025-12"}`
- 失敗: `{"status":"failed","month":"2025-12"}` または `{"error":"エラーメッセージ"}`

### 方法2: ブラウザから実行（Postman等のツール使用）

1. Postmanやcurlコマンドが使えるツールを開く
2. 以下の設定でリクエストを送信：
   - **Method**: POST
   - **URL**: `https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule`
   - **Headers**: `Content-Type: application/json`
   - **Body** (JSON):
     ```json
     {
       "spreadsheet_id": "あなたのスプレッドシートID",
       "month": "2025-12"
     }
     ```

### 方法3: ローカルから実行

```bash
cd "/Users/yamagataai/Desktop/シフト提案ツール"
source venv/bin/activate
python src/sheets_auth.py --month 2025-12
```

---

## 結果の確認方法

### 1. Googleスプレッドシートで確認

実行後、以下のシートを確認してください：

**`Schedule`シート:**
- 各日付ごとに、各従業員の出勤（`WORK`）または休み（`OFF`）が表示されます
- **赤字**: 必要人数が満たされていない日（Date列が赤字表示）
- **緑字**: 希望休が反映されなかったセル（希望休だったのに出勤になった場合）

**`Summary`シート:**
- 各従業員の勤務日数・休日日数・希望未反映件数が集計されます

### 2. Herokuログで確認

```bash
heroku logs --tail
```

実行ログが表示されます。エラーが発生している場合は、ここで確認できます。

### 3. Slack通知で確認（設定している場合）

`SLACK_WEBHOOK_URL`が設定されている場合、実行完了時にSlackに通知が送信されます。

通知内容：
- 実行期間
- 不足日数
- 希望未反映件数
- スプレッドシートURL

---

## トラブルシューティング

### 問題1: シフトが生成されない

**確認事項:**
1. スプレッドシートIDが正しいか
2. `Employees`シートと`Requests`シートが正しく入力されているか
3. Herokuログでエラーを確認：
   ```bash
   heroku logs --tail
   ```

**解決策:**
- スプレッドシートの構造を確認
- 従業員データと希望休データが正しく入力されているか確認
- エラーメッセージを確認して、該当する問題を修正

### 問題2: Google認証エラー

**エラーメッセージ例:**
```
Invalid credentials
Token expired
```

**解決策:**
1. ローカルで新しいトークンを生成：
   ```bash
   python src/sheets_auth.py --month 2025-12
   ```
2. 新しいトークンをHerokuに設定：
   ```bash
   heroku config:set GOOGLE_TOKEN_JSON="$(cat credentials/token.json | tr -d '\n')"
   ```

### 問題3: 必要人数が満たされない日がある

**原因:**
- 希望休が多すぎる
- 従業員数が不足している
- 固定勤務パターンと希望休の組み合わせで制約が厳しすぎる

**解決策:**
- `Schedule`シートで赤字表示されている日を確認
- 希望休の調整を依頼
- 従業員数の見直しを検討

### 問題4: Schedulerが実行されない

**確認事項:**
1. Schedulerアドオンが正しく設定されているか：
   ```bash
   heroku addons
   ```
2. ジョブが正しく設定されているか：
   ```bash
   heroku addons:open scheduler
   ```
3. ログで実行履歴を確認：
   ```bash
   heroku logs --tail
   ```

**解決策:**
- Schedulerの設定を再確認
- スケジュール設定が正しいか確認（タイムゾーンなど）
- 手動で「Run now」を実行してテスト

---

## 定期メンテナンス

### 月次メンテナンス

1. **実行結果の確認**
   - 毎月のシフト生成後、`Schedule`シートと`Summary`シートを確認
   - 不足日や希望未反映がないか確認

2. **ログの確認**
   ```bash
   heroku logs --tail --num 100
   ```
   エラーがないか確認

3. **Google認証トークンの確認**
   - トークンの有効期限を確認
   - 期限切れの場合は更新（通常は自動更新されますが、問題がある場合は手動更新）

### 四半期メンテナンス

1. **依存パッケージの更新**
   - `requirements.txt`のパッケージバージョンを確認
   - セキュリティアップデートがあれば適用

2. **コードの更新**
   - GitHubリポジトリから最新のコードを取得
   - 必要に応じてHerokuにデプロイ

3. **バックアップ**
   - Googleスプレッドシートのバックアップを作成
   - 重要なデータは定期的にバックアップ

### 年次メンテナンス

1. **Herokuプランの見直し**
   - 使用状況を確認
   - 必要に応じてプランの変更を検討

2. **セキュリティ確認**
   - 認証情報の漏洩がないか確認
   - 環境変数の見直し

---

## よくある質問（FAQ）

### Q1: スプレッドシートIDはどこで確認できますか？

A: GoogleスプレッドシートのURLから確認できます。
```
https://docs.google.com/spreadsheets/d/[スプレッドシートID]/edit
```
`[スプレッドシートID]`の部分がスプレッドシートIDです。

### Q2: 毎月の実行日時を変更したい

A: Heroku Schedulerの設定画面で変更できます。
```bash
heroku addons:open scheduler
```
設定画面で、既存のジョブを編集して、Scheduleを変更してください。

### Q3: 複数のスプレッドシートに対応できますか？

A: はい。手動実行の場合は、`spreadsheet_id`パラメータを変更するだけで対応できます。
自動実行で複数のスプレッドシートに対応する場合は、複数のジョブを作成するか、コードを修正する必要があります。

### Q4: エラーが発生した場合、誰に連絡すればいいですか？

A: システム管理者に連絡してください。Herokuログを確認して、エラーの詳細を共有してください。

---

## 緊急時の対応

### アプリが起動しない場合

1. **ヘルスチェック:**
   ```bash
   curl https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/health
   ```

2. **ログ確認:**
   ```bash
   heroku logs --tail
   ```

3. **再起動:**
   ```bash
   heroku restart
   ```

### データが正しく生成されない場合

1. **手動実行でテスト:**
   ```bash
   curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule \
     -H 'Content-Type: application/json' \
     -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":"2025-12"}'
   ```

2. **ログでエラーを確認**

3. **スプレッドシートの構造を確認**

---

## 連絡先・サポート

- **GitHubリポジトリ**: https://github.com/aiyamagata/shift-scheduler
- **Herokuダッシュボード**: https://dashboard.heroku.com/apps/shift-scheduler-aiyamagata

---

**最終更新日**: 2025年11月16日

