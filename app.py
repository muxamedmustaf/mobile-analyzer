import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io

# Setup Page
st.set_page_config(page_title="مُحلل الشارت الذكي (OpenRouter)", page_icon="📈", layout="centered")

st.title("📈 المُحلل المالي البصري الشامل")
st.caption("تحليل لقطات الشاشات الفنية بدقة عالية باستخدام OpenRouter API")

# Input key & file
api_key = st.text_input("أدخل مفتاح OpenRouter API الخاص بك:", type="password")
uploaded_file = st.file_uploader("ارفع لقطة شاشة للشارت:", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="الشارت المراد تحليله", use_container_width=True)

if st.button("🚀 بدء التحليل الشامل والتوافق", use_container_width=True):
    if not api_key:
        st.error("يرجى إدخال مفتاح الـ OpenRouter API أولاً.")
    elif not uploaded_file:
        st.error("يرجى رفع صورة الشارت.")
    else:
        with st.spinner("جاري مسح الشارت والبحث عن أفضل نموذج متاح للتحليل..."):
            try:
                # Convert Image to Base64 Format
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                base64_image = f"data:image/png;base64,{img_str}"

                # Initialize OpenAI client pointed to OpenRouter
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key.strip(),
                )

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
                   - سيناريو الدخول، ومستوى وقف الخسارة المقترح، وأهداف جني الأرباح (يجب أن تعرض الأهداف ووقف الخسارة كأرقام أسعار دقيقة، ولا تستخدم النسبة المئوية إطلاقاً).
                """

                # قائمة النماذج المجانية الفعالة (Fallback List)
                fallback_models = [
                    "meta-llama/llama-3.2-11b-vision-instruct:free",
                    "qwen/qwen-2-vl-7b-instruct:free",
                    "meta-llama/llama-3.2-90b-vision-instruct:free"
                ]

                response = None
                used_model = ""

                # تجربة النماذج واحداً تلو الآخر حتى ينجح أحدهم
                for m in fallback_models:
                    try:
                        response = client.chat.completions.create(
                            model=m,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": base64_image
                                            }
                                        }
                                    ]
                                }
                            ],
                            max_tokens=2048
                        )
                        used_model = m
                        break  # الخروج من الحلقة بمجرد نجاح التحليل
                    except Exception:
                        continue  # في حال فشل النموذج، جرب الذي يليه

                # طباعة النتيجة
                if response:
                    st.info(f"🤖 تم التحليل بنجاح باستخدام النموذج: `{used_model}`")
                    st.markdown(response.choices[0].message.content)
                else:
                    st.error("عذراً، لم نتمكن من الوصول لأي نموذج رؤية مجاني فعال حالياً على منصة OpenRouter.")

            except Exception as e:
                st.error(f"حدث خطأ غير متوقع: {e}")
                
