"""
Телеграм-бот для сбора анкет скалолазов — поездка в Роклэндс

Установка:
    pip install python-telegram-bot==20.7

Запуск:
    python climbing_survey_bot.py

Или через переменные окружения:
    BOT_TOKEN=xxx ADMIN_CHAT_ID=yyy python climbing_survey_bot.py
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ─── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN     = os.getenv("BOT_TOKEN",     "8751174713:AAH4VZhvdWO5FBvvTh7M7OATSy8I3VZKZc4")
ADMIN_CHAT_ID = 133825520  # ваш личный chat_id

# ─── Шаги ─────────────────────────────────────────────────────────────────────
(
    Q1, Q2, Q3, Q4, Q5, Q6, Q7,
    Q8, Q9, Q10, Q11, Q12, Q13, Q14,
) = range(14)

# ─── Клавиатуры ───────────────────────────────────────────────────────────────
def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

KEYBOARDS = {
    Q2:  kb([["XS", "S", "M"], ["L", "XL", "XXL"]]),
    Q3:  kb([["Меньше 1 года"], ["1–2 года"], ["3–5 лет"], ["6–10 лет"], ["Больше 10 лет"]]),
    Q4:  kb([["Нет, только зал"], ["1–2 раза выезжал(а)"], ["Несколько поездок"], ["Езжу регулярно"]]),
    Q5:  kb([["1–2 раза в месяц"], ["Раз в неделю"], ["2–3 раза в неделю"], ["Почти каждый день"]]),
    Q6:  kb([["До 5c", "6a–6b"], ["6b+–6c", "6c+–7a"], ["7a+–7b", "7b+–7c"], ["8a и выше"]]),
    Q7:  kb([["До 5c", "6a–6b"], ["6b+–6c", "6c+–7a"], ["7a+–7b", "7b+–7c"], ["8a и выше"]]),
    Q8:  kb([["Slopers", "Compression"], ["Прыжки / динамика", "Нависание"],
             ["Чтение трасс", "Психология срывов"], ["Техника ног", "Crimps"], ["Напишу сам(а) ✏️"]]),
    Q9:  kb([["Сила пальцев", "Баланс / техника ног"], ["Прыжки / динамика", "Статика"],
             ["Гибкость", "Выносливость"], ["Контактная сила", "Compression"], ["Напишу сам(а) ✏️"]]),
    Q10: kb([["Только зал, на камне не был(а)"], ["Гранит", "Известняк"],
             ["Песчаник", "Конгломерат"], ["Разный камень"], ["Напишу сам(а) ✏️"]]),
    Q11: kb([["😕 Не в форме"], ["😐 Средняя"], ["💪 Хорошая"], ["🔥 Отличная"]]),
    Q12: kb([["Пролезть проекты"], ["Попробовать новые категории"],
             ["Просто кайфануть"], ["Поддержать команду"],
             ["Отдохнуть на природе"], ["Напишу сам(а) ✏️"]]),
}

QUESTIONS = {
    Q1:  "1️⃣ Напиши своё *ФИО*:",
    Q2:  "2️⃣ *Размер футболки:*",
    Q3:  "3️⃣ *Опыт лазания* — сколько лет занимаешься?",
    Q4:  "4️⃣ *Опыт лазания на скалах* (на улице, не в зале):",
    Q5:  "5️⃣ *Как часто лазаешь?*",
    Q6:  "6️⃣ *Максимальная пройденная категория* в боулдеринге на скалах\n_(Fontainebleau)_",
    Q7:  "7️⃣ *Комфортная рабочая категория* — лезешь уверенно, без срывов:",
    Q8:  "8️⃣ *Слабые стороны* — что хочешь прокачать?\n_(или напиши своё)_",
    Q9:  "9️⃣ *Сильные стороны:*\n_(или напиши своё)_",
    Q10: "🔟 *Опыт на скалах* — на каком камне лазал(а)?\n_(или напиши своё)_",
    Q11: "1️⃣1️⃣ Как оцениваешь *текущую физическую форму?*",
    Q12: "1️⃣2️⃣ *Что хочешь получить от поездки?*\n_(или напиши своё)_",
    Q13: "1️⃣3️⃣ *Травмы и ограничения*, о которых стоит знать?\n_(напиши «нет» если всё хорошо)_",
    Q14: "1️⃣4️⃣ *Дополнительные комментарии:*\n_(напиши «нет» если нечего добавить)_",
}

KEYS = [
    "fio", "shirt", "exp_general", "exp_outdoor", "frequency",
    "max_grade", "comfort_grade", "weaknesses", "strengths",
    "rock_type", "fitness", "goals", "injuries", "comments",
]

LABELS = [
    "ФИО", "Размер футболки", "Опыт лазания", "Опыт на скалах",
    "Частота", "Максимум (боулдеринг на камне)", "Рабочая категория",
    "Слабые стороны", "Сильные стороны", "Тип камня",
    "Текущая форма", "Цели поездки", "Травмы/ограничения", "Комментарии",
]

STEP_ORDER = [Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14]


# ─── Отправить вопрос ─────────────────────────────────────────────────────────
async def ask(update: Update, step: int) -> int:
    reply_kb = KEYBOARDS.get(step, ReplyKeyboardRemove())
    await update.message.reply_text(
        QUESTIONS[step], parse_mode="Markdown", reply_markup=reply_kb
    )
    return step


# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()
    await update.message.reply_text(
        "Привет! 🧗 Это анкета для поездки в *Роклэндс*.\n"
        "14 вопросов — займёт ~2 минуты. Поехали!\n\n"
        "_/cancel — отменить в любой момент_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return await ask(update, Q1)


# ─── Итог ─────────────────────────────────────────────────────────────────────
async def finish(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    d = ctx.user_data
    lines = [f"━━━━━━━━━━━━━━━━━━━━━━━━━━━",
             f"👤 {d.get('fio', '—')}",
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for key, label in zip(KEYS, LABELS):
        lines.append(f"*{label}:* {d.get(key, '—')}")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    summary = "\n".join(lines)

    await update.message.reply_text(
        "✅ Готово! Анкета отправлена. Увидимся на камне 🤙\n\n" + summary,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    user = update.effective_user
    await ctx.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📩 *Новая анкета* от @{user.username or user.first_name}\n\n" + summary,
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ─── /cancel ──────────────────────────────────────────────────────────────────
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Анкета отменена. Напиши /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ─── Запуск ───────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    f = filters.TEXT & ~filters.COMMAND

    async def h1(u, c):  c.user_data["fio"]           = u.message.text; return await ask(u, Q2)
    async def h2(u, c):  c.user_data["shirt"]          = u.message.text; return await ask(u, Q3)
    async def h3(u, c):  c.user_data["exp_general"]    = u.message.text; return await ask(u, Q4)
    async def h4(u, c):  c.user_data["exp_outdoor"]    = u.message.text; return await ask(u, Q5)
    async def h5(u, c):  c.user_data["frequency"]      = u.message.text; return await ask(u, Q6)
    async def h6(u, c):  c.user_data["max_grade"]      = u.message.text; return await ask(u, Q7)
    async def h7(u, c):  c.user_data["comfort_grade"]  = u.message.text; return await ask(u, Q8)
    async def h8(u, c):  c.user_data["weaknesses"]     = u.message.text; return await ask(u, Q9)
    async def h9(u, c):  c.user_data["strengths"]      = u.message.text; return await ask(u, Q10)
    async def h10(u, c): c.user_data["rock_type"]      = u.message.text; return await ask(u, Q11)
    async def h11(u, c): c.user_data["fitness"]        = u.message.text; return await ask(u, Q12)
    async def h12(u, c): c.user_data["goals"]          = u.message.text; return await ask(u, Q13)
    async def h13(u, c): c.user_data["injuries"]       = u.message.text; return await ask(u, Q14)
    async def h14(u, c): c.user_data["comments"]       = u.message.text; return await finish(u, c)

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
            Q13: [MessageHandler(f, h13)],
            Q14: [MessageHandler(f, h14)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("✅ Бот запущен. Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
