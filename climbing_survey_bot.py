"""
Телеграм-бот для сбора анкет скалолазов — поездка в Роклэндс
Установка: pip install python-telegram-bot==20.7
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN     = os.getenv("BOT_TOKEN",     "ВСТАВЬТЕ_ТОКЕН_СЮДА")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "133825520"))

(
    Q1, Q2, Q3, Q4, Q5, Q6, Q7,
    Q8, Q9, Q10, Q11, Q12, Q13,
) = range(13)

def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

KEYBOARDS = {
    Q2:  kb([["XS", "S", "M"], ["L", "XL", "XXL"]]),
    Q3:  kb([["Меньше 1 года"], ["1–2 года"], ["3–5 лет"], ["6–10 лет"], ["Больше 10 лет"]]),
    Q4:  kb([["Нет опыта"], ["Был пару раз"],
             ["Небольшой опыт (до 10 поездок)"], ["Регулярно выезжаю в сезон"]]),
    Q5:  kb([["1–2 раза в месяц"], ["Раз в неделю"], ["2–3 раза в неделю"], ["Почти каждый день"]]),
    Q6:  kb([["До 5c", "6a–6b"], ["6b+–6c", "6c+–7a"], ["7a+–7b", "7b+–7c"], ["8a и выше"]]),
    Q7:  kb([["До 5c", "6a–6b"], ["6b+–6c", "6c+–7a"], ["7a+–7b", "7b+–7c"], ["8a и выше"]]),
    Q9:  kb([["😕 Не в форме"], ["😐 Средняя"], ["💪 Хорошая"], ["🔥 Отличная"]]),
}

QUESTIONS = {
    Q1:  "1️⃣ Напиши своё *ФИО*:",
    Q2:  "2️⃣ *Размер футболки:*",
    Q3:  "3️⃣ *Опыт лазания* — сколько лет занимаешься?",
    Q4:  "4️⃣ *Опыт лазания на скалах:*",
    Q5:  "5️⃣ *Как часто лазаешь?*",
    Q6:  "6️⃣ *Максимальная пройденная категория* в боулдеринге на скалах:",
    Q7:  "7️⃣ *Комфортная рабочая категория*\n_(стабильно лазаешь и есть от 5 пролазов данной категории)_",
    Q8:  "8️⃣ *Слабые стороны* — напиши через запятую:\n\n"
         "Варианты: активники, пассивы, прыжки/динамика, лежачка, нависание, постановка ног на скалах, чтение трасс",
    Q9:  "9️⃣ Как оцениваешь *текущую физическую форму?*",
    Q10: "🔟 *Сильные стороны* — напиши через запятую:\n\n"
         "Варианты: сильные пальцы, прыжки/динамика, выносливость, гибкость, баланс/постановка ног",
    Q11: "1️⃣1️⃣ *Что хочешь получить от поездки?* — напиши через запятую:\n\n"
         "Варианты: открыть новую категорию, максимум наслаждения без особых ожиданий, "
         "пролезть как можно больше трасс своего уровня, изучить новую страну, всё и сразу",
    Q12: "1️⃣2️⃣ *Травмы и ограничения*, о которых стоит знать?\n_(напиши «нет» если всё хорошо)_",
    Q13: "1️⃣3️⃣ *Дополнительные комментарии:*\n_(напиши «нет» если нечего добавить)_",
}

KEYS   = ["fio","shirt","exp_general","exp_outdoor","frequency","max_grade",
          "comfort_grade","weaknesses","fitness","strengths","goals","injuries","comments"]
LABELS = ["ФИО","Размер футболки","Опыт лазания","Опыт на скалах","Частота",
          "Максимум (боулдеринг)","Рабочая категория","Слабые стороны","Текущая форма",
          "Сильные стороны","Цели поездки","Травмы/ограничения","Комментарии"]

async def ask(update, step):
    reply_kb = KEYBOARDS.get(step, ReplyKeyboardRemove())
    await update.message.reply_text(QUESTIONS[step], parse_mode="Markdown", reply_markup=reply_kb)
    return step

async def start(update, ctx):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Привет! 🧗 Это анкета для поездки в *Роклэндс*.\n"
        "13 вопросов — займёт ~2 минуты. Поехали!\n\n_/cancel — отменить_",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return await ask(update, Q1)

async def finish(update, ctx):
    ctx.user_data["comments"] = update.message.text
    d = ctx.user_data
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━",
             f"👤 {d.get('fio','—')}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for key, label in zip(KEYS, LABELS):
        lines.append(f"*{label}:* {d.get(key, '—')}")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    summary = "\n".join(lines)
    await update.message.reply_text(
        "✅ Готово! Анкета отправлена. Увидимся на камне 🤙",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    user = update.effective_user
    await ctx.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📩 *Новая анкета* от @{user.username or user.first_name}\n\n" + summary,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update, ctx):
    await update.message.reply_text("Анкета отменена. /start — начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def h1(u, c):  c.user_data["fio"]          = u.message.text; return await ask(u, Q2)
async def h2(u, c):  c.user_data["shirt"]         = u.message.text; return await ask(u, Q3)
async def h3(u, c):  c.user_data["exp_general"]   = u.message.text; return await ask(u, Q4)
async def h4(u, c):  c.user_data["exp_outdoor"]   = u.message.text; return await ask(u, Q5)
async def h5(u, c):  c.user_data["frequency"]     = u.message.text; return await ask(u, Q6)
async def h6(u, c):  c.user_data["max_grade"]     = u.message.text; return await ask(u, Q7)
async def h7(u, c):  c.user_data["comfort_grade"] = u.message.text; return await ask(u, Q8)
async def h8(u, c):  c.user_data["weaknesses"]    = u.message.text; return await ask(u, Q9)
async def h9(u, c):  c.user_data["fitness"]       = u.message.text; return await ask(u, Q10)
async def h10(u, c): c.user_data["strengths"]     = u.message.text; return await ask(u, Q11)
async def h11(u, c): c.user_data["goals"]         = u.message.text; return await ask(u, Q12)
async def h12(u, c): c.user_data["injuries"]      = u.message.text; return await ask(u, Q13)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    f = filters.TEXT & ~filters.COMMAND

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            Q1:  [MessageHandler(f, h1)],
            Q2:  [MessageHandler(f, h2)],
            Q3:  [MessageHandler(f, h3)],
            Q4:  [MessageHandler(f, h4)],
            Q5:  [MessageHandler(f, h5)],
            Q6:  [MessageHandler(f, h6)],
            Q7:  [MessageHandler(f, h7)],
            Q8:  [MessageHandler(f, h8)],
            Q9:  [MessageHandler(f, h9)],
            Q10: [MessageHandler(f, h10)],
            Q11: [MessageHandler(f, h11)],
            Q12: [MessageHandler(f, h12)],
            Q13: [MessageHandler(f, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("✅ Бот запущен. Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
