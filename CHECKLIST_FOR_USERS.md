# シフト提案ツール 運用開始チェックリスト

実際に人に使ってもらう前に、以下の項目を確認・設定してください。

---

## ✅ 必須設定（完了必須）

### 1. スプレッドシートIDの確認と記録

- [ ] GoogleスプレッドシートのURLからスプレッドシートIDを確認
- [ ] スプレッドシートIDを安全な場所に記録（例: パスワードマネージャー）

**確認方法:**
```
URL例: https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
スプレッドシートID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

### 2. スプレッドシートの構造確認

- [ ] `Employees`シートが存在し、必要な列（`EmployeeID`, `Name`, `FixedPattern`）がある
- [ ] `Requests`シートが存在し、必要な列（`Date`, `Day`, 各従業員ID列）がある
- [ ] `Schedule`シートと`Summary`シートが自動生成されることを確認（存在しなくてもOK）

### 3. Google認証の確認

- [ ] Heroku上でGoogle認証トークンが設定されている
- [ ] トークンが有効期限内であることを確認

**確認コマンド:**
```bash
heroku config:get GOOGLE_TOKEN_JSON
```

### 4. アプリの動作確認

- [ ] ヘルスチェックが正常に動作する
- [ ] 手動実行でシフトが正しく生成される

**確認コマンド:**
```bash
# ヘルスチェック
curl https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/health

# 手動実行（スプレッドシートIDを実際の値に置き換える）
curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule \
  -H 'Content-Type: application/json' \
  -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":"2025-12"}'
```

---

## ✅ 自動実行の設定（推奨）

### 5. Heroku Schedulerの設定

- [ ] Schedulerアドオンを追加
- [ ] ジョブを作成（スプレッドシートIDを設定）
- [ ] スケジュールを設定（例: 毎月20日 19:00 JST）
- [ ] テスト実行で正常に動作することを確認

**設定コマンド:**
```bash
# Schedulerアドオンを追加
heroku addons:create scheduler:standard

# 設定画面を開く
heroku addons:open scheduler
```

**設定画面での入力:**
- **Run Command**: 
  ```
  curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule -H 'Content-Type: application/json' -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":""}'
  ```
- **Schedule**: `0 10 20 * *` （毎月20日の10:00 UTC = 日本時間19:00）
- **Timezone**: `Asia/Tokyo`

---

## ✅ オプション設定（任意）

### 6. Slack通知の設定

- [ ] Slack Webhook URLを取得
- [ ] Herokuの環境変数に設定

**設定コマンド:**
```bash
heroku config:set SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXXX/YYY/ZZZ'
```

### 7. ドキュメントの共有

- [ ] `OPERATION_MANUAL.md`を関係者に共有
- [ ] スプレッドシートIDを安全に共有（必要に応じて）

---

## ✅ 運用開始前の最終確認

### 8. テスト実行

- [ ] 手動実行でシフトが正しく生成される
- [ ] `Schedule`シートに結果が出力される
- [ ] `Summary`シートに集計結果が表示される
- [ ] エラーが発生していない（ログで確認）

**確認コマンド:**
```bash
# ログ確認
heroku logs --tail --num 50
```

### 9. 権限の確認

- [ ] Googleスプレッドシートへのアクセス権限が正しく設定されている
- [ ] 必要な従業員がスプレッドシートを編集できる

### 10. バックアップの準備

- [ ] スプレッドシートのバックアップ方法を確認
- [ ] 定期的なバックアップのスケジュールを設定（推奨）

---

## 📋 運用開始後の確認事項

### 初回実行後

- [ ] シフトが正しく生成されている
- [ ] 不足日がないか確認
- [ ] 希望未反映がないか確認
- [ ] Slack通知が届いている（設定している場合）

### 毎月の確認

- [ ] 自動実行が正常に完了している
- [ ] シフト結果を確認
- [ ] エラーがないかログで確認

---

## 🆘 トラブル時の対応

### エラーが発生した場合

1. **ログを確認:**
   ```bash
   heroku logs --tail
   ```

2. **手動実行でテスト:**
   ```bash
   curl -s -X POST https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule \
     -H 'Content-Type: application/json' \
     -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":"2025-12"}'
   ```

3. **`OPERATION_MANUAL.md`のトラブルシューティングセクションを参照**

---

## 📞 サポート連絡先

- **GitHubリポジトリ**: https://github.com/aiyamagata/shift-scheduler
- **Herokuダッシュボード**: https://dashboard.heroku.com/apps/shift-scheduler-aiyamagata

---

**チェックリスト完了日**: _______________
**確認者**: _______________

