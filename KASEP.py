import threading
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from flask import Flask

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Telegram Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))

    flask_app.run(
        host="0.0.0.0",
        port=port
    )

# =========================================
# KONFIGURASI
# =========================================

TOKEN = os.getenv("TELEGRAM_TOKEN")

SPREADSHEET_ID = "1u2NTeyID8YfiMjzttRfLWnx4kGtoDyw-3YFSO9t1O_M"

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

    kode_sf = update.message.text.strip().upper()

    data = sheet.get_all_values()

    ditemukan = False

    # Skip header
    for row in data[1:]:

        # Pastikan kolom sampai AC tersedia
        if len(row) >= 29:

            kode_sheet = row[1].strip().upper()   # Kolom B

            if kode_sheet == kode_sf:

                # =========================
                # IDENTITAS SF
                # =========================

                nama_sf = row[0]      # A
                kode_sf = row[1]      # B
                cluster = row[11]     # L
                status = row[13]      # N

                # =========================
                # TARGET
                # =========================

                target_ps = row[20]           # U
                target_sales_fee = row[21]    # V

                # =========================
                # SALES PERFORMANCE
                # =========================

                total_ps_mtd = row[15]        # P
                total_ps_m1 = row[14]         # O
                mom_ps = row[16]              # Q

                total_sf_mtd = row[18]        # S
                total_sf_m1 = row[17]         # R
                mom_sales_fee = row[19]       # T

                gap_ps = row[22]              # W
                gap_sales_fee = row[23]       # X

                # =========================
                # DJP PERFORMANCE
                # =========================

                odp_assign = row[24]          # Y
                odp_visit = row[25]           # Z
                ach_visit = row[26]           # AA
                daily_visit = row[27]         # AB

                # =========================
                # UPDATE DATE
                # =========================

                update_data = row[28]         # AC

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

                await update.message.reply_text(pesan,parse_mode="HTML")

                ditemukan = True
                break

    if not ditemukan:
        await update.message.reply_text(
            f"Kode SF '{kode_sf}' tidak ditemukan."
        )

# =========================================
# MAIN
# =========================================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, cari_sf)
)

print("Bot berjalan...")

# Jalankan web server di thread terpisah
threading.Thread(target=run_web).start()

# Jalankan telegram bot
app.run_polling()
