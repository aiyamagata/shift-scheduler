# Google Apps Script でボタン追加ガイド

タブレットやスマホから簡単にシフト生成を実行できるように、Googleスプレッドシートにボタンを追加する方法です。

---

## 概要

Google Apps Scriptを使って、スプレッドシートに「シフト生成」ボタンを追加し、ボタンを押すだけでHerokuのAPIを呼び出してシフトを生成できるようにします。

**メリット:**
- タブレット/スマホから簡単に実行可能
- 複雑なコマンド入力が不要
- スプレッドシート上で完結

---

## セットアップ手順

### ステップ1: Google Apps Scriptエディタを開く

1. シフト管理用のGoogleスプレッドシートを開く
2. メニューから「拡張機能」→「Apps Script」を選択
3. 新しいスクリプトエディタが開きます

### ステップ2: スクリプトを記述

**重要**: 
- ```javascript のようなMarkdown記法は**不要**です。純粋なJavaScriptコードだけをコピーしてください。
- コードブロックの最初の行（```javascript）と最後の行（```）は**含めないでください**。

エディタに以下のコードを貼り付けます：

```javascript
// シフト生成APIのURL（実際のHerokuアプリURLに置き換える）
const HEROKU_API_URL = 'https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/generate_schedule';

// スプレッドシートIDを取得する関数
function getSpreadsheetId() {
  return SpreadsheetApp.getActiveSpreadsheet().getId();
}

// 現在の月を取得（YYYY-MM形式）
function getCurrentMonth() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth() + 1;
  const monthStr = (month < 10) ? '0' + month : String(month);
  return year + '-' + monthStr;
}

// 次月を取得（YYYY-MM形式）
function getNextMonth() {
  const today = new Date();
  let year = today.getFullYear();
  let month = today.getMonth() + 2; // 次月
  
  if (month > 12) {
    month = 1;
    year += 1;
  }
  
  const monthStr = (month < 10) ? '0' + month : String(month);
  return year + '-' + monthStr;
}

