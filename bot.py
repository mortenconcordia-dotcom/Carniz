import os
import math
from typing import Optional, Dict, Any, List, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --------- Conversation states ----------
CHOOSE_MODE, ENTER_LENGTH = range(2)

# --------- Modes ----------
MODE_CENTER = "center"
MODE_LR = "left_right"

# --------- Callback data ----------
CB_CENTER = "mode_center"
CB_LR = "mode_lr"
CB_NEW = "new_calc"
CB_BACK = "back_to_menu"

# ----------------- .env loader (no extra deps) -----------------
def load_env_file(path: str = ".env") -> None:
    """Loads KEY=VALUE pairs from .env into os.environ if not already set."""
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        # If .env is malformed we just ignore it; BOT_TOKEN must still be provided somehow.
        return

# ----------------- UI -----------------
def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("К центру", callback_data=CB_CENTER),
                InlineKeyboardButton("Слева-Направо", callback_data=CB_LR),
            ]
        ]
    )

def after_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Начать новый расчёт", callback_data=CB_NEW)],
        ]
    )

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⬅️ Назад к выбору", callback_data=CB_BACK)],
        ]
    )

# ----------------- Parsing -----------------
def parse_length(text: str) -> Optional[float]:
    """Accepts: '404', '404.5', '404,5', '404 см' -> float cm."""
    t = text.strip().lower()
    t = t.replace("см", "").strip()
    t = t.replace(",", ".")
    try:
        x = float(t)
        if x <= 0:
            return None
        return x
    except ValueError:
        return None

# ----------------- Calculator logic (as per your verified screenshots) -----------------
def even_up(n: int) -> int:
    """Make integer even by rounding up to the next even if needed."""
    return n if n % 2 == 0 else n + 1

def calc(mode: str, x: float) -> Dict[str, Any]:
    """Returns dict: mode_name, X, L, parts_count N, part_len S, runners, hooks, mounts."""
    if mode == MODE_CENTER:
        mode_name = "К центру"
        L = x - 15.2
    elif mode == MODE_LR:
        mode_name = "Слева-Направо"
        L = x - 11.6
    else:
        raise ValueError("Unknown mode")

    L = max(0.0, L)
    N = max(1, math.ceil(L / 300.0))
    S = round(L / N, 1)

    runners = even_up(math.ceil(x / 8.0))
    hooks = runners + 10
    mounts = math.ceil(x / 100.0) + 1

    return {
        "mode_name": mode_name,
        "X": x,
        "L": round(L, 1),
        "N": N,
        "S": S,
        "runners": runners,
        "hooks": hooks,
        "mounts": mounts,
    }

def format_scheme(S: float, N: int) -> str:
    return "   ".join([f"{S} см" for _ in range(N)])

# ----------------- Handlers -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Выберите режим расчёта:",
        reply_markup=menu_keyboard()
    )
    return CHOOSE_MODE

async def on_mode_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    if q.data == CB_CENTER:
        context.user_data["mode"] = MODE_CENTER
        await q.edit_message_text("Режим: К центру.\nВведите длину карниза X (см):", reply_markup=back_keyboard())
        return ENTER_LENGTH

    if q.data == CB_LR:
        context.user_data["mode"] = MODE_LR
        await q.edit_message_text("Режим: Слева-Направо.\nВведите длину карниза X (см):", reply_markup=back_keyboard())
        return ENTER_LENGTH

    await q.edit_message_text("Выберите режим расчёта:", reply_markup=menu_keyboard())
    return CHOOSE_MODE

async def on_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data.pop("mode", None)
    await q.edit_message_text("Выберите режим расчёта:", reply_markup=menu_keyboard())
    return CHOOSE_MODE

async def on_new_calc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    await q.edit_message_text("Выберите режим расчёта:", reply_markup=menu_keyboard())
    return CHOOSE_MODE

async def on_length(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mode = context.user_data.get("mode")
    if mode not in (MODE_CENTER, MODE_LR):
        await update.message.reply_text("Сначала выберите режим:", reply_markup=menu_keyboard())
        return CHOOSE_MODE

    x = parse_length(update.message.text)
    if x is None:
        await update.message.reply_text("Введите число в см (например: 404 или 404.5):")
        return ENTER_LENGTH

    res = calc(mode, x)
    scheme = format_scheme(res["S"], res["N"])

    text = (
        f"✅ Результат\n"
        f"Режим: {res['mode_name']}\n"
        f"Длина карниза X: {res['X']} см\n\n"
        f"Схема: {scheme}\n"
        f"Рабочая длина L: {res['L']} см\n\n"
        f"Бегунков: {res['runners']} шт.\n"
        f"Крючков: {res['hooks']} шт.\n"
        f"Креплений: {res['mounts']} шт."
    )

    await update.message.reply_text(text, reply_markup=after_result_keyboard())
    return CHOOSE_MODE

async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quick self-check using control values from our comparisons."""
    tests: List[float] = [202, 289, 404, 510, 550, 653]
    lines: List[str] = ["🧪 Тест (контрольные значения):"]
    for x in tests:
        c = calc(MODE_CENTER, x)
        lr = calc(MODE_LR, x)
        lines.append(
            f"\nX={x} см | Бегунки {c['runners']} | Крючки {c['hooks']} | Крепления {c['mounts']}"
        )
        lines.append(f"  К центру:  {format_scheme(c['S'], c['N'])}  (L={c['L']})")
        lines.append(f"  Слева→Напр: {format_scheme(lr['S'], lr['N'])}  (L={lr['L']})")

    await update.message.reply_text("\n".join(lines))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Ок. Нажмите /start чтобы начать заново.")
    return ConversationHandler.END

def main() -> None:
    # Load .env if present (so BOT_TOKEN can be stored there)
    load_env_file(".env")

    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Не найден BOT_TOKEN.\n"
            "Варианты: (1) задайте переменную окружения BOT_TOKEN, (2) положите BOT_TOKEN=... в файл .env рядом с bot.py"
        )

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_MODE: [
                CallbackQueryHandler(on_mode_click, pattern=f"^({CB_CENTER}|{CB_LR})$"),
                CallbackQueryHandler(on_new_calc, pattern=f"^{CB_NEW}$"),
            ],
            ENTER_LENGTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, on_length),
                CallbackQueryHandler(on_back_to_menu, pattern=f"^{CB_BACK}$"),
                CallbackQueryHandler(on_new_calc, pattern=f"^{CB_NEW}$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("test", test_cmd))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
