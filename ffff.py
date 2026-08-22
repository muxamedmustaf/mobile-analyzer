import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

JSON_FILE = 'dynamic-camp-491505-i2-7b5e91a55337.json'
SHEET_GOLD_ID = "1TXvF6RhSgfJ631UpnWB38Ww1OMvZVx7VonDB_y1pO3s"

# النطاقات المعتمدة لوصول Google Drive و Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_symbols_from_sheet(spreadsheet_id=SHEET_GOLD_ID, sheet_name="Sheet1", column_name="Ticker", json_path=JSON_FILE):
    """
    تقوم هذه الدالة بالاتصال بـ Google Sheets باستخدام ملف الاعتمادات الخدمي JSON،
    وتقرأ القائمة وتستخرج رموز الأزواج والعملات.
    """
    try:
        # 1. الاتصال بـ Google API باستخدام JSON
        if os.path.exists(json_path):
            creds = Credentials.from_service_account_file(json_path, scopes=SCOPES)
            gc = gspread.authorize(creds)
            
            sh = gc.open_by_key(spreadsheet_id)
            worksheet = sh.worksheet(sheet_name)
            
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
        else:
            # طريقة احتياطية للقراءة المباشرة مجاناً عبر CSV في حال عدم وجود ملف JSON
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
            df = pd.read_csv(url)

        if df.empty:
            return [], "جدول البيانات فارغ أو يتعذر استخراج البيانات منه."

        # 2. المطابقة الذكية للعمود المخصص لرموز العملات
        matched_col = None
        for col in df.columns:
            if str(col).strip().lower() == column_name.strip().lower():
                matched_col = col
                break
        
        if matched_col is None:
            # إذا لم يتم العثور على اسم العمود، نأخذ العمود الأول
            matched_col = df.columns[0]

        # تنظيف النتيجة واستبعاد الخلايا الفارغة
        symbols = df[matched_col].dropna().astype(str).str.strip().tolist()
        # تنظيف القيم الفارغة الكاذبة
        symbols = [s for s in symbols if s and s.lower() != 'nan']

        return symbols, None

    except Exception as e:
        return [], f"خطأ أثناء جلب البيانات من Google Sheet: {str(e)}"
      
