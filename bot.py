import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

BOT_TOKEN = os.getenv("BOT_TOKEN", "9107550593:AAFaoFd3-mH5cmaAJqR-ykQ-04WxJ_FLNsQ")

# Усі 20 секцій із таблиці DISC self-assessment.xlsx (аркуш DISC self-assessment PFC)
SECTIONS = [
    {"section": 1, "options": [("Компанійський", "I"), ("Сентиментальний", "S"), ("Стриманий", "C"), ("Конкуруючий", "D")]},
    {"section": 2, "options": [("Сміливий", "D"), ("Захоплений", "I"), ("Обачний", "S"), ("Методичний", "C")]},
    {"section": 3, "options": [("Замкнутий", "C"), ("Активний", "D"), ("Ентузіаст", "I"), ("Дружелюбний", "S")]},
    {"section": 4, "options": [("Той, що вагається", "S"), ("Песиміст", "C"), ("Реаліст", "D"), ("Оптиміст", "I")]},
    {"section": 5, "options": [("Захоплений", "I"), ("Дружелюбний", "S"), ("Пунктуальний", "C"), ("Переконливий", "D")]},
    {"section": 6, "options": [("Ініціативний", "D"), ("Імпульсивний", "I"), ("Нерішучий", "S"), ("Детальний", "C")]},
    {"section": 7, "options": [("Послідовний", "C"), ("Завзятий", "D"), ("Творчий", "I"), ("Традиційний", "S")]},
    {"section": 8, "options": [("Категоричний", "D"), ("Демонстративний", "I"), ("Толерантний", "S"), ("Детальний", "C")]},
    {"section": 9, "options": [("Критичний", "C"), ("Впевнений", "D"), ("Творчий", "I"), ("Той, що пристосовується", "S")]},
    {"section": 10, "options": [("Душевний", "S"), ("Допитливий", "C"), ("Наполегливий", "D"), ("Мотивуючий", "I")]},
    {"section": 11, "options": [("Виразний", "I"), ("Чутливий", "S"), ("Уважний", "C"), ("Радикальний", "D")]},
    {"section": 12, "options": [("Діяльний", "D"), ("Мрійливий", "I"), ("Стабільний", "S"), ("Добросовісний", "C")]},
    {"section": 13, "options": [("Той, що оцінює", "C"), ("Цілеспрямований", "D"), ("Ентузіаст", "I"), ("Спокійний", "S")]},
    {"section": 14, "options": [("Вразливий", "S"), ("Розважливий", "C"), ("Рішучий", "D"), ("Демонстративний", "I")]},
    {"section": 15, "options": [("Дипломатичний", "C"), ("Прямий", "D"), ("Балакучий", "I"), ("Турботливий", "S")]},
    {"section": 16, "options": [("Співчутливий", "S"), ("Той, що оцінює", "C"), ("Переконливий", "D"), ("Підприємливий", "I")]},
    {"section": 17, "options": [("Мінливий", "I"), ("Терплячий", "S"), ("Акуратний", "C"), ("Наполегливий", "D")]},
    {"section": 18, "options": [("Автономний", "D"), ("Комунікабельний", "I"), ("Відданий", "S"), ("Обачний", "C")]},
    {"section": 19, "options": [("Акуратний", "C"), ("Контролюючий", "D"), ("Надихаючий", "I"), ("Поблажливий", "S")]},
    {"section": 20, "options": [("Обережний", "S"), ("Компетентний", "C"), ("Енергійний", "D"), ("Креативний", "I")]},
]

DESCRIPTIONS = {
    "D": "Dominance (Домінування) — орієнтація на результат, рішучість, швидке прийняття рішень і готовність брати відповідальність.",
    "I": "Influence (Вплив) — відкритість, комунікабельність, оптимізм, вміння надихати та домовлятися з людьми.",
    "S": "Steadiness (Стабільність) — надійність, терплячість, підтримка команди, послідовність і комфорт у стабільному середовищі.",
    "C": "Compliance (Відповідність / Аналітичність) — увага до деталей, логіка, якість, порядок і дотримання стандартів.",
}

# Стан проходження тесту в пам'яті: {user_id: {"step": int, "scores": {"D": 0, "I": 0, "S": 0, "C": 0}}}
user_sessions: dict[int, dict] = {}


def build_section_keyboard(step_idx: int) -> InlineKeyboardMarkup:
    options = SECTIONS[step_idx]["options"]
    buttons = [
        [InlineKeyboardButton(text=word, callback_data=f"ans:{step_idx}:{opt_idx}")]
        for opt_idx, (word, _) in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_result(scores: dict[str, int]) -> str:
    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_letter, top_score = sorted_types[0]
    second_letter, second_score = sorted_types[1]

    # Якщо друга шкала теж помітно виражена (наприклад, різниця <= 2 бали), показуємо поєднання двох літер
    if second_score > 0 and (top_score - second_score) <= 2:
        profile_code = f"{top_letter}/{second_letter}"
        profile_summary = (
            f"Провідний профіль: **{profile_code}**\n\n"
            f"• **{top_letter}**: {DESCRIPTIONS[top_letter]}\n"
            f"• **{second_letter}**: {DESCRIPTIONS[second_letter]}"
        )
    else:
        profile_code = top_letter
        profile_summary = (
            f"Провідний профіль: **{profile_code}**\n\n"
            f"{DESCRIPTIONS[top_letter]}"
        )

    return (
        "Тест **DISC** завершено! Ось твій результат:\n\n"
        f"• **D** (Домінування): {scores['D']}\n"
        f"• **I** (Вплив): {scores['I']}\n"
        f"• **S** (Стабільність): {scores['S']}\n"
        f"• **C** (Відповідність): {scores['C']}\n\n"
        f"{profile_summary}"
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {
        "step": 0,
        "scores": {"D": 0, "I": 0, "S": 0, "C": 0},
    }
    await message.answer(
        "Привіт! Це тест **DISC** (20 секцій).\n"
        "Оберіть **1 слово** у кожній секції, яке найбільш відповідає вашій звичній поведінці.\n\n"
        f"**Секція 1 з {len(SECTIONS)}:**",
        reply_markup=build_section_keyboard(0),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data.startswith("ans:"))
async def handle_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = user_sessions.get(user_id)

    if not session:
        await callback.answer("Сесію не знайдено. Натисніть /start, щоб почати заново.", show_alert=True)
        return

    _, step_str, opt_str = callback.data.split(":")
    step_idx = int(step_str)
    opt_idx = int(opt_str)

    if step_idx != session["step"]:
        await callback.answer("Це запитання вже оброблено.", show_alert=False)
        return

    chosen_word, disc_type = SECTIONS[step_idx]["options"][opt_idx]
    session["scores"][disc_type] += 1
    session["step"] += 1

    # Оновлюємо повідомлення з поточною секцією, щоб зафіксувати вибір
    await callback.message.edit_text(
        f"**Секція {step_idx + 1} з {len(SECTIONS)}:** обрано *{chosen_word}*",
        parse_mode="Markdown",
    )

    if session["step"] < len(SECTIONS):
        next_step = session["step"]
        await callback.message.answer(
            f"**Секція {next_step + 1} з {len(SECTIONS)}:** оберіть 1 слово:",
            reply_markup=build_section_keyboard(next_step),
            parse_mode="Markdown",
        )
    else:
        result_text = format_result(session["scores"])
        del user_sessions[user_id]
        await callback.message.answer(
            result_text + "\n\nЩоб пройти тест ще раз — натисніть /start",
            parse_mode="Markdown",
        )

    await callback.answer()


async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())