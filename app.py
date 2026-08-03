import streamlit as st
from PIL import Image
import numpy as np
import cv2
import pytesseract

st.set_page_config(page_title="Structure High & Low Chart Analyzer")
st.title("📊 Falanqeeyaha Qaab-dhismeedka Suuqa (High & Low / Support & Resistance)")
st.caption("App-ku wuxuu eegayaa High (Resistance) iyo Low (Support) si uu u go'aamiyo BUY ama SELL.")

uploaded_file = st.file_uploader("Soo geli sawirka shartiga suuqa", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Shartiga la falanqeynayo", use_column_width=True)
    
    if st.button("🚀 Falanqee High & Low (Support & Resistance)"):
        with st.spinner("Waxaa la baaraynaa heerarka Resistance (H) iyo Support (L)..."):
            
            # 1. Sawirka oo loo beddelo OpenCV format
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            h_img, w_img, _ = img_cv.shape
            
            # 2. Diiradda saarista dhinaca midig ee qiimaha ugu dambeeya (Recent Price & Wave zone)
            right_zone = img_cv[:, int(w_img * 0.7):w_img]
            hsv_right = cv2.cvtColor(right_zone, cv2.COLOR_BGR2HSV)
            
            # Midabada shumacyada ee aagga midig
            green_mask = cv2.inRange(hsv_right, np.array([35, 40, 40]), np.array([85, 255, 255]))
            red_mask1 = cv2.inRange(hsv_right, np.array([0, 40, 40]), np.array([10, 255, 255]))
            red_mask2 = cv2.inRange(hsv_right, np.array([170, 40, 40]), np.array([180, 255, 255]))
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            green_pixels = cv2.countNonZero(green_mask)
            red_pixels = cv2.countNonZero(red_mask)
            
            # 3. Kontoroolka Contours-ka si loo helo meelaha ay ku yaalliin High (Resistance) iyo Low (Support)
            combined_mask = cv2.bitwise_or(green_mask, red_mask)
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            resistance_h = "Not Tested"
            support_l = "Not Tested"
            market_structure = "Neutral"
            
            if contours:
                # Soo helidda dhererka iyo meesha uu qiimuhu ku eg yahay
                y_coords = []
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    y_coords.append(y) # Dusha sare waa High (Resistance)
                    y_coords.append(y + h) # Hoose waa Low (Support)
                
                if y_coords:
                    # Meesha ugu sarreysa ee sawirka ku taal ee mawjadda ah Resistance (H)
                    min_y = min(y_coords)
                    # Meesha ugu hooseysa ee mawjadda ah Support (L)
                    max_y = max(y_coords)
                    
                    resistance_h = f"Heerka Resistance (H): {min_y}px"
                    support_l = f"Heerka Support (L): {max_y}px"
            
            # 4. Go'aanka ku saleysan halka uu qiimaha ugu dambeeya ku dambeeyay (H mise L)
            if red_pixels > green_pixels:
                trend = "Bearish Structure (Suuqu wuxuu jebiyey Support-kii ama wuxuu ku socdaa L hoose)"
                signal = "SELL (Fursad Iibin)"
                reason = "Qiimuhu wuxuu cadaadis saarayaa dhinaca hoose (Low / Support Zone), taasoo muujinaysa jabitaan."
            else:
                trend = "Bullish Structure (Suuqu wuxuu dhisanayaa H sare iyo L kor u kacaya)"
                signal = "BUY (Fursad Iibsi)"
                reason = "Qiimuhu wuxuu ka soo lulmayaa Support-ka (L) oo wuxuu u jeedaa dhinaca Resistance-ka (H)."

            # 5. Natiijada
            st.markdown(f"### 📍 Falanqaynta Mawjadda & Heerarka:")
            st.write(f"- **{resistance_h}**")
            st.write(f"- **{support_l}**")
            st.write(f"- **Qaab-dhismeedka:** {trend}")
            
            st.markdown(f"### 🎯 Go'aanka Suuqa: **`{signal}`**")
            st.info(reason)
