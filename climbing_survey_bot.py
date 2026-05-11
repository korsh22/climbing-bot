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

Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,Q9,Q10,Q11,Q12,Q13 = range(13)

def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

VALID = {
    Q2: ["XS","S","M","L","XL","XXL"],
    Q3: ["Меньше 1 года","1–2 года","3–5 лет","6–10 лет","Больше 10 лет"],
    Q4: ["Нет опыта","Был(а) пару раз","Небольшой опыт — до 10 поездок","Регулярно выезжаю в сезон"],
    Q5: ["1–2 раза в месяц","Раз в неделю","2–3 раза в неделю","Почти каждый день"],
    Q6: ["До 5c","6a–6b","6b+–6c","6c+–7a","7a+–7b","7b+–7c","8a и выше"],
    Q7: ["До 5c","6a–6b","6b+–6c","6c+–7a","7a+–7b","7b+–7c","8a и выше"],
    Q9: ["😕 Не в форме","😐 Средняя","💪 Хорошая","🔥 Отличная"],
}

KEYBOARDS = {
    Q2: kb([["XS","S","M"],["L","XL","XXL"]]),
    Q3: kb([["Меньше 1 года"],["1–2 года"],["3–5 лет"],["6–10 лет"],["Больше 10 лет"]]),
    Q4: kb([["Нет опыта"],["Был(а) пару раз"],["Небольшой опыт — до 10 поездок"],["Регулярно выезжаю в сезон"]]),
    Q5: kb([["1–2 раза в месяц"],["Раз в неделю"],["2–3 раза в неделю"],["Почти каждый день"]]),
    Q6: kb([["До 5c","6a–6b"],["6b+–6c","6c+–7a"],["7a+–7b","7b+–7c"],["8a и выше"]]),
    Q7: kb([["До 5c","6a–6b"],["6b+–6c","6c+–7a"],["7a+–7b","7b+–7c"],["8a и выше"]]),
    Q9: kb([["😕 Не в форме"],["😐 Средняя"],["💪 Хорошая"],["🔥 Отличная"]]),
}

QUESTIONS = {
    Q1:  "1️⃣ Напиши своё *ФИО*:",
    Q2:  "2️⃣ *Размер футболки:*",
    Q3:  "3️⃣ *Опыт лазания* — сколько лет занимаешься?",
    Q4:  "4️⃣ *Опыт лазания на скалах:*",
    Q5:  "5️⃣ *Как часто лазаешь?*",
    Q6:  "6️⃣ *Максимальная пройденная категория* в боулдеринге на скалах:",
    Q7:  "7️⃣ *Комфортная рабочая категория*\n_(стабильно лазаешь и есть от 5 пролазов данной категории)_",
    Q8:  "8️⃣ *Слабые стороны* — напиши через запятую:\n\nВарианты: активники, пассивы, прыжки/динамика, лежачка, нависание, постановка ног на скалах, чтение трасс, свой вариант",
    Q9:  "9️⃣ Как оцениваешь *текущую физическую форму?*",
    Q10: "🔟 *Сильные стороны* — напиши через запятую:\n\nВарианты: сильные пальцы, прыжки/динамика, выносливость, гибкость, баланс/постановка ног, свой вариант",
    Q11: "1️⃣1️⃣ *Что хочешь получить от поездки?* — напиши через запятую:\n\nВарианты: открыть новую категорию, максимум наслаждения без особых ожиданий, пролезть как можно больше трасс своего уровня, изучить новую страну, всё и сразу, свой вариант",
    Q12: "1️⃣2️⃣ *Травмы и ограничения*, о которых стоит знать?\n_(напиши «нет» если всё хорошо)_",
    Q13: "1️⃣3️⃣ *Дополнительные комментарии:*\n_(напиши «нет» если нечего добавить)_",
}

KEYS   = ["fio","shirt","exp_general","exp_outdoor","frequency","max_grade","comfort_grade","weaknesses","fitness","strengths","goals","injuries","comments"]
LABELS = ["ФИО","Размер футболки","Опыт лазания","Опыт на скалах","Частота","Максимум (боулдеринг)","Рабочая категория","Слабые стороны","Текущая форма","Сильные стороны","Цели поездки","Травмы/ограничения","Комментарии"]

async def ask(update, step):
    reply_kb = KEYBOARDS.get(step, ReplyKeyboardRemove())
    await update.message.reply_text(QUESTIONS[step], parse_mode="Markdown", reply_markup=reply_kb)
    return step

async def validate(update, step, ctx_key, next_step, ctx):
    text = update.message.text
    if text not in VALID[step]:
        await update.message.reply_text("Пожалуйста, выбери вариант из кнопок 👇", reply_markup=KEYBOARDS[step])
        return step
    ctx.user_data[ctx_key] = text
    return await ask(update, next_step)

async def start(update, ctx):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Привет! 🧗 Это анкета для поездки в *Роклэндс*.\n13 вопросов — займёт ~2 минуты. Поехали!\n\n_/cancel — отменить_",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return await ask(update, Q1)

async def finish(update, ctx):
    ctx.user_data["comments"] = update.message.text
    d = ctx.user_data
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━", f"👤 {d.get('fio','—')}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for key, label in zip(KEYS, LABELS):
        lines.append(f"{label}: {d.get(key, chr(8212))}")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    summary = "\n".join(lines)
    await update.message.reply_text("✅ Готово! Анкета отправлена. Увидимся в Rocklands 🤙", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    user = update.effective_user
    try:
        await ctx.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📩 Новая анкета от @{user.username or user.first_name}\n\n" + summary)
    except Exception as e:
        logging.error(f"Failed to send to admin: {e}")
    return ConversationHandler.END

async def cancel(update, ctx):
    await update.message.reply_text("Анкета отменена. Напиши /start чтобы начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def h1(u,c):  c.user_data["fio"]=u.message.text; return await ask(u,Q2)
async def h2(u,c):  return await validate(u,Q2,"shirt",Q3,c)
async def h3(u,c):  return await validate(u,Q3,"exp_general",Q4,c)
async def h4(u,c):  return await validate(u,Q4,"exp_outdoor",Q5,c)
async def h5(u,c):  return await validate(u,Q5,"frequency",Q6,c)
async def h6(u,c):  return await validate(u,Q6,"max_grade",Q7,c)
async def h7(u,c):  return await validate(u,Q7,"comfort_grade",Q8,c)
async def h8(u,c):  c.user_data["weaknesses"]=u.message.text; return await ask(u,Q9)
async def h9(u,c):  return await validate(u,Q9,"fitness",Q10,c)
async def h10(u,c): c.user_data["strengths"]=u.message.text; return await ask(u,Q11)
async def h11(u,c): c.user_data["goals"]=u.message.text; return await ask(u,Q12)
async def h12(u,c): c.user_data["injuries"]=u.message.text; return await ask(u,Q13)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    f = filters.TEXT & ~filters.COMMAND
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        allow_reentry=True,
        states={
            Q1:[MessageHandler(f,h1)], Q2:[MessageHandler(f,h2)],
            Q3:[MessageHandler(f,h3)], Q4:[MessageHandler(f,h4)],
            Q5:[MessageHandler(f,h5)], Q6:[MessageHandler(f,h6)],
            Q7:[MessageHandler(f,h7)], Q8:[MessageHandler(f,h8)],
            Q9:[MessageHandler(f,h9)], Q10:[MessageHandler(f,h10)],
            Q11:[MessageHandler(f,h11)], Q12:[MessageHandler(f,h12)],
            Q13:[MessageHandler(f,finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    print("✅ Бот запущен. Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
