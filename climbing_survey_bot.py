"""
Телеграм-бот для сбора анкет скалолазов — поездка в Роклэндс
Установка: pip install python-telegram-bot==20.7
"""

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, filters, ContextTypes,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN     = os.getenv("BOT_TOKEN",     "ВСТАВЬТЕ_ТОКЕН_СЮДА")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "133825520"))

(
    Q1, Q2, Q3, Q4, Q5, Q6, Q7,
    Q8, Q8_CUSTOM,
    Q9, Q9_CUSTOM,
    Q10, Q11,
    Q12, Q12_CUSTOM,
    Q13, Q14,
) = range(17)

def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

# Варианты для множественного выбора
WEAKNESSES_OPTIONS = [
    "Активники", "Пассивы", "Прыжки / динамика",
    "Лежачка", "Нависание", "Постановка ног на скалах",
    "Чтение трасс", "Свой вариант ✏️"
]
STRENGTHS_OPTIONS = [
    "Сильные пальцы", "Прыжки / динамика", "Выносливость",
    "Гибкость", "Баланс / постановка ног", "Свой вариант ✏️"
]
GOALS_OPTIONS = [
    "Открыть новую категорию",
    "Максимум наслаждения без особых ожиданий",
    "Пролезть как можно больше трасс своего уровня",
    "Изучить новую страну",
    "Всё и сразу",
    "Свой вариант ✏️"
]

def make_inline_kb(options, selected, prefix):
    buttons = []
    for opt in options:
        check = "✅ " if opt in selected else "☐ "
        buttons.append([InlineKeyboardButton(check + opt, callback_data=f"{prefix}:{opt}")])
    buttons.append([InlineKeyboardButton("✓ Готово", callback_data=f"{prefix}:__done__")])
    return InlineKeyboardMarkup(buttons)

KEYBOARDS = {
    Q2:  kb([["XS", "S", "M"], ["L", "XL", "XXL"]]),
    Q3:  kb([["Меньше 1 года"], ["1–2 года"], ["3–5 лет"], ["6–10 лет"], ["Больше 10 лет"]]),
    Q4:  kb([["Нет опыта"], ["Был пару раз"],
             ["Небольшой опыт (до 10 поездок)"], ["Регулярно выезжаю в сезон"]]),
    Q5:  kb([["1–2 раза в месяц"], ["Раз в неделю"], ["2–3 раза в неделю"], ["Почти каждый день"]]),
    Q6:  kb([["До 5c", "6a–6b"], ["6b+–6c", "6c+–7a"], ["7a+–7b", "7b+–7c"], ["8a и выше"]]),
    Q7:  kb([["До 5c", "6a–6b"], ["6b+–6c", "6c+–7a"], ["7a+–7b", "7b+–7c"], ["8a и выше"]]),
    Q10: kb([["Только зал, на камне не был(а)"], ["Гранит", "Известняк"],
             ["Песчаник", "Конгломерат"], ["Разный камень"]]),
    Q11: kb([["😕 Не в форме"], ["😐 Средняя"], ["💪 Хорошая"], ["🔥 Отличная"]]),
}

QUESTIONS = {
    Q1:  "1️⃣ Напиши своё *ФИО*:",
    Q2:  "2️⃣ *Размер футболки:*",
    Q3:  "3️⃣ *Опыт лазания* — сколько лет занимаешься?",
    Q4:  "4️⃣ *Опыт лазания на скалах:*",
    Q5:  "5️⃣ *Как часто лазаешь?*",
    Q6:  "6️⃣ *Максимальная пройденная категория* в боулдеринге на скалах:",
    Q7:  "7️⃣ *Комфортная рабочая категория*\n_(стабильно лазаешь и есть от 5 пролазов данной категории)_",
    Q8:  "8️⃣ *Слабые стороны* — выбери всё подходящее:",
    Q8_CUSTOM: "8️⃣ Напиши свои слабые стороны (через запятую):",
    Q9:  "9️⃣ *Сильные стороны* — выбери всё подходящее:",
    Q9_CUSTOM: "9️⃣ Напиши свои сильные стороны (через запятую):",
    Q10: "🔟 *Опыт на скалах* — на каком камне лазал(а)?",
    Q11: "1️⃣1️⃣ Как оцениваешь *текущую физическую форму?*",
    Q12: "1️⃣2️⃣ *Что хочешь получить от поездки?* — выбери всё подходящее:",
    Q12_CUSTOM: "1️⃣2️⃣ Напиши свой вариант:",
    Q13: "1️⃣3️⃣ *Травмы и ограничения*, о которых стоит знать?\n_(напиши «нет» если всё хорошо)_",
    Q14: "1️⃣4️⃣ *Дополнительные комментарии:*\n_(напиши «нет» если нечего добавить)_",
}

