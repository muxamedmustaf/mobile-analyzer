import streamlit as st
from PIL import Image
import numpy as np
import cv2
import pytesseract

st.set_page_config(page_title="True Smart Chart AI")
st.title("📈 Falanqaynta Shartiga ee OCR-ka (Smart Text Vision)")
st.caption("App-ku wuxuu hadda akhrinayaa qoraalada iyo nambarada dhabta ah ee shartiga.")

uploaded_file = st.file_uploader("Soo geli sawirka shartiga", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Sawirka la soo geliyay", use_column_width=True)
    
    if st.button("🚀 Bilow Akhrinta Qoraalka (OCR)"):
        with st.spinner("Waxaa la baaritaanka qoraalada iyo nambarada shartiga..."):
            
            # U beddelida sawirka mid madow iyo caddaan ah si OCR-ku u si fiican u akhriyo
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            
            # Isticmaalka pytesseract si uu u soo saaro qoraalka ku jira sawirka
            extracted_text = pytesseract.image_to_string(img_cv).upper()
            
            # Calaamadaha lagu garto shartiga dhabta ah (Sida nambarada qiimaha ama erayada BUY/SELL)
            chart_keywords = ["BUY", "SELL", "EUR", "USD", "GBP", "BTC", "D1", "H1", "M15", "0."]
            
            # Hubinta in ugu yaraan laba ka mid ah ereyadaas ay sawirka ka dhex muuqdaan
            matches = sum(1 for word in chart_keywords if word in extracted_text)
            
            if matches < 2:
                st.error("❌ **Khalad:** Sawirkani MA AHA sharti suuq! Waa khariidad, chat, ama sawir caadi ah. Fadlan soo geli sharti sax ah.")
            else:
                st.success("✅ Waa la xaqiijiyay: Waa sharti dhab ah oo leh xog suuq!")
                
                # Halkan waxaa ka bilaabmaya falanqaynta midabada shamacyada ee shartiga dhabta ah
                img_color = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV)
                
                green_count = cv2.countNonZero(cv2.inRange(img_color, np.array([35, 50, 50]), np.array([85, 255, 255])))
                
                red_mask1 = cv2.inRange(img_color, np.array([0, 50, 50]), np.array([10, 255, 255]))
                red_mask2 = cv2.inRange(img_color, np.array([170, 50, 50]), np.array([180, 255, 255]))
                red_count = cv2.countNonZero(cv2.bitwise_or(red_mask1, red_mask2))
                
                if green_count > red_count:
                    trend = "Bullish Uptrend (Kor u kac)"
                    signal = "BUY (Fursad Iibsi)"
                else:
                    trend = "Bearish Downtrend (Hoos u dhac)"
                    signal = "SELL (Fursad Iibin)"
                
                st.markdown(f"### 📊 Xaaladda Suuqa: **{trend}**")
                st.markdown(f"### 🎯 Go'aanka: **`{signal}`**")
                