// シフト生成を実行する関数（次月を生成）
function generateShiftNextMonth() {
  try {
    const spreadsheetId = getSpreadsheetId();
    const targetMonth = getNextMonth();
    
    const ui = SpreadsheetApp.getUi();
    ui.alert('シフト生成中...', 'しばらくお待ちください。', ui.ButtonSet.OK);
    
    const payload = {
      'spreadsheet_id': spreadsheetId,
      'month': targetMonth
    };
    
    const options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(payload),
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(HEROKU_API_URL, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (responseCode === 200) {
      const result = JSON.parse(responseText);
      if (result.status === 'success') {
        ui.alert(
          'シフト生成完了',
          targetMonth + 'のシフトを生成しました。\n\nScheduleシートとSummaryシートを確認してください。',
          ui.ButtonSet.OK
        );
      } else {
        ui.alert(
          'シフト生成失敗',
          'シフトの生成に失敗しました。\n\nエラー: ' + (result.error || '不明なエラー'),
          ui.ButtonSet.OK
        );
      }
    } else {
      ui.alert(
        'エラー',
        'APIリクエストに失敗しました。\n\nステータスコード: ' + responseCode + '\n\nエラー: ' + responseText,
        ui.ButtonSet.OK
      );
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'エラーが発生しました。\n\n' + error.toString(),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

// シフト生成を実行する関数（今月を生成）
function generateShiftCurrentMonth() {
  try {
    const spreadsheetId = getSpreadsheetId();
    const targetMonth = getCurrentMonth();
    
    const ui = SpreadsheetApp.getUi();
    ui.alert('シフト生成中...', 'しばらくお待ちください。', ui.ButtonSet.OK);
    
    const payload = {
      'spreadsheet_id': spreadsheetId,
      'month': targetMonth
    };
    
    const options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(payload),
      'muteHttpExceptions': true
    };
    
    const response = UrlFetchApp.fetch(HEROKU_API_URL, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (responseCode === 200) {
      const result = JSON.parse(responseText);
      if (result.status === 'success') {
        ui.alert(
          'シフト生成完了',
          targetMonth + 'のシフトを生成しました。\n\nScheduleシートとSummaryシートを確認してください。',
          ui.ButtonSet.OK
        );
      } else {
        ui.alert(
          'シフト生成失敗',
          'シフトの生成に失敗しました。\n\nエラー: ' + (result.error || '不明なエラー'),
          ui.ButtonSet.OK
        );
      }
    } else {
      ui.alert(
        'エラー',
        'APIリクエストに失敗しました。\n\nステータスコード: ' + responseCode + '\n\nエラー: ' + responseText,
        ui.ButtonSet.OK
      );
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert(
      'エラー',
      'エラーが発生しました。\n\n' + error.toString(),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

// スプレッドシートを開いたときにメニューを追加
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('シフト生成')
    .addItem('シフトを生成（Requestsシートから自動検出）', 'generateShiftCurrentMonth')
    .addToUi();
}
```

**重要**: 
- `month`パラメータは空文字列（`''`）で送信されます
- これにより、RequestsシートのDate列から月が自動検出されます
- 当月・次月の指定は不要です

### ステップ3: スクリプトを保存

1. エディタの上部にある「保存」ボタン（💾）をクリック
2. プロジェクト名を入力（例: 「シフト生成スクリプト」）
3. 「OK」をクリック

### ステップ4: ボタンを追加

#### 方法1: メニューから実行（推奨・簡単）

1. スプレッドシートに戻る
2. メニューから「拡張機能」→「Apps Script」→「シフト生成」を選択
3. 初回実行時は認証が必要です（後述）

#### 方法2: カスタムメニューを追加（より使いやすい）

スクリプトに以下の関数を追加：

```javascript
// スプレッドシートを開いたときにメニューを追加
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('シフト生成')
    .addItem('今月のシフトを生成', 'generateShiftCurrentMonth')
    .addItem('次月のシフトを生成', 'generateShiftNextMonth')
    .addToUi();
}

// 今月のシフトを生成
function generateShiftCurrentMonth() {
  try {
    const spreadsheetId = getSpreadsheetId();
    const targetMonth = getCurrentMonth();
    
    const payload = {
      'spreadsheet_id': spreadsheetId,
      'month': targetMonth
    };
    
    const options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(payload),
      'muteHttpExceptions': true
    };
    
    const ui = SpreadsheetApp.getUi();
    ui.alert('シフト生成中...', 'しばらくお待ちください。', ui.ButtonSet.OK);
    
    const response = UrlFetchApp.fetch(HEROKU_API_URL, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (responseCode === 200) {
      const result = JSON.parse(responseText);
      if (result.status === 'success') {
        ui.alert(
          '✅ シフト生成完了',
          `${targetMonth}のシフトを生成しました。\n\nScheduleシートとSummaryシートを確認してください。`,
          ui.ButtonSet.OK
        );
      } else {
        ui.alert(
          '⚠️ シフト生成失敗',
          `エラー: ${result.error || '不明なエラー'}`,
          ui.ButtonSet.OK
        );
      }
    } else {
      ui.alert(
        '❌ エラー',
        `ステータスコード: ${responseCode}\n\nエラー: ${responseText}`,
        ui.ButtonSet.OK
      );
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert(
      '❌ エラー',
      error.toString(),
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}
```

#### 方法3: 図形をボタンとして使用（最も見やすい）

1. スプレッドシートで「挿入」→「図形描画」を選択
2. ボタンのような図形を描画（例: 四角形に「シフト生成」とテキスト）
3. 図形を右クリック→「スクリプトを割り当て」
4. 関数名を入力: `generateShiftNextMonth` または `generateShiftCurrentMonth`
5. 「OK」をクリック

### ステップ5: 初回認証

1. スクリプトを初めて実行すると、認証画面が表示されます
2. 「権限を確認」をクリック
3. Googleアカウントを選択
4. 「詳細」→「（プロジェクト名）に移動」をクリック
5. 「許可」をクリック

**注意**: 「このアプリは確認されていません」という警告が表示される場合がありますが、これは正常です。「詳細」→「（プロジェクト名）に移動」をクリックして続行してください。

---

## 使用方法

### タブレット/スマホから使用

1. Googleスプレッドシートアプリを開く
2. シフト管理用のスプレッドシートを開く
3. メニューから「シフト生成」→「次月のシフトを生成」を選択
   - または、図形ボタンをタップ
4. 確認ダイアログが表示されるので、「OK」をクリック
5. シフト生成が完了すると、完了メッセージが表示されます
6. `Schedule`シートと`Summary`シートを確認

---

## カスタマイズ

### API URLを変更する場合

スクリプトの最初の行を変更：

```javascript
const HEROKU_API_URL = 'https://あなたのアプリ名.herokuapp.com/generate_schedule';
```

### エラーメッセージをカスタマイズ

`generateShift()` 関数内の `ui.alert()` のメッセージを変更してください。

### 自動で次月を生成する（確認なし）

```javascript
function generateShiftNextMonthAuto() {
  // 確認なしで次月を生成
  const spreadsheetId = getSpreadsheetId();
  const targetMonth = getNextMonth();
  
  // ... (API呼び出しのコード)
}
```

---

## トラブルシューティング

### 問題1: 「権限が必要です」というエラーが出る

**解決策:**
1. Apps Scriptエディタを開く
2. 「実行」→「generateShift」を選択
3. 認証を再度実行

### 問題2: APIリクエストが失敗する

**確認事項:**
1. `HEROKU_API_URL` が正しいか確認
2. Herokuアプリが起動しているか確認：
   ```bash
   curl https://shift-scheduler-aiyamagata-47313535876f.herokuapp.com/health
   ```
3. スプレッドシートIDが正しいか確認

### 問題3: ボタンが表示されない（方法3の場合）

**解決策:**
1. 図形を再作成
2. スクリプトの割り当てを確認
3. スプレッドシートを再読み込み

### 問題4: タブレット/スマホでメニューが見つからない

**解決策:**
- 方法3（図形ボタン）を使用することを推奨
- または、スプレッドシートの上部に固定セルに「シフト生成」と書いて、そのセルにスクリプトを割り当てる

---

## セキュリティに関する注意

- このスクリプトは、スプレッドシートを開いているユーザーの権限で実行されます
- API URLは公開情報ですが、機密情報は含まれていません
- 必要に応じて、スクリプトの実行権限を制限できます（スプレッドシートの共有設定で制御）

---

## 完成例

スクリプトを正しく設定すると、以下のように使用できます：

1. **スプレッドシートを開く**
2. **メニューから「シフト生成」→「次月のシフトを生成」を選択**
   - または、図形ボタンをタップ
3. **確認ダイアログで「OK」をクリック**
4. **「シフト生成中...」と表示される**
5. **完了メッセージが表示される**
6. **`Schedule`シートと`Summary`シートを確認**

---

**最終更新日**: 2025年11月16日

