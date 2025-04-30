from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from shopping_list import ShoppingList
import json
import os
import re
from dotenv import load_dotenv

# טעינת משתני הסביבה
load_dotenv()

# קבלת טוקן הבוט ממשתנה הסביבה
BOT_TOKEN = os.getenv('BOT_TOKEN')

# קבלת מזהי המשתמשים המורשים ממשתנה הסביבה (רשימה מופרדת בפסיק)
PARTNER_CHAT_IDS = os.getenv('PARTNER_CHAT_ID', '').split(',')

# טעינת רשימת הקניות מהקובץ או יצירת חדשה
def load_shopping_list():
    filename = "shared_shopping_list.json"
    if os.path.exists(filename):
        return ShoppingList.load_from_file(filename)
    return ShoppingList()

# שמירת רשימת הקניות לקובץ
def save_shopping_list(shopping_list):
    filename = "shared_shopping_list.json"
    shopping_list.save_to_file(filename)

# טעינת קטגוריות קבועות
def load_categories():
    if os.path.exists("categories.json"):
        with open("categories.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# שמירת קטגוריות קבועות
def save_categories(categories):
    with open("categories.json", 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

# פונקציה לזיהוי כמות מהטקסט
def extract_quantity(text):
    # אם אין מספרים בטקסט, מחזיר 1
    if not re.search(r'\d+', text):
        return 1
    
    # אם יש מספרים, מחזיר את הראשון
    numbers = re.findall(r'\d+', text)
    return int(numbers[0]) if numbers else 1

# פונקציה לזיהוי פעולה מהטקסט
def detect_action(text):
    text = text.lower()
    remove_words = ['קניתי', 'קנית', 'קנו', 'קנתה', 'קנו', 'מחק', 'הסר', 'הסרתי', 'הסיר', 'קנה', 'קנתה']
    if any(word in text for word in remove_words):
        return 'remove'
    return 'add'

# פונקציה ליצירת מקלדת אישור
def create_confirmation_keyboard(item_name, quantity):
    keyboard = [
        [
            InlineKeyboardButton("✅ כן, הוסף", callback_data=f"confirm_add_{item_name}_{quantity}"),
            InlineKeyboardButton("❌ לא, אל תוסיף", callback_data="cancel_add")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# פונקציה ליצירת מקלדת קטגוריות
def create_categories_keyboard(categories):
    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(category, callback_data=f"show_category_{category}")])
    return InlineKeyboardMarkup(keyboard)

# פונקציה ליצירת מקלדת פריטים לשינוי קטגוריה
def create_items_keyboard(items):
    keyboard = []
    for item_name in items:
        keyboard.append([InlineKeyboardButton(item_name, callback_data=f"change_category_{item_name}")])
    return InlineKeyboardMarkup(keyboard)

# פונקציה ליצירת מקלדת קטגוריות לשינוי קטגוריה של פריט
def create_category_change_keyboard(item_name):
    keyboard = []
    # קבלת כל הקטגוריות הייחודיות מהקטגוריות הקבועות
    all_categories = set(load_categories().values())
    for category in all_categories:
        keyboard.append([InlineKeyboardButton(category, callback_data=f"update_category_{item_name}_{category}")])
    return InlineKeyboardMarkup(keyboard)

# פונקציה ליצירת מקלדת קטגוריות למחיקה
def create_delete_categories_keyboard():
    keyboard = []
    categories = load_categories()
    for item_name, category in categories.items():
        keyboard.append([InlineKeyboardButton(f"{item_name} ({category})", callback_data=f"delete_category_{item_name}")])
    return InlineKeyboardMarkup(keyboard)

# פונקציה לטיפול בפקודת /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    shopping_list = load_shopping_list()
    context.user_data['shopping_list'] = shopping_list
    context.user_data['categories'] = load_categories()
    
    # הוספת הודעה שמציגה את מזהה הצ'אט
    chat_id_message = f"מזהה הצ'אט שלך הוא: {chat_id}\n\n"
    
    welcome_message = (
        chat_id_message +
        "👋 שלום! אני בוט רשימת קניות משותפת.\n\n"
        "אני מבין הודעות טבעיות בעברית:\n\n"
        "• כתוב שם פריט להוספה (למשל: 'חלב' או 'חלב 2')\n"
        "• כתוב 'קניתי' או 'מחק' ואחריו שם הפריט (למשל: 'קניתי חלב' או 'מחק חלב 2')\n"
        "• כתוב 'רשימה' כדי לראות את כל הפריטים\n"
        "• כתוב 'מחק רשימה' כדי לנקות את כל הרשימה\n\n"
        "אם תנסה להוסיף פריט שכבר קיים, אשאל אותך אם להוסיף אותו בכל זאת!\n\n"
        "הרשימה משותפת עם בן/בת הזוג שלך!"
    )
    
    await update.message.reply_text(welcome_message)

# פונקציה לטיפול בהודעות טקסט
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """מטפל בהודעות טקסט"""
    if not update.message or not update.message.text:
        return

    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)
    
    # שמירת ה-chat_id של המשתמש
    save_chat_id(chat_id)
    
    # בדיקה אם המשתמש מורשה
    if str(chat_id) not in [id.strip() for id in PARTNER_CHAT_IDS if id.strip()]:
        await update.message.reply_text("❌ לא מורשה להשתמש בבוט.")
        return

    # בדיקה אם יש רשימת קניות פעילה
    if 'shopping_list' not in context.user_data:
        context.user_data['shopping_list'] = ShoppingList()

    shopping_list = context.user_data['shopping_list']
    categories = context.user_data.get('categories', load_categories())
    
    try:
        # בדיקה אם זו תשובה לקטגוריה
        if context.user_data.get('waiting_for_category'):
            item_name = context.user_data['current_item']
            category = update.message.text.strip()
            
            # שמירת הקטגוריה בקבוע
            categories[item_name] = category
            save_categories(categories)
            context.user_data['categories'] = categories
            
            # עדכון הקטגוריה בפריט
            shopping_list.categories[item_name] = category
            context.user_data['shopping_list'] = shopping_list
            save_shopping_list(shopping_list)
            
            # ניקוי משתנים זמניים
            del context.user_data['current_item']
            del context.user_data['waiting_for_category']
            
            message = f"✅ שמרתי את הקטגוריה של {item_name} כ-{category}"
            await update.message.reply_text(message)
            return

        # בדיקה אם זו פקודה מיוחדת
        if update.message.text.lower() in ['רשימה', 'הצג רשימה', 'הראה רשימה']:
            if not shopping_list.items:
                await update.message.reply_text("📝 הרשימה ריקה")
                return
            
            message = "📝 *רשימת קניות*\n\n"
            for item_name, quantity in shopping_list.items.items():
                category = shopping_list.get_category(item_name) or categories.get(item_name)
                message += f"• {item_name} ({category or 'ללא קטגוריה'}): {quantity}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        elif update.message.text.lower() in ['מחק רשימה', 'נקה רשימה', 'אפס רשימה']:
            shopping_list.clear_list()
            save_shopping_list(shopping_list)
            message = "✅ הרשימה נוקתה בהצלחה!"
            await update.message.reply_text(message)
            return
        
        elif update.message.text.lower() in ['קטגוריות', 'הצג קטגוריות', 'הראה קטגוריות']:
            all_categories = set(categories.values())
            if not all_categories:
                await update.message.reply_text("📝 אין קטגוריות מוגדרות")
                return
            
            await update.message.reply_text(
                "📝 בחר קטגוריה כדי לראות את הפריטים שלה:",
                reply_markup=create_categories_keyboard(all_categories)
            )
            return
        
        elif update.message.text.lower() in ['החלף קטגוריה', 'שנה קטגוריה', 'עדכן קטגוריה']:
            if not shopping_list.items:
                await update.message.reply_text("📝 הרשימה ריקה")
                return
            
            await update.message.reply_text(
                "📝 בחר פריט לשינוי קטגוריה:",
                reply_markup=create_items_keyboard(shopping_list.items.keys())
            )
            return
        
        elif update.message.text.lower() in ['מחק קטגוריה', 'הסר קטגוריה', 'הסר קטגוריות']:
            if not categories:
                await update.message.reply_text("📝 אין קטגוריות מוגדרות")
                return
            
            await update.message.reply_text(
                "📝 בחר פריט למחיקת הקטגוריה שלו:",
                reply_markup=create_delete_categories_keyboard()
            )
            return

        # בדיקה אם ההודעה מכילה קטגוריה
        if ':' in update.message.text:
            item_name, category = update.message.text.split(':', 1)
            item_name = item_name.strip()
            category = category.strip()
            
            # הוספת פריט עם קטגוריה
            if item_name not in shopping_list.items:
                shopping_list.add_item(item_name, 1)
                shopping_list.categories[item_name] = category
                save_shopping_list(shopping_list)
                message = f"✅ הוספתי {item_name} לרשימה עם הקטגוריה: {category}"
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"❌ {item_name} כבר קיים ברשימה")
            return
        
        # זיהוי פעולה
        action = detect_action(update.message.text)
        
        # הסרת מילות פעולה מהטקסט
        clean_text = re.sub(r'קניתי|קנית|קנו|קנתה|קנו|מחק|הסר|הסרתי|הסיר|קנה|קנתה', '', update.message.text, flags=re.IGNORECASE).strip()
        
        if action == 'add':
            # הוספת פריט
            quantity = extract_quantity(clean_text)
            item_name = clean_text.replace(str(quantity), '').strip()
            
            if item_name not in shopping_list.items:
                shopping_list.add_item(item_name, quantity)
                save_shopping_list(shopping_list)
                message = f"✅ הוספתי {item_name} לרשימה"
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"❌ {item_name} כבר קיים ברשימה")
        else:
            # הסרת פריט
            item_name = clean_text
            if item_name in shopping_list.items:
                shopping_list.remove_item(item_name)
                save_shopping_list(shopping_list)
                message = f"✅ הסרתי {item_name} מהרשימה"
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"❌ {item_name} לא נמצא ברשימה")
    except Exception as e:
        print(f"Error in handle_message: {str(e)}")
        await update.message.reply_text("❌ אירעה שגיאה בעיבוד ההודעה. אנא נסה שוב.")

