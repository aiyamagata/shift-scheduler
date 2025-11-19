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

// シフト生成を実行する関数（Requestsシートから自動検出）
function generateShiftNextMonth() {
  try {
    const spreadsheetId = getSpreadsheetId();
    
    const ui = SpreadsheetApp.getUi();
    ui.alert('シフト生成中...', 'Requestsシートから月を自動検出してシフトを生成します。', ui.ButtonSet.OK);
    
    const payload = {
      'spreadsheet_id': spreadsheetId,
      'month': ''  // 空文字列で送ると、Requestsシートから自動検出されます
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
        const detectedMonth = result.month || '自動検出';
        ui.alert(
          'シフト生成完了',
          detectedMonth + 'のシフトを生成しました。\n\nScheduleシートとSummaryシートを確認してください。',
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

// シフト生成を実行する関数（Requestsシートから自動検出）
function generateShiftCurrentMonth() {
  try {
    const spreadsheetId = getSpreadsheetId();
    
    const ui = SpreadsheetApp.getUi();
    ui.alert('シフト生成中...', 'Requestsシートから月を自動検出してシフトを生成します。', ui.ButtonSet.OK);
    
    const payload = {
      'spreadsheet_id': spreadsheetId,
      'month': ''  // 空文字列で送ると、Requestsシートから自動検出されます
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
        const detectedMonth = result.month || '自動検出';
        ui.alert(
          'シフト生成完了',
          detectedMonth + 'のシフトを生成しました。\n\nScheduleシートとSummaryシートを確認してください。',
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

