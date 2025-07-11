import streamlit as st
from PIL import Image
import pytesseract
import re
from datetime import datetime, timedelta
import pdf2image
import io
import sqlite3
import hashlib
import validators

# Move these functions to the top of the file, after the imports and before the authentication code
def validate_email(email):
    """
    Email must:
    - Be properly formatted
    - Not contain certain special characters
    - Have a valid domain structure
    """
    if not validators.email(email):
        return False, "Invalid email format"
    
    # Additional checks for common issues
    if len(email) > 254:  # Maximum length for email addresses
        return False, "Email is too long"
    
    if re.search(r'[<>"\']', email):
        return False, "Email contains invalid characters"
    
    return True, "Email is valid"

def validate_password(password):
    """
    Password must:
    - Be at least 8 characters long
    - Contain at least one uppercase letter
    - Contain at least one lowercase letter
    - Contain at least one number
    - Contain at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

# Add this at the beginning of your file, after imports
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (email TEXT PRIMARY KEY, 
                  password TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  phone TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def create_user(email, password, first_name, last_name, phone):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password, first_name, last_name, phone) VALUES (?, ?, ?, ?, ?)",
                 (email, hash_password(password), first_name, last_name, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# Initialize the database
init_db()

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Add this before your existing page config
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🧾 Project ORMA - Authentication")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if not all([login_email, login_password]):
                st.error("Please enter both email and password")
            else:
                email_valid, _ = validate_email(login_email)
                if not email_valid:
                    st.error("Invalid email format")
                elif login_user(login_email, login_password):
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    with tab2:
        st.subheader("Sign Up")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        phone = st.text_input("Phone Number")
        
        # Add password requirements info
        st.info("""Password Requirements:
        - At least 8 characters long
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character (!@#$%^&*(),.?":{}|<>)
        """)
        
        if st.button("Sign Up"):
            if not all([new_email, new_password, first_name, last_name, phone]):
                st.error("All fields are required")
            else:
                # Validate email
                email_valid, email_msg = validate_email(new_email)
                if not email_valid:
                    st.error(email_msg)
                    st.stop()
                
                # Validate password
                password_valid, password_msg = validate_password(new_password)
                if not password_valid:
                    st.error(password_msg)
                    st.stop()
                
                # Check if passwords match
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    st.stop()
                
                # Validate phone number (basic check)
                if not re.match(r'^\+?1?\d{9,15}$', phone):
                    st.error("Please enter a valid phone number")
                    st.stop()
                
                # Try to create user
                if create_user(new_email, new_password, first_name, last_name, phone):
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Email already registered")

else:
    # Add logout button
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
        
    # Your existing app code starts here
    st.title("🧾 Project ORMA - POC")
    st.markdown("Upload your bill image/PDF or take a photo. We'll extract the product info and send a WhatsApp-style reminder.")

    # Input method selection
    input_method = st.radio("Choose input method:", ["Upload File", "Take Photo"])

    if input_method == "Upload File":
        uploaded_file = st.file_uploader("📤 Upload your product bill", type=["jpg", "jpeg", "png", "pdf"])
        
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                # Convert PDF to image
                pdf_pages = pdf2image.convert_from_bytes(uploaded_file.read())
                image = pdf_pages[0]  # Taking first page only
                st.image(image, caption="Uploaded PDF (First Page)", use_column_width=True)
            else:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Bill", use_column_width=True)

    elif input_method == "Take Photo":
        camera_image = st.camera_input("📸 Take a photo of your bill")
        
        if camera_image:
            image = Image.open(camera_image)
            st.image(image, caption="Captured Bill", use_column_width=True)

    # Process image if available (either from upload or camera)
    if 'image' in locals():
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
                try:
                    purchase_date = datetime.strptime(raw_date, "%d/%m/%Y")
                except:
                    st.error("❌ Could not parse the date format. Please ensure date is in DD-MM-YYYY or DD/MM/YYYY format.")
                    st.stop()

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