# פונקציה לטיפול בלחיצות על כפתורים
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    shopping_list = context.user_data.get('shopping_list', load_shopping_list())
    categories = context.user_data.get('categories', load_categories())
    
    if query.data.startswith("show_category_"):
        category = query.data.replace("show_category_", "")
        items_in_category = []
        
        for item_name, quantity in shopping_list.items.items():
            item_category = shopping_list.get_category(item_name) or categories.get(item_name)
            if item_category == category:
                items_in_category.append(f"• {item_name}: {quantity}")
        
        if items_in_category:
            message = f"📝 *פריטים בקטגוריה {category}:*\n\n" + "\n".join(items_in_category)
        else:
            message = f"📝 אין פריטים בקטגוריה {category}"
        
        await query.message.edit_text(message, parse_mode='Markdown')
    
    elif query.data.startswith("change_category_"):
        item_name = query.data.replace("change_category_", "")
        await query.message.edit_text(
            f"📝 בחר קטגוריה חדשה עבור {item_name}:",
            reply_markup=create_category_change_keyboard(item_name)
        )
    
    elif query.data.startswith("update_category_"):
        _, _, item_name, new_category = query.data.split("_")
        
        # עדכון הקטגוריה בקבוע
        categories[item_name] = new_category
        save_categories(categories)
        context.user_data['categories'] = categories
        
        # עדכון הקטגוריה בפריט
        if item_name in shopping_list.items:
            # שמירת הכמות הנוכחית
            current_quantity = shopping_list.items[item_name]
            # מחיקת הפריט הישן
            del shopping_list.items[item_name]
            # הוספת הפריט מחדש עם הקטגוריה החדשה
            shopping_list.add_item(item_name, current_quantity, category=new_category)
        
        context.user_data['shopping_list'] = shopping_list
        save_shopping_list(shopping_list)
        
        await query.message.edit_text(f"✅ שיניתי את הקטגוריה של {item_name} ל-{new_category}")
    
    elif query.data.startswith("delete_category_"):
        item_name = query.data.replace("delete_category_", "")
        
        if item_name in categories:
            # מחיקת הקטגוריה מהפריט
            del categories[item_name]
            save_categories(categories)
            context.user_data['categories'] = categories
            
            # עדכון הפריט ברשימה
            if item_name in shopping_list.items:
                current_quantity = shopping_list.items[item_name]
                del shopping_list.items[item_name]
                shopping_list.add_item(item_name, current_quantity)
            
            context.user_data['shopping_list'] = shopping_list
            save_shopping_list(shopping_list)
            
            await query.message.edit_text(f"✅ מחקתי את הקטגוריה של {item_name}")
        else:
            await query.message.edit_text(f"❌ לא נמצאה קטגוריה עבור {item_name}")
    
    elif query.data.startswith("confirm_add_"):
        # חילוץ המידע מהנתונים
        _, _, item_name, quantity = query.data.split("_")
        quantity = int(quantity)
        
        # הוספת הפריט
        shopping_list.add_item(item_name, quantity)
        context.user_data['shopping_list'] = shopping_list
        save_shopping_list(shopping_list)
        
        await query.message.edit_text(f"✅ הוספתי {quantity} {item_name} לרשימה!")
    
    elif query.data == "cancel_add":
        await query.message.edit_text("❌ ביטלתי את ההוספה.")

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in environment variables")
        return
    
    if not PARTNER_CHAT_IDS:
        print("Error: PARTNER_CHAT_ID not found in environment variables")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()
    
    # הוספת מטפלי פקודות
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # הפעלת הבוט
    application.run_polling()

if __name__ == "__main__":
    main() 