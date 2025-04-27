import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from shopping_list import ShoppingList
import json
from datetime import datetime
from telegram import Bot
import asyncio
import threading

class ShoppingListGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("רשימת קניות")
        self.root.geometry("800x600")
        
        # יצירת רשימת קניות חדשה
        self.shopping_list = ShoppingList()
        
        # יצירת מסגרת ראשית
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # יצירת אזור הוספת פריטים
        self.create_add_item_frame()
        
        # יצירת אזור הצגת הרשימה
        self.create_list_frame()
        
        # יצירת אזור כפתורים
        self.create_buttons_frame()
        
        # יצירת אזור הגדרות טלגרם
        self.create_telegram_frame()
        
        # הגדרת הרחבה של החלון
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

    def create_add_item_frame(self):
        # יצירת מסגרת להוספת פריטים
        add_frame = ttk.LabelFrame(self.main_frame, text="הוספת פריט", padding="5")
        add_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # שדות קלט
        ttk.Label(add_frame, text="שם הפריט:").grid(row=0, column=0, padx=5, pady=5)
        self.item_name = ttk.Entry(add_frame)
        self.item_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="כמות:").grid(row=1, column=0, padx=5, pady=5)
        self.quantity = ttk.Spinbox(add_frame, from_=1, to=100, width=5)
        self.quantity.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="קטגוריה:").grid(row=2, column=0, padx=5, pady=5)
        self.category = ttk.Entry(add_frame)
        self.category.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="מחיר:").grid(row=3, column=0, padx=5, pady=5)
        self.price = ttk.Entry(add_frame)
        self.price.grid(row=3, column=1, padx=5, pady=5)
        
        # כפתור הוספה
        ttk.Button(add_frame, text="הוסף פריט", command=self.add_item).grid(row=4, column=0, columnspan=2, pady=5)

    def create_list_frame(self):
        # יצירת מסגרת להצגת הרשימה
        list_frame = ttk.LabelFrame(self.main_frame, text="רשימת קניות", padding="5")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # יצירת Treeview להצגת הרשימה
        self.tree = ttk.Treeview(list_frame, columns=("שם", "כמות", "קטגוריה", "מחיר"), show="headings")
        self.tree.heading("שם", text="שם הפריט")
        self.tree.heading("כמות", text="כמות")
        self.tree.heading("קטגוריה", text="קטגוריה")
        self.tree.heading("מחיר", text="מחיר")
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # הוספת scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # הגדרת הרחבה של העץ
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

    def create_buttons_frame(self):
        # יצירת מסגרת לכפתורים
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        # כפתורים
        ttk.Button(buttons_frame, text="הסר פריט נבחר", command=self.remove_selected_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="שמור רשימה", command=self.save_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="טען רשימה", command=self.load_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="חשב סכום", command=self.show_total).pack(side=tk.LEFT, padx=5)

    def create_telegram_frame(self):
        # יצירת מסגרת להגדרות טלגרם
        telegram_frame = ttk.LabelFrame(self.main_frame, text="הגדרות טלגרם", padding="5")
        telegram_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # שדות קלט
        ttk.Label(telegram_frame, text="טוקן הבוט:").grid(row=0, column=0, padx=5, pady=5)
        self.bot_token = ttk.Entry(telegram_frame, width=50)
        self.bot_token.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(telegram_frame, text="ID הצ'אט:").grid(row=1, column=0, padx=5, pady=5)
        self.chat_id = ttk.Entry(telegram_frame, width=50)
        self.chat_id.grid(row=1, column=1, padx=5, pady=5)
        
        # כפתור שליחה
        ttk.Button(telegram_frame, text="שלח לטלגרם", command=self.send_to_telegram).grid(row=2, column=0, columnspan=2, pady=5)

    def add_item(self):
        # הוספת פריט לרשימה
        try:
            name = self.item_name.get()
            quantity = int(self.quantity.get())
            category = self.category.get() if self.category.get() else None
            price = float(self.price.get()) if self.price.get() else None
            
            if not name:
                messagebox.showerror("שגיאה", "חובה להזין שם פריט")
                return
            
            self.shopping_list.add_item(name, quantity, category, price)
            self.update_list_display()
            
            # ניקוי השדות
            self.item_name.delete(0, tk.END)
            self.quantity.delete(0, tk.END)
            self.quantity.insert(0, "1")
            self.category.delete(0, tk.END)
            self.price.delete(0, tk.END)
            
        except ValueError:
            messagebox.showerror("שגיאה", "נא להזין ערכים תקינים")

    def update_list_display(self):
        # עדכון תצוגת הרשימה
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for item_name, details in self.shopping_list.items.items():
            self.tree.insert("", tk.END, values=(
                item_name,
                details['quantity'],
                details['category'] or "",
                f"{details['price']} ₪" if details['price'] is not None else ""
            ))

    def remove_selected_item(self):
        # הסרת פריט נבחר
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("אזהרה", "נא לבחור פריט להסרה")
            return
        
        item_name = self.tree.item(selected[0])['values'][0]
        self.shopping_list.remove_item(item_name)
        self.update_list_display()

    def save_list(self):
        # שמירת הרשימה לקובץ
        filename = f"shopping_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.shopping_list.save_to_file(filename)
        messagebox.showinfo("שמירה", f"הרשימה נשמרה בקובץ: {filename}")

    def load_list(self):
        # טעינת רשימה מקובץ
        try:
            filename = tk.filedialog.askopenfilename(
                title="בחר קובץ רשימה",
                filetypes=[("JSON files", "*.json")]
            )
            if filename:
                self.shopping_list = ShoppingList.load_from_file(filename)
                self.update_list_display()
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בטעינת הקובץ: {str(e)}")

    def show_total(self):
        # הצגת הסכום הכולל
        total = self.shopping_list.calculate_total()
        messagebox.showinfo("סכום כולל", f"הסכום הכולל: {total:.2f} ₪")

    def send_to_telegram(self):
        # שליחה לטלגרם
        try:
            token = self.bot_token.get()
            chat_id = self.chat_id.get()
            
            if not token or not chat_id:
                messagebox.showerror("שגיאה", "חובה להזין טוקן ו-ID צ'אט")
                return
            
            # יצירת בוט
            bot = Bot(token=token)
            
            # יצירת הודעה
            message = "📝 *רשימת קניות*\n\n"
            
            # מיון לפי קטגוריות
            if self.shopping_list.categories:
                for category in sorted(self.shopping_list.categories):
                    message += f"*{category}:*\n"
                    for item_name, details in self.shopping_list.items.items():
                        if details['category'] == category:
                            message += self._format_telegram_item(item_name, details)
            else:
                for item_name, details in self.shopping_list.items.items():
                    message += self._format_telegram_item(item_name, details)
            
            # הוספת סכום כולל
            total = self.shopping_list.calculate_total()
            if total > 0:
                message += f"\n*סכום כולל:* {total:.2f} ₪"
            
            # שליחת ההודעה
            asyncio.run(bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown'))
            messagebox.showinfo("הצלחה", "הרשימה נשלחה בהצלחה לטלגרם")
            
        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בשליחה לטלגרם: {str(e)}")

    def _format_telegram_item(self, item_name, details):
        """עיצוב פריט בודד להודעה בטלגרם"""
        line = f"• {item_name}: {details['quantity']}"
        if details['price'] is not None:
            line += f" (מחיר: {details['price']} ₪ ליחידה)"
        return line + "\n"

if __name__ == "__main__":
    root = tk.Tk()
    app = ShoppingListGUI(root)
    root.mainloop() 