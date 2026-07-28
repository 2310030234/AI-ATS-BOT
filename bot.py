import os
import re
import json
import shutil
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN
from parser import get_jd, get_resumes
from ats import analyze_resume
from qa import answer_question

JD_FOLDER = "uploads/jd"
RESUME_FOLDER = "uploads/resumes"

os.makedirs(JD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """
🤖 Welcome to HireGenie AI

Upload ONE JD PDF
Upload MULTIPLE Resume PDFs

Commands:
/start
/analyze
/reset - clear old files before a new session

You can also ask:

Who has highest CGPA?
Who knows Python?
Who has AWS?
"""
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    shutil.rmtree(JD_FOLDER, ignore_errors=True)
    shutil.rmtree(RESUME_FOLDER, ignore_errors=True)

    os.makedirs(JD_FOLDER, exist_ok=True)
    os.makedirs(RESUME_FOLDER, exist_ok=True)

    if os.path.exists("ats_results.json"):
        os.remove("ats_results.json")

    await update.message.reply_text("🗑️ Cleared all uploaded files and previous results. Ready for a new session.")


async def save_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    doc = update.message.document

    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Upload only PDF")
        return

    file = await doc.get_file()

    name = doc.file_name.lower()

    if "jd" in name or "job" in name:

        path = os.path.join(JD_FOLDER, doc.file_name)
        await file.download_to_drive(path)

        await update.message.reply_text("✅ Job Description Uploaded")

    else:

        path = os.path.join(RESUME_FOLDER, doc.file_name)
        await file.download_to_drive(path)

        await update.message.reply_text("✅ Resume Uploaded")


def extract_score(result_text):
    match = re.search(r"ATS Score:\s*(\d+)\s*%", result_text)
    if match:
        return int(match.group(1))
    return None


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("🔍 Reading PDFs...")

    jd = get_jd()

    if jd is None:
        await update.message.reply_text("❌ Upload JD first.")
        return

    resumes = get_resumes()

    if len(resumes) == 0:
        await update.message.reply_text("❌ Upload resumes first.")
        return

    results = {}

    for file_name, resume in resumes:

        await update.message.reply_text(f"📄 Analyzing {file_name}...")

        result = analyze_resume(jd, resume)

        results[file_name] = {
            "score": extract_score(result),
            "full_result": result,
        }

        await update.message.reply_text(result)

    with open("ats_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    await update.message.reply_text("✅ ATS Analysis Completed.")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message.text

    if msg.startswith("/"):
        return

    ans = answer_question(msg)

    await update.message.reply_text(ans)


def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(
        MessageHandler(
            filters.Document.PDF,
            save_pdf,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat,
        )
    )

    print("Bot Running...")

    PORT = int(os.environ.get("PORT", 8443))
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if RENDER_URL:
        # Webhook mode (used when deployed on Render)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_URL}/{BOT_TOKEN}",
        )
    else:
        # Polling mode (used when running locally)
        app.run_polling()


if __name__ == "__main__":
    main()