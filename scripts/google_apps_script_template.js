/**
 * Google Apps Script dành cho Google Sheets "Ăn Dặm Mẹ Dâu"
 * Hướng dẫn sử dụng:
 * 1. Mở Google Sheets, vào Tiện ích mở rộng (Extensions) -> Apps Script.
 * 2. Dán toàn bộ mã nguồn này vào trình soạn thảo Code.gs.
 * 3. Điền TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID của bạn vào phần CẤU HÌNH bên dưới.
 * 4. Bấm Lưu và chạy hàm onOpen() một lần để cấp quyền.
 * 5. Menu "🍓 Ăn Dặm Mẹ Dâu" sẽ xuất hiện trên thanh công cụ của Google Sheets!
 */

// ==================== CẤU HÌNH (CONFIG) ====================
const TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"; // Thay bằng Token từ @BotFather
const TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE";     // Thay bằng Chat ID của bạn từ @userinfobot

// ==================== TẠO MENU TRÊN GOOGLE SHEETS ====================
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu("🍓 Ăn Dặm Mẹ Dâu")
    .addItem("🚀 Gửi Video dòng đang chọn sang Telegram", "sendSelectedRowToTelegram")
    .addItem("📅 Gửi Video hôm nay sang Telegram", "sendTodayVideosToTelegram")
    .addSeparator()
    .addItem("⚙️ Kiểm tra kết nối Telegram Bot", "testTelegramConnection")
    .addToUi();
}

// ==================== HÀM GỬI DÒNG ĐANG CHỌN ====================
function sendSelectedRowToTelegram() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const selectedRow = sheet.getActiveCell().getRow();
  
  if (selectedRow === 1) {
    SpreadApp.getUi().alert("Vui lòng chọn một dòng nội dung (từ dòng 2 trở đi), không chọn dòng tiêu đề!");
    return;
  }
  
  const rowData = sheet.getRange(selectedRow, 1, 1, 14).getValues()[0];
  sendVideoNotification(rowData, selectedRow);
}

// ==================== HÀM GỬI VIDEO THEO NGÀY HIỆN TẠI ====================
function sendTodayVideosToTelegram() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Tính ngày trong chu kỳ 30 ngày (Dựa trên ngày hiện tại)
  const today = new Date();
  const currentDayNumber = (today.getDate() % 30) || 30;
  
  let found = 0;
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (parseInt(row[0]) === currentDayNumber) {
      sendVideoNotification(row, i + 1);
      found++;
      Utilities.sleep(1000); // Tránh rate-limit của Telegram
    }
  }
  
  if (found === 0) {
    SpreadsheetApp.getUi().alert("Không tìm thấy video cho Ngày " + currentDayNumber);
  } else {
    SpreadsheetApp.getUi().alert("Đã gửi thành công " + found + " video của Ngày " + currentDayNumber + " sang Telegram!");
  }
}

// ==================== HÀM GỬI THÔNG BÁO VÀ TẠO NÚT BẤM TELEGRAM ====================
function sendVideoNotification(row, rowIndex) {
  const day = row[0];
  const slot = row[2];
  const pillar = row[3];
  const title = row[4];
  const hook = row[5];
  const body = row[6];
  const cta = row[7];
  const tiktokCaption = row[8] || "";
  const ytTitle = row[10] || "";
  const ytDesc = row[11] || "";
  
  const messageText = 
    `🍓 *[ĂN DẶM MẸ DÂU] — KẾ HOẠCH VIDEO NGÀY ${day} (${slot})*\n\n` +
    `📌 *Chủ đề:* ${pillar}\n` +
    `🎬 *Tiêu đề (3-8 từ):* ${title}\n\n` +
    `🎯 *Hook (Mở đầu):* "${hook}"\n\n` +
    `📝 *Thân bài:* ${body}\n\n` +
    `📣 *CTA (Kêu gọi):* "${cta}"\n\n` +
    `🔴 *YouTube Title:* ${ytTitle}\n` +
    `📱 *Caption TikTok:* \n\`${tiktokCaption.substring(0, 150)}...\`\n\n` +
    `⚠️ *Hành động:* Bấm nút bên dưới để xác nhận App Desktop bắt đầu render video này:`;

  const inlineKeyboard = {
    inline_keyboard: [
      [
        { text: "✅ Duyệt & Tạo Video", callback_data: `APPROVE_ROW_${rowIndex}_DAY_${day}` },
        { text: "❌ Bỏ qua / Sửa sau", callback_data: `REJECT_ROW_${rowIndex}_DAY_${day}` }
      ]
    ]
  };

  const payload = {
    chat_id: TELEGRAM_CHAT_ID,
    text: messageText,
    parse_mode: "Markdown",
    reply_markup: JSON.stringify(inlineKeyboard)
  };

  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
  const response = UrlFetchApp.fetch(url, options);
  const result = JSON.parse(response.getContentText());
  
  if (!result.ok) {
    Logger.log("Lỗi Telegram API: " + response.getContentText());
    SpreadsheetApp.getUi().alert("Lỗi khi gửi Telegram: " + result.description);
  }
}

// ==================== HÀM KIỂM TRA KẾT NỐI ====================
function testTelegramConnection() {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe`;
  try {
    const response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    const result = JSON.parse(response.getContentText());
    if (result.ok) {
      SpreadsheetApp.getUi().alert(`✅ Kết nối thành công với Bot: @${result.result.username}`);
    } else {
      SpreadsheetApp.getUi().alert(`❌ Token không hợp lệ: ${result.description}`);
    }
  } catch (e) {
    SpreadsheetApp.getUi().alert("❌ Lỗi mạng hoặc URL: " + e.toString());
  }
}
