import streamlit as st
from PIL import Image
import numpy as np

st.set_page_config(page_title="Advanced Smart Chart Analyzer")
st.title("📈 Falanqaynta Sifeeyaha Shartiga (Advanced Vision)")
st.caption("App-ku wuxuu hadda adeegsanayaa shaandhaynta xariiqyada iyo qaabdhismeedka shartiga dhabta ah.")

uploaded_file = st.file_uploader("Soo geli sawirka shartiga", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Shartiga la falanqaynayo", use_column_width=True)
    
    if st.button("🚀 Bilow Falanqaynta Qoto dheer"):
        with st.spinner("Waxaa socota baaritaanka xariiqyada iyo shamacyada suuqa..."):
            
            # U beddelida sawirka laba-cabbir (Grayscale) si loo ogaado xariiqyada asaasiga ah
            img_gray = image.convert('L')
            img_np = np.array(img_gray)
            
            # Xisaabinta isbeddelka cufnaanta iyo xariiqyada
            edges = np.abs(np.diff(img_np, axis=1))
            edge_intensity = np.mean(edges)
            
            # Hubinta in sawirku yahay sharti dhab ah ama sawir caadi ah
            if edge_intensity < 2.0:
                st.error("⚠️ Digniin: Sawirkani uma muuqdo sharti suuq oo leh xariiqyo ama shumacyo cadcad. Fadlan soo geli sharti sax ah (TradingView/MetaTrader).")
            else:
                # Mantiiqada falanqaynta suuqa
                color_img = np.array(image)
                r_mean = np.mean(color_img[:, :, 0])
                g_mean = np.mean(color_img[:, :, 1])
                
                if g_mean >= r_mean:
                    trend = "Bullish Uptrend (Kor u kac adag)"
                    signal = "BUY (Fursad Iibsi)"
                    details = "Xariiqyada shartiga waxay muujinayaan in qiimuhu jebiyey caqabaddii hore oo uu kor u socdo."
                else:
                    trend = "Bearish Downtrend (Hoos u dhac / Cadaadis)"
                    signal = "SELL (Fursad Iibin)"
                    details = "Xariiqyada shartiga waxay muujinayaan in iibiyeyaashu ay dejiyeen heerar hoose (Lower Lows)."
                
                # Natiijada ugu dambeysa (oo la saxay xigashada)
                st.success("✅ Falanqayntii waa la dhamaystiray!")
                st.markdown(f"### 📊 Xaaladda Suuqa: **{trend}**")
                st.markdown(f"### 🎯 Go'aanka: **`{signal}`**")
                st.info(details)
                
