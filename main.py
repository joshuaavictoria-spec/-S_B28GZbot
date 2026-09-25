import os
import secrets
import string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Configuration from environment variable (set in Railway)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# Character sets
LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"

def generate_password(length=12, use_upper=True, use_digits=True, use_special=True):
    """Generate a cryptographically secure password locally."""
    chars = LOWERCASE
    if use_upper:
        chars += UPPERCASE
    if use_digits:
        chars += DIGITS
    if use_special:
        chars += SPECIAL
    
    if not chars:
        chars = LOWERCASE
    
    return "".join(secrets.choice(chars) for _ in range(length))

def get_strength(password):
    """Simple strength indicator."""
    score = 0
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in SPECIAL for c in password):
        score += 1
    
    if score <= 2:
        return "Weak 🔴"
    elif score <= 4:
        return "Medium 🟡"
    else:
        return "Strong 🟢"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with the main menu."""
    keyboard = [
        [InlineKeyboardButton("🔐 Generate Password", callback_data="generate_default")],
        [InlineKeyboardButton("⚙️ Custom Length", callback_data="custom_length")],
        [InlineKeyboardButton("📦 Batch Generate (5)", callback_data="batch_generate")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *Password Generator Bot*\n\n"
        "Generate strong passwords locally. No data is collected or uploaded.\n\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help information."""
    help_text = (
        "📖 *Help*\n\n"
        "• *Generate Password*: Creates a 12-character password with uppercase, digits, and special characters.\n"
        "• *Custom Length*: Choose a length between 8 and 32 characters.\n"
        "• *Batch Generate*: Creates 5 passwords at once.\n\n"
        "🔒 *Privacy*: All passwords are generated locally on the server and never stored or transmitted."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "generate_default":
        password = generate_password(12, True, True, True)
        strength = get_strength(password)
        await query.edit_message_text(
            f"🔐 *Generated Password*\n\n"
            f"`{password}`\n\n"
            f"Strength: {strength}\n\n"
            f"Tap the password to copy it.",
            parse_mode="Markdown"
        )
    
    elif data == "custom_length":
        keyboard = [
            [InlineKeyboardButton("8", callback_data="len_8"), InlineKeyboardButton("12", callback_data="len_12"), InlineKeyboardButton("16", callback_data="len_16")],
            [InlineKeyboardButton("20", callback_data="len_20"), InlineKeyboardButton("24", callback_data="len_24"), InlineKeyboardButton("32", callback_data="len_32")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")],
        ]
        await query.edit_message_text(
            "Select password length:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("len_"):
        length = int(data.split("_")[1])
        password = generate_password(length, True, True, True)
        strength = get_strength(password)
        await query.edit_message_text(
            f"🔐 *Generated Password* ({length} chars)\n\n"
            f"`{password}`\n\n"
            f"Strength: {strength}\n\n"
            f"Tap the password to copy it.",
            parse_mode="Markdown"
        )
    
    elif data == "batch_generate":
        passwords = [generate_password(12, True, True, True) for _ in range(5)]
        text = "📦 *Batch Passwords*\n\n"
        for i, pwd in enumerate(passwords, 1):
            text += f"{i}. `{pwd}`\n"
        text += "\nTap any password to copy it."
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif data == "help":
        await query.edit_message_text(
            "📖 *Help*\n\n"
            "Use the buttons to generate passwords. All generation is local and secure.",
            parse_mode="Markdown"
        )
    
    elif data == "back_to_menu":
        keyboard = [
            [InlineKeyboardButton("🔐 Generate Password", callback_data="generate_default")],
            [InlineKeyboardButton("⚙️ Custom Length", callback_data="custom_length")],
            [InlineKeyboardButton("📦 Batch Generate (5)", callback_data="batch_generate")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        ]
        await query.edit_message_text(
            "🔐 *Password Generator Bot*\n\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple health check endpoint for Railway."""
    return "ok"

def main():
    """Start the bot with webhooks (Railway-compatible)."""
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Webhook URL based on Railway's public domain
    webhook_url = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN')}/webhook"
    
    print(f"Starting bot with webhook: {webhook_url}")
    
    # Run webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="webhook",
        webhook_url=webhook_url,
        secret_token=os.environ.get("WEBHOOK_SECRET", "default_secret"),
    )

if __name__ == "__main__":
    main()
