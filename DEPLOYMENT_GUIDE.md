# GitHub・Heroku デプロイ手順書（初心者向け）

このガイドでは、シフト提案ツールをGitHubにアップロードし、Herokuにデプロイする手順を詳しく説明します。

---

## 📋 事前準備チェックリスト

デプロイを始める前に、以下を確認してください：

- [ ] GitHubアカウントを持っている（なければ [github.com](https://github.com) で作成）
- [ ] Herokuアカウントを持っている（なければ [heroku.com](https://heroku.com) で作成）
- [ ] ターミナル（コマンドライン）が使える
- [ ] Gitがインストールされている（`git --version` で確認可能）

---

## ステップ1: GitHubリポジトリの作成

### 1-1. GitHubでリポジトリを作成

1. [GitHub](https://github.com) にログイン
2. 右上の「+」ボタン → 「New repository」をクリック
3. リポジトリ名を入力（例: `shift-scheduler`）
4. **Public** または **Private** を選択（Private推奨：機密情報を含むため）
5. 「Initialize this repository with a README」は**チェックしない**（既存のコードがあるため）
6. 「Create repository」をクリック

### 1-2. リポジトリURLを控える

作成後、表示されるページのURLを控えておきます。
例: `https://github.com/あなたのユーザー名/shift-scheduler.git`

---

## ステップ2: ローカルでGitを設定（初回のみ）

ターミナルで以下を実行します：

```bash
# プロジェクトディレクトリに移動
cd "/Users/yamagataai/Desktop/シフト提案ツール"

# Gitのユーザー名とメールアドレスを設定（初回のみ）
git config --global user.name "あなたの名前"
git config --global user.email "あなたのメールアドレス"
```

---

## ステップ3: コードをGitにコミット

### 3-1. 現在の状態を確認

```bash
cd "/Users/yamagataai/Desktop/シフト提案ツール"
git status
```

`.gitignore`で除外されたファイル（`credentials/token.json`など）は表示されないはずです。

### 3-2. ファイルをステージング（追加）

```bash
# すべてのファイルを追加
git add .
```

### 3-3. コミット（変更を記録）

```bash
git commit -m "初回コミット: シフト提案ツールの基本実装"
```

---

## ステップ4: GitHubにプッシュ（アップロード）

### 4-1. リモートリポジトリを追加

ステップ1-2で控えたURLを使います：

```bash
git remote add origin https://github.com/あなたのユーザー名/shift-scheduler.git
```

### 4-2. GitHubにプッシュ

```bash
git branch -M main
git push -u origin main
```

**初回プッシュ時は認証が必要です：**
- ユーザー名とパスワード（またはPersonal Access Token）を求められます
- パスワードの代わりにPersonal Access Tokenを使う場合は、[GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) で作成してください

### 4-3. 確認

GitHubのリポジトリページをリロードして、ファイルがアップロードされているか確認してください。

---

## ステップ5: Herokuアプリの作成

### 5-1. Heroku CLIのインストール（未インストールの場合）

Heroku CLIがインストールされていない場合、以下のいずれかの方法でインストールしてください。

#### 方法1: 公式サイトから手動インストール（最も簡単・推奨）

パスワード入力の問題を避けるため、公式サイトから直接ダウンロードする方法が最も簡単です。

1. ブラウザで以下のURLを開く：
   - https://devcenter.heroku.com/articles/heroku-cli
   - または直接: https://cli-assets.heroku.com/heroku-darwin-x64.tar.gz

2. macOS用のインストーラーをダウンロード（通常は自動的にダウンロードフォルダに保存されます）

3. ダウンロードしたファイルを開いてインストールを実行

4. インストール確認：
```bash
heroku --version
```

**注意**: インストール後、ターミナルを再起動するか、以下を実行してください：
```bash
source ~/.zshrc
```

#### 方法1-2: スクリプトをダウンロードしてから実行（パスワード入力が必要）

1. スクリプトをダウンロード：
```bash
curl -o /tmp/heroku-install.sh https://cli-assets.heroku.com/install.sh
```

2. 実行権限を付与：
```bash
chmod +x /tmp/heroku-install.sh
```

3. スクリプトを実行（この時点でパスワード入力が求められます）：
```bash
/tmp/heroku-install.sh
```

4. インストール確認：
```bash
heroku --version
```

#### 方法2: Homebrewを使用（Homebrewがインストールされている場合）

```bash
# Homebrewがインストールされている場合
brew tap heroku/brew && brew install heroku
```

**Homebrewのインストール方法（未インストールの場合）:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 方法3: npmを使用（Node.jsがインストールされている場合）

Node.jsとnpmがインストールされている場合は、以下のコマンドでインストールできます：

```bash
npm install -g heroku
```

インストール確認：
```bash
heroku --version
```

### 5-2. Herokuにログイン

```bash
heroku login
```

ブラウザが開くので、Herokuアカウントでログインしてください。

### 5-3. Herokuアプリを作成

#### 5-3-1. アカウントの確認（支払い情報の登録が必要な場合）

**重要**: Herokuは2022年11月以降、無料プランを廃止しました。アプリを作成するには、支払い情報（クレジットカード）の登録が必要です。

**注意点:**
- 支払い情報を登録しても、**Eco Dynoプラン（$5/月）** を使用する限り、実際に課金されることはありません
- ただし、使用量がプランの上限を超えた場合のみ課金されます
- アカウント確認のためだけに必要で、登録後すぐに課金されるわけではありません

**手順:**
1. エラーメッセージに表示されているURLにアクセス：
   ```
   https://heroku.com/verify
   ```
2. Herokuダッシュボードにログイン
3. 「Account settings」→「Billing」に移動
4. クレジットカード情報を入力（確認のみで、すぐに課金されません）
5. 確認が完了したら、再度アプリ作成コマンドを実行

#### 5-3-2. アプリを作成

```bash
cd "/Users/yamagataai/Desktop/シフト提案ツール"
heroku create shift-scheduler-あなたの名前
```

**重要**: アプリ名は全世界で一意である必要があります。上記の例が使えない場合は、別の名前に変更してください。

作成されると、以下のようなURLが表示されます：
- Web URL: `https://shift-scheduler-あなたの名前.herokuapp.com`
- Git URL: `https://git.heroku.com/shift-scheduler-あなたの名前.git`

---

## ステップ6: 環境変数の設定（Heroku）

### 6-1. Slack Webhook URLを設定（任意）

Slack連携を使う場合は、以下を実行します：

```bash
heroku config:set SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXXX/YYY/ZZZ'
```

**Slack Webhook URLの取得方法：**
1. Slackワークスペースの設定 → 「アプリを管理」
2. 「Incoming Webhooks」を検索して追加
3. 投稿先チャンネルを選択
4. 表示されるWebhook URLをコピー

### 6-2. Google認証トークンを設定（必須）

Heroku上でGoogle Sheets APIを使用するため、認証トークンを環境変数として設定する必要があります。

#### 6-2-1. ローカルでトークンファイルを確認

まず、ローカルの`credentials/token.json`ファイルの内容を確認します：

```bash
cd "/Users/yamagataai/Desktop/シフト提案ツール"
cat credentials/token.json
```

このファイルが存在しない場合は、先にローカルで認証を実行してください：

```bash
python src/sheets_auth.py --month 2025-12
```

ブラウザが開いてGoogle認証が求められます。認証が完了すると`token.json`が作成されます。

#### 6-2-2. トークンをHerokuの環境変数に設定

`token.json`の内容を1行のJSON文字列として、Herokuの環境変数に設定します：

```bash
# macOS/Linuxの場合
heroku config:set GOOGLE_TOKEN_JSON="$(cat credentials/token.json | tr -d '\n')"
```

**Windowsの場合（PowerShell）:**
```powershell
$token = Get-Content credentials/token.json -Raw
heroku config:set GOOGLE_TOKEN_JSON="$token"
```

**手動で設定する場合:**
1. `credentials/token.json`を開く
2. 内容をすべてコピー（改行を含む）
3. 以下のコマンドで設定（`<JSON内容>`の部分を貼り付け）：

```bash
heroku config:set GOOGLE_TOKEN_JSON='<JSON内容>'
```

**重要**: JSON文字列内にシングルクォート（`'`）が含まれている場合は、エスケープするか、ダブルクォートで囲む必要があります。

#### 6-2-3. 設定の確認

```bash
heroku config:get GOOGLE_TOKEN_JSON
```

正しく設定されていれば、JSON形式の文字列が表示されます。

### 6-3. スプレッドシートIDを設定（必要に応じて）

アプリ内でスプレッドシートIDを環境変数から取得する設計にしている場合は：

```bash
heroku config:set SPREADSHEET_ID='あなたのスプレッドシートID'
```

### 6-4. 設定を確認

```bash
heroku config
```

---

## ステップ7: Herokuにデプロイ

### 7-1. コードをHerokuにプッシュ

```bash
git push heroku main
```

**注意**: 初回デプロイ時は、依存パッケージのインストールに数分かかることがあります。

### 7-2. デプロイの確認

デプロイが完了すると、以下のようなメッセージが表示されます：

```
remote: -----> Launching...
remote:        Released v1
remote:        https://shift-scheduler-あなたの名前.herokuapp.com/ deployed to Heroku
```

### 7-3. 動作確認

ブラウザで以下のURLにアクセスして、アプリが起動しているか確認します：

```
https://shift-scheduler-あなたの名前.herokuapp.com/health
```

「OK」や「{"status":"ok"}」のようなレスポンスが返ってくれば成功です。

---

## ステップ8: Heroku Schedulerの設定（自動実行）

### 8-1. Heroku Schedulerアドオンを追加

```bash
heroku addons:create scheduler:standard
```

### 8-2. スケジュールを設定

```bash
heroku addons:open scheduler
```

ブラウザでHeroku Schedulerの設定画面が開きます。

### 8-3. ジョブを追加

1. 「Create job」ボタンをクリック
2. 以下のように設定：
   - **Run Command**: `curl -s -X POST https://shift-scheduler-あなたの名前.herokuapp.com/generate_schedule -H 'Content-Type: application/json' -d '{"spreadsheet_id":"あなたのスプレッドシートID","month":""}'`
   - **Schedule**: `0 10 20 * *` （毎月20日の10:00 UTC = 日本時間19:00）
     - または `0 10 20 * *` を `0 10 20 * *` の形式で設定
   - **Timezone**: `Asia/Tokyo`（日本時間の場合）
3. 「Save job」をクリック

**スケジュールの例：**
- 毎月20日 10:00 UTC: `0 10 20 * *`
- 毎月20日 19:00 JST: `0 10 20 * *`（Timezone: Asia/Tokyo）
- 毎日 10:00 UTC: `0 10 * * *`

### 8-4. テスト実行

設定画面で「Run now」ボタンをクリックして、手動で実行してみます。
実行後、Googleスプレッドシートの`Schedule`シートと`Summary`シートを確認してください。

---

## ステップ9: 今後の更新方法

コードを変更した後、GitHubとHerokuの両方に反映する手順：

### 9-1. 変更をコミット

```bash
cd "/Users/yamagataai/Desktop/シフト提案ツール"
git add .
git commit -m "変更内容の説明"
```

### 9-2. GitHubにプッシュ

```bash
git push origin main
```

### 9-3. Herokuにデプロイ

```bash
git push heroku main
```

---

## 🔧 トラブルシューティング

### 問題1: Herokuアプリ作成時に「支払い情報の確認が必要」というエラーが出る

**エラーメッセージ例:**
```
To create an app, verify your account by adding payment information.
```

**原因:**
Herokuは2022年11月以降、無料プランを廃止しました。アプリを作成するには、支払い情報（クレジットカード）の登録が必要です。

**解決策:**
1. エラーメッセージに表示されているURLにアクセス：
   ```
   https://heroku.com/verify
   ```
2. Herokuダッシュボードにログイン
3. 「Account settings」→「Billing」に移動
4. クレジットカード情報を入力
5. 確認が完了したら、再度アプリ作成コマンドを実行：
   ```bash
   heroku create shift-scheduler-あなたの名前
   ```

**注意点:**
- 支払い情報を登録しても、**Eco Dynoプラン（$5/月）** を使用する限り、実際に課金されることはありません
- 使用量がプランの上限を超えた場合のみ課金されます
- アカウント確認のためだけに必要です

### 問題2: `git push` で認証エラーが出る

**解決策：**
- Personal Access Tokenを使用する（GitHub Settings > Developer settings > Personal access tokens）
- または、SSHキーを設定する

### 問題3: Herokuデプロイが失敗する

**確認事項：**
- `Procfile`が正しく存在するか
- `requirements.txt`に必要なパッケージがすべて記載されているか
- `runtime.txt`のPythonバージョンが正しいか

**ログを確認：**
```bash
heroku logs --tail
```

### 問題4: アプリが起動しない

**確認事項：**
- 環境変数が正しく設定されているか（`heroku config`）
- `/health`エンドポイントにアクセスしてエラーメッセージを確認

### 問題5: Google認証が失敗する

**確認事項：**
- 環境変数`GOOGLE_TOKEN_JSON`が正しく設定されているか（`heroku config:get GOOGLE_TOKEN_JSON`で確認）
- トークンの有効期限が切れていないか（Google OAuthトークンは一定期間で期限切れになります）

**解決策：**

1. **トークンの再生成**
   - ローカルで`python src/sheets_auth.py --month 2025-12`を実行して、新しいトークンを生成
   - 生成された`token.json`の内容を再度Herokuの環境変数に設定

2. **トークンの形式確認**
   - `token.json`は有効なJSON形式である必要があります
   - 環境変数に設定する際に、改行や特殊文字が正しく処理されているか確認

3. **ログでエラー内容を確認**
   ```bash
   heroku logs --tail
   ```
   認証エラーの詳細が表示されます

4. **トークンの手動更新**
   - トークンが期限切れの場合は、ローカルで再認証して新しいトークンを取得
   - 新しいトークンをHerokuの環境変数に再設定

---

## 📝 重要な注意事項

1. **機密情報の管理**
   - `credentials/token.json`と`credentials/credentials.json`は`.gitignore`で除外されています
   - これらのファイルはGitHubにアップロードされません
   - Heroku上で実行する場合は、`GOOGLE_TOKEN_JSON`環境変数にトークンを設定してください

2. **Google認証トークンの有効期限**
   - Google OAuthトークンは一定期間で期限切れになります（通常、数時間〜数日）
   - 期限切れの場合は、ローカルで再認証して新しいトークンを取得し、Herokuの環境変数を更新してください
   - より長期的な運用には、サービスアカウントキーの使用を検討してください

3. **スプレッドシートID**
   - スプレッドシートIDは環境変数として設定するか、APIリクエスト時に指定する必要があります

4. **Herokuのプランについて**
   - Herokuは2022年11月以降、無料プランを廃止しました
   - アプリを作成するには、支払い情報（クレジットカード）の登録が必要です
   - **Eco Dynoプラン（$5/月）** を使用する限り、実際に課金されることはありません
   - 無料プランでは、一定時間アクセスがないとアプリがスリープします
   - Schedulerは有料プランが必要な場合があります（確認してください）

5. **トークンのセキュリティ**
   - `GOOGLE_TOKEN_JSON`環境変数には機密情報が含まれています
   - この環境変数はHerokuの設定画面で確認できますが、他人に共有しないでください
   - トークンが漏洩した場合は、Google Cloud Consoleで認証情報を無効化してください

---

## ✅ デプロイ完了チェックリスト

- [ ] GitHubリポジトリにコードがアップロードされている
- [ ] Herokuアプリが作成されている
- [ ] `GOOGLE_TOKEN_JSON`環境変数が設定されている（必須）
- [ ] `SLACK_WEBHOOK_URL`環境変数が設定されている（任意）
- [ ] すべての環境変数が正しく設定されているか確認（`heroku config`）
- [ ] `/health`エンドポイントが正常に動作している
- [ ] `/generate_schedule`エンドポイントが正常に動作している（テスト実行）
- [ ] Heroku Schedulerが設定されている
- [ ] Schedulerのテスト実行が成功している
- [ ] Googleスプレッドシートの`Schedule`シートと`Summary`シートに結果が出力されている

---

以上でデプロイ手順は完了です！🎉

