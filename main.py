import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os  # เพิ่มการนำเข้า os

# กำหนด token และ sheet id
TOKEN = '8043058951:AAGm2F2DlMdei-l34EPT-uzOFIj27FzHUlg'
SHEET_ID = '1JNTtut0dnntTBR0Byj4PouRquSWL-gCWlAkIPaUrQ1M'

# ตั้งค่า Google Sheets
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds",  'https://www.googleapis.com/auth/spreadsheets', 
             "https://www.googleapis.com/auth/drive.file",  "https://www.googleapis.com/auth/drive"] 
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet('เงินเชื่อ')
    
    # เขียน credentials.json จาก secret
    with open("credentials.json", "w") as f:
        f.write(os.getenv("GOOGLE_CREDENTIALS_JSON"))  # เขียนข้อมูลจาก environment variable
    return sheet

# คำสั่ง /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("สวัสดีครับ กรุณาพิมพ์ เลขที่เอกสาร เพื่อดูข้อมูล")

# รับเลขที่เอกสาร
def handle_message(update: Update, context: CallbackContext):
    doc_id = update.message.text.strip()
    sheet = get_sheet()

    try:
        cell = sheet.find(doc_id)
        row = sheet.row_values(cell.row)

        headers = ["วันที่ครบกำหนดชำระ", "เลขที่เอกสาร", "สาขา", "ชื่อ", "นามสกุล", "เบอร์โทร", "ยอดชำระ",
                   "ยอดค้างชำระ", "สถานะสินค้า", "บิล"]

        response = "\n".join([f"{h}: {v}" for h, v in zip(headers, row)])
        update.message.reply_text(response)
    except:
        update.message.reply_text("ไม่พบข้อมูลสำหรับเลขที่เอกสารนี้")

# คำสั่ง /update เลขที่เอกสาร|ยอดชำระ=1000
def update_data(update: Update, context: CallbackContext):
    args = update.message.text.replace("/update ", "").strip().split("|")
    if len(args) != 2:
        update.message.reply_text("กรุณาใช้รูปแบบ: /update เลขที่เอกสาร|ฟิลด์=ค่า")
        return

    doc_id = args[0]
    field, value = args[1].split("=")
    field = field.strip()
    value = value.strip()

    sheet = get_sheet()

    try:
        cell = sheet.find(doc_id)
        headers = sheet.row_values(1)
        if field not in headers:
            update.message.reply_text(f"ไม่พบฟิลด์ '{field}' ใน sheet")
            return

        col_index = headers.index(field) + 1
        sheet.update_cell(cell.row, col_index, value)
        update.message.reply_text(f"อัปเดต '{field}' เป็น '{value}' เรียบร้อยแล้ว")
    except Exception as e:
        update.message.reply_text("ไม่สามารถอัปเดตข้อมูลได้")
        print(e)

# ตั้งค่า bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("update", update_data))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()