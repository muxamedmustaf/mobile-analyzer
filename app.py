import streamlit as st
import google.generativeai as genai
from PIL import Image

# إعداد واجهة الجوال
st.set_page_config(page_title="مُحلل الشارت الذكي", page_icon="📈", layout="centered")

st.title("📈 المُحلل المالي البصري الشامل")
st.caption("تحليل لقطات الشاشات الفنية مع اختيار النموذج ديناميكياً")

# إدخال المفتاح
api_key = st.text_input("أدخل مفتاح Google Gemini API:", type="password")

# رفع الصورة
uploaded_file = st.file_uploader("ارفع لقطة شاشة للشارت:", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="الشارت المراد تحليله", use_container_width=True)

if st.button("🚀 بدء التحليل الشامل والتوافق", use_container_width=True):
    if not api_key:
        st.error("يرجى إدخال مفتاح الـ API أولاً.")
    elif not uploaded_file:
        st.error("يرجى رفع صورة الشارت.")
    else:
        with st.spinner("جاري فحص النماذج المتاحة وحساب درجات التوافق..."):
            try:
                # تهيئة المكتبة بمفتاح الـ API
                genai.configure(api_key=api_key)
                
                # --- آلية اختيار النموذج ديناميكياً ---
                available_models = [
                    m.name for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                # البحث عن أحدث نموذج متوفر في حسابك (Gemini Flash أو Pro)
                selected_model_name = None
                for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision', 'gemini-1.0-pro']:
                    for m in available_models:
                        if preferred in m:
                            selected_model_name = m
                            break
                    if selected_model_name:
                        break
                
                # إذا لم يجد الأفضلية، يختار أول نموذج متاح يدعم generateContent
                if not selected_model_name and available_models:
                    selected_model_name = available_models[0]

                if not selected_model_name:
                    st.error("لم يتم العثور على أي نموذج مفعل على مفتاح API الخاص بك.")
                else:
                    # طباعة اسم النموذج المستعمل في الواجهة للتأكد
                    st.info(f"🤖 النمط المستخدم للتحليل: `{selected_model_name}`")

                    model = genai.GenerativeModel(selected_model_name)

                    prompt = """
                    أنت خبير محترف في التحليل الفني ومدرسة السلوك السعري (Price Action). 
                    قم بقراءة وتحليل صورة الشارت المرفقة بدقة عالية جداً وتقديم تقرير هيكلي شامل بالشكل التالي:

                    1. 📊 **تحديد الاتجاه وسلوك السعر (Price Action):**
                       - الاتجاه العام (صاعد / هابط / عرضي).
                       - مستويات الدعم والمقاومة المرئية بالأرقام أو المستويات المحددة.

                    2. 🔍 **كشف الأنماط والشموع (Pattern Recognition):**
                       - نماذج الشارت الكلاسيكية المرئية (مثل: الرأس والكتفين، القمتين/القاعين، القنوات، المثلثات).
                       - نماذج الشموع اليابانية المؤكدة (مثل: Pin Bar, Engulfing, Doji).

                    3. 📉 **تحليل المؤشرات الفنية (إن وجدت في الصورة):**
                       - قراءة المتوسطات المتحركة (EMA/MA)، مؤشر RSI، MACD، أو ADX إذا كانت واضحة على الرسم البياني.

                    4. ⚖️ **جدول الترجيح وتوافق العلامات (Confluence Score Matrix):**
                       - اذكر كل علامة/مؤشر تم اكتشافه مع إعطائه درجة توافق من (1 إلى 10) وتوضيح تحيزه (صعود أو هبوط).
                       - احسب **نسبة التوافق الإجمالية (Confluence Percentage)** بناءً على عدد الإشارات المتطابقة.

                    5. 🎯 **التوصية الفنية النهائية:**
                       - القرار الترجيحي الأقوى: (شراء / بيع / انتظار وتريّث).
                       - سيناريو الدخول، ومستوى وقف الخسارة المقترح، وأهداف جني الأرباح.
                    """

                    # إرسال الصورة والبرومبت للنموذج الديناميكي
                    response = model.generate_content([prompt, image])
                    
                    st.success("تم التقييم والتحليل بنجاح!")
                    st.markdown(response.text)

            except Exception as e:
                st.error(f"حدث خطأ أثناء إجراء التحليل: {e}")
                