KEYS   = ["fio","shirt","exp_general","exp_outdoor","frequency","max_grade","comfort_grade",
          "weaknesses","strengths","rock_type","fitness","goals","injuries","comments"]
LABELS = ["ФИО","Размер футболки","Опыт лазания","Опыт на скалах","Частота",
          "Максимум (боулдеринг)","Рабочая категория","Слабые стороны","Сильные стороны",
          "Тип камня","Текущая форма","Цели поездки","Травмы/ограничения","Комментарии"]

async def ask(update, step):
    reply_kb = KEYBOARDS.get(step, ReplyKeyboardRemove())
    await update.message.reply_text(QUESTIONS[step], parse_mode="Markdown", reply_markup=reply_kb)
    return step

async def ask_multi(update, step, options, prefix, ctx_key, ctx):
    selected = ctx.user_data.get(ctx_key, [])
    await update.message.reply_text(
        QUESTIONS[step], parse_mode="Markdown",
        reply_markup=make_inline_kb(options, selected, prefix)
    )
    return step

async def start(update, ctx):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Привет! 🧗 Это анкета для поездки в *Роклэндс*.\n"
        "14 вопросов — займёт ~2 минуты. Поехали!\n\n_/cancel — отменить_",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return await ask(update, Q1)

async def finish(update, ctx):
    ctx.user_data["comments"] = update.message.text
    d = ctx.user_data
    lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━",
             f"👤 {d.get('fio','—')}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for key, label in zip(KEYS, LABELS):
        val = d.get(key, '—')
        if isinstance(val, list):
            val = ", ".join(val) if val else "—"
        lines.append(f"*{label}:* {val}")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    summary = "\n".join(lines)
    await update.message.reply_text(
        "✅ Готово! Анкета отправлена. Увидимся на камне 🤙\n\n" + summary,
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

# ─── Обычные хендлеры ─────────────────────────────────────────────────────────
async def h1(u, c):  c.user_data["fio"]          = u.message.text; return await ask(u, Q2)
async def h2(u, c):  c.user_data["shirt"]         = u.message.text; return await ask(u, Q3)
async def h3(u, c):  c.user_data["exp_general"]   = u.message.text; return await ask(u, Q4)
async def h4(u, c):  c.user_data["exp_outdoor"]   = u.message.text; return await ask(u, Q5)
async def h5(u, c):  c.user_data["frequency"]     = u.message.text; return await ask(u, Q6)
async def h6(u, c):  c.user_data["max_grade"]     = u.message.text; return await ask(u, Q7)
async def h7(u, c):
    c.user_data["comfort_grade"] = u.message.text
    c.user_data["weaknesses"] = []
    return await ask_multi(u, Q8, WEAKNESSES_OPTIONS, "weak", "weaknesses", c)

async def h8_custom(u, c):
    c.user_data["weaknesses"].append(u.message.text)
    c.user_data["strengths"] = []
    return await ask_multi(u, Q9, STRENGTHS_OPTIONS, "str", "strengths", c)

async def h9_custom(u, c):
    c.user_data["strengths"].append(u.message.text)
    return await ask(u, Q10)

async def h10(u, c): c.user_data["rock_type"] = u.message.text; return await ask(u, Q11)
async def h11(u, c):
    c.user_data["fitness"] = u.message.text
    c.user_data["goals"] = []
    return await ask_multi(u, Q12, GOALS_OPTIONS, "goal", "goals", c)

async def h12_custom(u, c):
    c.user_data["goals"].append(u.message.text)
    return await ask(u, Q13)

async def h13(u, c): c.user_data["injuries"] = u.message.text; return await ask(u, Q14)

# ─── Инлайн callback ──────────────────────────────────────────────────────────
async def inline_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    prefix, value = data.split(":", 1)

    if prefix == "weak":
        key, options, next_step, custom_step = "weaknesses", WEAKNESSES_OPTIONS, Q9, Q8_CUSTOM
    elif prefix == "str":
        key, options, next_step, custom_step = "strengths", STRENGTHS_OPTIONS, Q10, Q9_CUSTOM
    elif prefix == "goal":
        key, options, next_step, custom_step = "goals", GOALS_OPTIONS, Q13, Q12_CUSTOM
    else:
        return

    selected = ctx.user_data.get(key, [])

    if value == "__done__":
        if not selected:
            await query.answer("Выбери хотя бы один вариант!", show_alert=True)
            return
        # Если среди выбранных есть "Свой вариант" — сначала спросим текст
        if "Свой вариант ✏️" in selected:
            selected.remove("Свой вариант ✏️")
            ctx.user_data[key] = selected
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(
                QUESTIONS[custom_step], parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            return custom_step
        # Иначе идём дальше
        await query.edit_message_reply_markup(reply_markup=None)
        if next_step in (Q9, Q10, Q13):
            ctx.user_data["strengths" if next_step == Q10 else ("goals" if next_step == Q13 else key)] = selected if next_step != Q9 else ctx.user_data.get("strengths", [])
            if next_step == Q9:
                ctx.user_data["strengths"] = []
                await query.message.reply_text(
                    QUESTIONS[Q9], parse_mode="Markdown",
                    reply_markup=make_inline_kb(STRENGTHS_OPTIONS, [], "str")
                )
                return Q9
            elif next_step == Q13:
                await query.message.reply_text(
                    QUESTIONS[Q13], parse_mode="Markdown",
                    reply_markup=ReplyKeyboardRemove()
                )
                return Q13
            else:
                await query.message.reply_text(
                    QUESTIONS[Q10], parse_mode="Markdown",
                    reply_markup=KEYBOARDS[Q10]
                )
                return Q10
        return next_step

    # Тогл выбора
    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)
    ctx.user_data[key] = selected
    await query.edit_message_reply_markup(
        reply_markup=make_inline_kb(options, selected, prefix)
    )
    return prefix == "weak" and Q8 or (prefix == "str" and Q9 or Q12)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    f = filters.TEXT & ~filters.COMMAND

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            Q1:        [MessageHandler(f, h1)],
            Q2:        [MessageHandler(f, h2)],
            Q3:        [MessageHandler(f, h3)],
            Q4:        [MessageHandler(f, h4)],
            Q5:        [MessageHandler(f, h5)],
            Q6:        [MessageHandler(f, h6)],
            Q7:        [MessageHandler(f, h7)],
            Q8:        [CallbackQueryHandler(inline_handler, pattern="^weak:")],
            Q8_CUSTOM: [MessageHandler(f, h8_custom)],
            Q9:        [CallbackQueryHandler(inline_handler, pattern="^str:")],
            Q9_CUSTOM: [MessageHandler(f, h9_custom)],
            Q10:       [MessageHandler(f, h10)],
            Q11:       [MessageHandler(f, h11)],
            Q12:       [CallbackQueryHandler(inline_handler, pattern="^goal:")],
            Q12_CUSTOM:[MessageHandler(f, h12_custom)],
            Q13:       [MessageHandler(f, h13)],
            Q14:       [MessageHandler(f, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("✅ Бот запущен. Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
