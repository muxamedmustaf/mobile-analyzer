import streamlit as st
from PIL import Image
import numpy as np
import cv2

st.set_page_config(page_title="True Candle Analyzer")
st.title("📈 Falanqaynta Shamacyada Dhabta ah (Candle Stick Vision)")
st.caption("App-ku wuxuu si gaar ah u baaraa shumacyada cagaaran iyo kuwa cas ee shartiga.")

uploaded_file = st.file_uploader("Soo geli sawirka shartiga", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Shartiga la falanqaynayo", use_column_width=True)
    
    if st.button("🚀 Falanqee Shumacyada"):
        with st.spinner("Waxaa la kala saarayaa shumacyada cagaaran iyo kuwa cas..."):
            
            # U beddelida sawirka habka OpenCV
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            
            # 1. Shaandhaynta Shumacyada Cagaaran (Green Candles)
            # Hue, Saturation, Value ranges oo loogu talagalay cagaarka shartiga
            lower_green1 = np.array([35, 50, 50])
            upper_green1 = np.array([85, 255, 255])
            mask_green = cv2.inRange(hsv, lower_green1, upper_green1)
            green_count = cv2.countNonZero(mask_green)
            
            # 2. Shaandhaynta Shumacyada Cas (Red/Pink Candles)
            # Casaanku wuxuu ku jiraa laba meelood oo kala duwan oo Hue spectrum ah (0-10 iyo 170-180)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            
            mask_red = cv2.bitwise_or(mask_red1, mask_red2)
            red_count = cv2.countNonZero(mask_red)
            
            # Hubinta in sawirku leeyahay shumacyo muuqata
            total_candles = green_count + red_count
            
            if total_candles < 150:
                st.error("❌ **Digniin:** Ma arkayo shumacyo ku filan ama shartigu ma cadda. Fadlan soo geli sawir sharti oo cad.")
            else:
                st.success("✅ Waa la helay shumacyadii suuqa!")
                
                # Isbarbar-dhigga xoogga cagaarka iyo casaanka
                st.write(قال: f"📊 Tirada dhibcaha Cagaaran: {green_count} | Dhibcaha Cas: {red_count}")
                
                if green_count > red_count:
                    trend = "Bullish Dominance (Awoodda Cagaaran / Kor u kac)"
                    signal = "BUY (Iibso)"
                    desc = "Shumacyada cagaaran ayaa ku badan, taasoo muujinaysa in iibsadayaashu ay haystaan suuqa."
                else:
                    trend = "Bearish Dominance (Awoodda Cas / Hoos u dhac)"
                    signal = "SELL (Iibi)"
                    desc = "Shumacyada cas ayaa ku badan, taasoo muujinaysa cadaadis iibiyeyaal ah."
                
                st.markdown(f"### 📊 Xaaladda Suuqa: **{trend}**")
                st.markdown(f"### 🎯 Go'aanka: **`{signal}`**")
                st.info(desc)
                
