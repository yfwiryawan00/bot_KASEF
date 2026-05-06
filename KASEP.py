import gspread
import os
import json
import asyncio

from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================================
# KONFIGURASI
# =========================================

TOKEN = os.getenv("TELEGRAM_TOKEN")

WEBHOOK_URL = "https://bot-kasef.onrender.com/webhook"

SPREADSHEET_ID = "1u2NTeyID8YfiMjzttRfLWnx4kGtoDyw-3YFSO9t1O_M"

# =========================================
# FLASK APP
# =========================================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "KASEF Bot is running!"

# =========================================
# CONNECT GOOGLE SHEET
# =========================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

google_creds = json.loads(
    os.getenv("GOOGLE_CREDENTIALS")
)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_creds,
    scope
)

client = gspread.authorize(creds)

spreadsheet = client.open_by_key(SPREADSHEET_ID)

sheet = spreadsheet.sheet1

# =========================================
# TELEGRAM APPLICATION
# =========================================

app = Application.builder().token(TOKEN).build()

# =========================================
# COMMAND START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim kode SF untuk melihat data sales.\n\nContoh:\nSPMKN89"
    )

# =========================================
# SEARCH SF
# =========================================

async def cari_sf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kode_input = update.message.text.strip().upper()

    data = sheet.get_all_values()

    ditemukan = False

    for row in data[1:]:

        if len(row) >= 29:

            kode_sheet = row[1].strip().upper()

            if kode_sheet == kode_input:

                # =========================
                # IDENTITAS SF
                # =========================

                nama_sf = row[0]
                kode_sf = row[1]
                cluster = row[11]
                status = row[13]

                # =========================
                # TARGET
                # =========================

                target_ps = row[20]
                target_sales_fee = row[21]

                # =========================
                # SALES PERFORMANCE
                # =========================

                total_ps_mtd = row[15]
                total_ps_m1 = row[14]
                mom_ps = row[16]

                total_sf_mtd = row[18]
                total_sf_m1 = row[17]
                mom_sales_fee = row[19]

                gap_ps = row[22]
                gap_sales_fee = row[23]

                # =========================
                # DJP PERFORMANCE
                # =========================

                odp_assign = row[24]
                odp_visit = row[25]
                ach_visit = row[26]
                daily_visit = row[27]

                # =========================
                # UPDATE DATE
                # =========================

                update_data = row[28]

                pesan = f"""
📊 <b>UPDATE DATA SALES</b>
🗓 <b>{update_data}</b>

━━━━━━━━━━━━━━━
👤 <b>SF INFORMATION</b>
━━━━━━━━━━━━━━━

Kode SF : <code>{kode_sf}</code>
Nama SF : {nama_sf}
Cluster : {cluster}
Status : {status}

Target Min. PS : {target_ps}
Target Min. Sales Fee : {target_sales_fee}

━━━━━━━━━━━━━━━
📈 <b>SALES PERFORMANCE</b>
━━━━━━━━━━━━━━━

Total PS Mtd : {total_ps_mtd}
Total PS M-1 : {total_ps_m1}
MoM PS : {mom_ps}

Total Sales Fee Mtd : {total_sf_mtd}
Total Sales Fee M-1 : {total_sf_m1}
MoM Sales Fee : {mom_sales_fee}

Gap PS : {gap_ps}
Gap Sales Fee : {gap_sales_fee}

━━━━━━━━━━━━━━━
🚪 <b>DJP PERFORMANCE</b>
━━━━━━━━━━━━━━━

ODP Assign : {odp_assign}
ODP Visit : {odp_visit}
Ach Visit : {ach_visit}
ODP Daily Visit : {daily_visit}
"""

                await update.message.reply_text(
                    pesan,
                    parse_mode="HTML"
                )

                ditemukan = True
                break

    if not ditemukan:
        await update.message.reply_text(
            f"Kode SF '{kode_input}' tidak ditemukan."
        )

# =========================================
# HANDLER
# =========================================

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        cari_sf
    )
)

# =========================================
# WEBHOOK
# =========================================

@flask_app.post("/webhook")
async def webhook():

    update = Update.de_json(
        request.get_json(force=True),
        app.bot
    )

    await app.process_update(update)

    return "OK"

# =========================================
# MAIN
# =========================================

if __name__ == "__main__":

    async def setup():
        await app.initialize()
        await app.bot.set_webhook(WEBHOOK_URL)

    asyncio.run(setup())

    print("Webhook bot berjalan...")

    port = int(os.environ.get("PORT", 10000))

    flask_app.run(
        host="0.0.0.0",
        port=port
    )
