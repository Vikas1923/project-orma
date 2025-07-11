import streamlit as st
from PIL import Image
import pytesseract
import re
from datetime import datetime, timedelta

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="Warranty Reminder POC", layout="centered")
st.title("🧾 Warranty Manager - AI-Based POC")
st.markdown("Upload your bill image. We'll extract the product info and send a WhatsApp-style reminder.")

uploaded_file = st.file_uploader("📤 Upload your product bill (jpg, jpeg, png)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Bill", use_column_width=True)

    # OCR Text Extraction
    extracted_text = pytesseract.image_to_string(image)
    st.subheader("📄 Extracted Text from Bill")
    st.text(extracted_text)

    # Try to extract product and date (basic rule-based method)
    product_match = re.search(r"(?:Product|Item|Model):?\s*(.+)", extracted_text, re.IGNORECASE)
    date_match = re.search(r"(?:Date|Purchase|Dated):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", extracted_text)

    if product_match and date_match:
        product = product_match.group(1).strip()
        raw_date = date_match.group(1).strip()
        
        # Try parsing multiple date formats
        try:
            purchase_date = datetime.strptime(raw_date, "%d-%m-%Y")
        except:
            purchase_date = datetime.strptime(raw_date, "%d/%m/%Y")

        # Assume 1-year warranty
        expiry_date = purchase_date + timedelta(days=365)

        st.success(f"🛍️ Product: {product}")
        st.info(f"🗓️ Purchase Date: {purchase_date.date()}")
        st.warning(f"⚠️ Warranty Expires On: {expiry_date.date()}")

        st.subheader("📲 WhatsApp-Style Reminder Message")
        reminder_msg = f"""
        🔔 *Warranty Reminder*

        Hi! This is a reminder that your *{product}* warranty will expire on *{expiry_date.date()}*.
        Don't miss out on your free service or repair. Reach out to your service center now!
        """
        st.code(reminder_msg)
    else:
        st.error("❌ Could not extract product name or purchase date. Try a clearer bill or format.")
