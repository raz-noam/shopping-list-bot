import json
import os

# מחלקה לניהול רשימת קניות
class ShoppingList:
    # פונקציה שמתבצעת בעת יצירת אובייקט חדש של רשימת קניות
    def __init__(self):
        self.items = {}  # Dictionary to store items and their quantities
        self.categories = {}  # Dictionary to store item categories

    # פונקציה להוספת פריט לרשימה
    def add_item(self, name, quantity=1, category=None):
        """Add an item to the shopping list"""
        if name in self.items:
            self.items[name] += quantity
        else:
            self.items[name] = quantity
            if category is not None:
                self.categories[name] = category

    # פונקציה להסרת פריט מהרשימה
    def remove_item(self, name, quantity=1):
        """Remove an item from the shopping list"""
        if name in self.items:
            if quantity >= self.items[name]:
                del self.items[name]
                if name in self.categories:
                    del self.categories[name]
            else:
                self.items[name] -= quantity

    # פונקציה לנקה את הרשימה
    def clear_list(self):
        """Clear the entire shopping list"""
        self.items.clear()
        self.categories.clear()

    # פונקציה לקבלת הרשימה הנוכחית
    def get_list(self):
        """Get the current shopping list"""
        return self.items

    def get_category(self, item_name):
        """Get the category of an item"""
        return self.categories.get(item_name)

    # פונקציה לחישוב הסכום הכולל
    def calculate_total(self):
        """
        חישוב הסכום הכולל של רשימת הקניות
        :return: סכום כולל
        """
        total = 0
        for item in self.items.values():
            if item['price'] is not None:
                total += item['price'] * item['quantity']
        return total

    # פונקציה להצגת הרשימה בפורמט יפה
    def format_list(self):
        """
        הצגת רשימת הקניות בפורמט קריא
        :return: מחרוזת מעוצבת של רשימת הקניות
        """
        # אם הרשימה ריקה, מחזירים הודעה מתאימה
        if not self.items:
            return "הרשימה ריקה"
        
        # יצירת כותרת לרשימה
        formatted_list = "רשימת הקניות שלך:\n"
        
        # מיון לפי קטגוריות אם יש
        if self.categories:
            for category in sorted(self.categories):
                formatted_list += f"\nקטגוריה: {category}\n"
                for item_name, details in self.items.items():
                    if details['category'] == category:
                        formatted_list += self._format_item(item_name, details)
        else:
            # אם אין קטגוריות, מציגים את כל הפריטים
            for item_name, details in self.items.items():
                formatted_list += self._format_item(item_name, details)
        
        # הוספת סכום כולל אם יש מחירים
        total = self.calculate_total()
        if total > 0:
            formatted_list += f"\nסכום כולל: {total:.2f} ₪"
        
        return formatted_list

    # פונקציה עזר לעיצוב פריט בודד
    def _format_item(self, item_name, details):
        """עיצוב פריט בודד לרשימה"""
        line = f"- {item_name}: {details['quantity']}"
        if details['price'] is not None:
            line += f" (מחיר: {details['price']} ₪ ליחידה)"
        return line + "\n"

    # פונקציה לשמירת הרשימה לקובץ
    def save_to_file(self, filename):
        """Save the shopping list to a file"""
        data = {
            'items': self.items,
            'categories': self.categories
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # פונקציה לטעינת רשימה מקובץ
    @classmethod
    def load_from_file(cls, filename):
        """Load a shopping list from a file"""
        shopping_list = cls()
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                shopping_list.items = data.get('items', {})
                shopping_list.categories = data.get('categories', {})
        except FileNotFoundError:
            pass
        return shopping_list

# דוגמת שימוש בקוד
if __name__ == "__main__":
    # יצירת אובייקט חדש של רשימת קניות
    shopping_list = ShoppingList()
    
    # הוספת פריטים לרשימה עם קטגוריות ומחירים
    shopping_list.add_item("חלב", 2, "מוצרי חלב")  # הוספת 2 חלב בקטגוריית מוצרי חלב
    shopping_list.add_item("לחם", 1, "מאפים")     # הוספת לחם בקטגוריית מאפים
    shopping_list.add_item("ביצים", 12, "מוצרי חלב")  # הוספת 12 ביצים בקטגוריית מוצרי חלב
    shopping_list.add_item("עגבניות", 5, "ירקות")  # הוספת 5 עגבניות בקטגוריית ירקות
    
    # הדפסת הרשימה המעוצבת
    print(shopping_list.format_list())
    
    # שמירת הרשימה לקובץ
    filename = shopping_list.save_to_file()
    print(f"\nהרשימה נשמרה בקובץ: {filename}")
    
    # טעינת הרשימה מהקובץ
    loaded_list = ShoppingList.load_from_file(filename)
    print("\nרשימה נטענה מהקובץ:")
    print(loaded_list.format_list()) 