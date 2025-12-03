# シフト提案ツール

従業員の希望休を考慮しながら、店舗の必要人数を満たすシフト案を自動生成するツールです。Googleスプレッドシートをデータソースとして使用し、OR-Toolsによる最適化アルゴリズムでシフトを生成します。

## 📋 目次

- [機能概要](#機能概要)
- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
- [シフト要件](#シフト要件)
- [API仕様](#api仕様)
- [デプロイ](#デプロイ)
- [ドキュメント](#ドキュメント)
- [注意事項](#注意事項)

## 機能概要

このツールは以下の機能を提供します：

- **自動シフト生成**: 従業員の希望休、固定シフト、店舗の必要人数を考慮して最適なシフトを自動生成
- **Googleスプレッドシート連携**: 従業員情報、希望休、生成結果をGoogleスプレッドシートで管理
- **制約条件の最適化**: OR-Toolsを使用した高度な制約プログラミングによる最適化
- **可視化**: 要件未達成日を赤色、希望未反映セルを緑色で表示
- **Slack連携**: 生成完了時にSlackへ通知（オプション）
- **Web API**: FlaskベースのRESTful APIで外部から実行可能

## 主な機能

### 1. シフト最適化エンジン

- **固定シフト対応**: `FixedPattern`列に指定された曜日パターンを厳密に反映
- **希望休の優先**: `Requests`シートで指定された希望休を可能な限り反映
- **人数制約**: 各日の必要人数を満たすように自動調整
- **週休2日の確保**: 全従業員が週休2日（店休日を含む）を確保
- **男女バランス**: 可能な限り男女のバランスを考慮
- **平日人数バランス**: 月・火・木・金・日曜日の出勤人数を可能な限り均等化

### 2. データ管理

- **従業員マスタ**: `Employees`シートで従業員情報を管理
- **希望休入力**: `Requests`シートで希望休を入力
- **結果出力**: `Schedule`シートに生成結果を出力
- **集計情報**: `Summary`シートに勤務日数・休日日数・希望未反映件数を集計

### 3. 可視化機能

- **要件未達成日の表示**: シフト要件を満たしていない日付を赤色で表示
- **希望未反映の表示**: 希望休が反映されなかった場合、該当セルを緑色で「出勤」と表示

## 技術スタック

- **Python 3.13**: メイン言語
- **OR-Tools**: Google製の最適化ライブラリ（CP-SATソルバー）
- **Flask**: Web APIフレームワーク
- **Google Sheets API**: スプレッドシートの読み書き
- **gunicorn**: 本番環境用WSGIサーバー
- **Heroku**: デプロイ先プラットフォーム

## セットアップ

### 必要な環境

- Python 3.13以上
- Google Cloud Platformアカウント（Google Sheets APIの有効化が必要）
- Herokuアカウント（デプロイする場合）

### インストール手順

1. **リポジトリのクローン**

```bash
git clone https://github.com/あなたのユーザー名/shift-scheduler.git
cd shift-scheduler
```

2. **仮想環境の作成と有効化**

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

3. **依存パッケージのインストール**

```bash
pip install -r requirements.txt
```

4. **Google認証情報の設定**

- Google Cloud Consoleでプロジェクトを作成
- Google Sheets APIを有効化
- OAuth 2.0認証情報を作成（デスクトップアプリ）
- `credentials/credentials.json`として保存

5. **初回認証の実行**

```bash
python src/sheets_auth.py --month 2025-12
```

ブラウザが開いてGoogle認証が求められます。認証が完了すると`credentials/token.json`が作成されます。

## 使用方法

### コマンドラインからの実行

```bash
python src/sheets_auth.py --spreadsheet-id <スプレッドシートID> --month 2025-12
```

### Web APIからの実行

ローカル環境で起動:
```bash
export FLASK_APP=src/app.py
flask run
```

API呼び出し:
```bash
curl -X POST http://127.0.0.1:5000/generate_schedule \
  -H 'Content-Type: application/json' \
  -d '{"spreadsheet_id":"<スプレッドシートID>","month":"2025-12"}'
```

### Google Apps Scriptからの実行

GoogleスプレッドシートにGoogle Apps Scriptを設定することで、スプレッドシート内から直接シフト生成を実行できます。

詳細は`GOOGLE_APPS_SCRIPT.md`を参照してください。

## シフト要件

本ツールは以下のシフト要件に基づいて最適化を行います：

### 必須制約

1. **店休日**: 水曜日は全員休み（店舗休業日）
2. **特別休業日**: 12月29日、30日、31日は全員休み
3. **土曜日の出勤**: 従業員2008（村上）以外は全員出勤
4. **最低人数**: 平日・日曜日は最低3名の出勤が必要（4名以上も可）
5. **相互排他**: 従業員2005と2010は、どちらかが休みの場合はどちらかは必ず出勤
6. **週休2日**: 全従業員が週休2日を確保（水曜の店休日を含む）
   - 固定シフト従業員以外は、水曜以外でちょうど1日休み

### 固定シフト

- `FixedPattern`列に`WORK:月,火,木,金,日;OFF:水,土`のように指定
- 指定された曜日パターンを厳密に反映
- 希望休（有給）があれば休みに上書き

### 希望休

- `Requests`シートで`OFF`と入力した日は必ず休みにする
- やむを得ず勤務になった場合は緑字で「出勤」と表示

### 最適化目標（優先順位）

1. **不足人数の最小化**: 各日の必要人数を満たすことを最優先
2. **週休2日の確保**: 全従業員が週休2日を確保
3. **平日人数バランス**: 月・火・木・金・日曜日の出勤人数を可能な限り均等化
4. **週次超過勤務の抑制**: 週休2日を超える休みを抑制
5. **男女バランス**: 可能な限り男女のバランスを考慮

## API仕様

### エンドポイント

#### `GET /health`

ヘルスチェック用エンドポイント

**レスポンス:**
```json
{
  "status": "ok"
}
```

#### `POST /generate_schedule`

シフト生成を実行

**リクエストボディ:**
```json
{
  "spreadsheet_id": "スプレッドシートID（必須）",
  "month": "YYYY-MM（オプション、省略時はRequestsシートから自動検出）"
}
```

**レスポンス（成功）:**
```json
{
  "status": "success",
  "month": "2025-12"
}
```

**レスポンス（失敗）:**
```json
{
  "status": "failed",
  "month": "2025-12"
}
```

## デプロイ

### Herokuへのデプロイ

詳細な手順は`DEPLOYMENT_GUIDE.md`を参照してください。

**簡易手順:**

1. Heroku CLIのインストールとログイン
```bash
heroku login
```

2. Herokuアプリの作成
```bash
heroku create shift-scheduler-あなたの名前
```

3. 環境変数の設定
```bash
heroku config:set GOOGLE_TOKEN_JSON="$(cat credentials/token.json | tr -d '\n')"
heroku config:set SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXXX/YYY/ZZZ'  # オプション
```

4. デプロイ
```bash
git push heroku main
```

5. 動作確認
```bash
curl https://shift-scheduler-あなたの名前.herokuapp.com/health
```

### Heroku Schedulerの設定

毎月自動実行する場合は、Heroku Schedulerアドオンを追加して設定します。

```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler
```

詳細は`DEPLOYMENT_GUIDE.md`を参照してください。

## ドキュメント

プロジェクトには以下のドキュメントが含まれています：

- **PROJECT_OVERVIEW.md**: プロジェクト概要、要件、開発ロードマップ
- **DEPLOYMENT_GUIDE.md**: GitHub・Herokuへのデプロイ手順（初心者向け）
- **GOOGLE_APPS_SCRIPT.md**: Google Apps Scriptの設定方法
- **OPERATION_MANUAL.md**: 運用マニュアル
- **CHECKLIST_FOR_USERS.md**: ユーザー向けチェックリスト
- **CUSTOMIZATION_GUIDE.md**: カスタマイズガイド

## 注意事項

### 機密情報の管理

- `credentials/token.json`と`credentials/credentials.json`は`.gitignore`で除外されています
- これらのファイルはGitHubにアップロードされません
- Heroku上で実行する場合は、`GOOGLE_TOKEN_JSON`環境変数にトークンを設定してください

### Google認証トークンの有効期限

- Google OAuthトークンは一定期間で期限切れになります
- 期限切れの場合は、ローカルで再認証して新しいトークンを取得し、Herokuの環境変数を更新してください

### 制約条件の矛盾

- 制約条件が矛盾している場合、最適解が見つからない可能性があります
- その場合は、制約条件を見直すか、一部の制約を緩和してください

### パフォーマンス

- 従業員数や日数が多い場合、最適化に時間がかかる可能性があります
- タイムアウトが発生する場合は、制約条件を見直すか、最適化時間の上限を調整してください

## ライセンス

このプロジェクトは個人利用・商用利用を問わず自由に使用できます。

## サポート

問題が発生した場合は、以下の手順で確認してください：

1. ログを確認（`heroku logs --tail`）
2. 環境変数が正しく設定されているか確認（`heroku config`）
3. Google認証トークンが有効か確認
4. 制約条件が矛盾していないか確認

## 更新履歴

### 最新の変更点

- 平日人数バランスの重みを30から200に増加（日ごとの出勤人数の偏りを改善）
- 週休2日の制約を固定シフト従業員以外に厳密に適用
- 希望休の優先順位を向上
- 男女バランスを最適化（必須制約から最適化目標に変更）
- 12月29-31日の特別休業日対応
- 従業員2005と2010の相互排他制約の追加
- 土曜日の出勤制約（2008以外全員出勤）の追加

詳細な変更履歴はGitのコミット履歴を参照してください。

