import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import os
import base64
from PIL import Image, ImageFilter
import numpy as np
import hashlib
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

import os

def send_verification_email(to_email, code):
    from_email = os.getenv("WELLNEST_EMAIL")
    app_password = os.getenv("WELLNEST_APP_PASSWORD")

    if not from_email or not app_password:
        st.error("Email credentials are not set in environment variables.")
        return False

    subject = "WellNest Verification Code"
    body = f"""
    <html>
    <body>
        <h2>Verify your email</h2>
        <p>Your verification code is:</p>
        <h1>{code}</h1>
        <p>Please enter this in the WellNest app to complete registration.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, app_password)
            server.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send verification email: {e}")
        return False

# Initialize session state

if "user" not in st.session_state:
    st.session_state.user = None
if "user_profile" not in st.session_state:
    st.session_state.user_profile = None
if "activity_log" not in st.session_state:
    st.session_state.activity_log = []
if "awarded_badges" not in st.session_state:
    st.session_state.awarded_badges = set()
if "new_badges_to_show" not in st.session_state:
    st.session_state.new_badges_to_show = []
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # "login" or "register"

st.set_page_config(page_title="WellNest - Health Tracker", layout="wide")

# Custom CSS styling with top header banner
st.markdown("""
    <style>
    /* Remove default streamlit padding */
    .main .block-container {
        padding-top: 0rem;
        max-width: 100%;
    }
    
    /* Top header banner */
    .header-banner {
        width: 100%;
        height: 200px;
        background: #282631;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: -1rem -1rem 2rem -1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .header-banner::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100" fill="white" opacity="0.1"><polygon points="0,0 1000,0 1000,100 0,80"/></svg>');
        background-size: cover;
    }
    
    .header-content {
        position: relative;
        z-index: 1;
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
    }
    
    /* Auth container styling */
    .auth-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem auto;
        max-width: 600px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
    }
    
    /* Auth tabs */
    .auth-tabs {
        display: flex;
        margin-bottom: 2rem;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .auth-tab {
        flex: 1;
        padding: 15px;
        text-align: center;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        background: #f8f9fa;
        color: #666;
    }
    
    .auth-tab.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Feature cards */
.feature-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    border-left: 5px solid #667eea;
    color: #333;  /* Add this line */
}

.feature-card h3 {  /* Add this entire rule */
    color: #667eea;
    margin-bottom: 1rem;
}

.feature-card p {  /* Add this entire rule */
    color: #666;
    line-height: 1.6;
}
    
    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
    background: #282631;
        font-family: 'Poppins', sans-serif;
    }
    
    section[data-testid="stSidebar"] .stTextInput > label,
    section[data-testid="stSidebar"] .stRadio > label,
    section[data-testid="stSidebar"] .stRadio span {
        font-size: 18px;
        font-weight: 600;
        color: white;
    }
    
    section[data-testid="stSidebar"] h1 {
        font-size: 30px;
        font-weight: 800;
        color: white;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        font-size: 20px !important;
        font-weight: bold !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

def create_header_banner():
    """Create the top header banner"""
    st.markdown("""
        <div class="header-banner">
            <div class="header-content">
                <div class="header-title">wellnest.</div>
                <div class="header-subtitle">Your Personal Health Tracking Dashboard</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def hash_password(password):
    """Hash password for storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def save_user_account(email, password, username, age, height, weight):
    """Save user account information"""
    users_file = "users.json"
    
    # Load existing users
    users = {}
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
        except:
            users = {}
    
    # Check if user already exists
    if email in users:
        return False, "User already exists"
    
    # Add new user
    users[email] = {
        "password_hash": hash_password(password),
        "username": username,
        "age": age,
        "height_cm": height,
        "weight_kg": weight,
        "bmi": calculate_bmi(weight, height),
        "registration_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        return True, "Account created successfully"
    except Exception as e:
        return False, f"Error saving account: {str(e)}"

def authenticate_user(email, password):
    """Authenticate user login"""
    users_file = "users.json"
    
    if not os.path.exists(users_file):
        return False, "No users found"
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        if email not in users:
            return False, "User not found"
        
        if verify_password(password, users[email]["password_hash"]):
            return True, users[email]
        else:
            return False, "Invalid password"
    except Exception as e:
        return False, f"Error authenticating: {str(e)}"

def get_user_profile_filename():
    """Generate user-specific profile filename"""
    if st.session_state.user:
        email = st.session_state.user['email'].replace('@', '_').replace('.', '_')
        return f"profile_{email}.csv"
    return "user_profile.csv"

def save_user_profile(profile_data):
    """Save user profile data to CSV file"""
    try:
        df = pd.DataFrame([profile_data])
        df.to_csv(get_user_profile_filename(), index=False)
        return True
    except Exception as e:
        st.error(f"Error saving profile: {str(e)}")
        return False

def load_user_profile():
    """Load user profile data from CSV file"""
    filename = get_user_profile_filename()
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            return df.iloc[0].to_dict() if len(df) > 0 else None
        return None
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")
        return None

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI from weight and height"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_bmi_category(bmi):
    """Get BMI category based on value"""
    if bmi < 18.5:
        return "Underweight", "🔵"
    elif bmi < 25:
        return "Normal weight", "🟢"
    elif bmi < 30:
        return "Overweight", "🟡"
    else:
        return "Obese", "🔴"

def get_user_filename():   
    """Generate user-specific filename"""
    if st.session_state.user:
        email = st.session_state.user['email'].replace('@', '_').replace('.', '_')
        return f"user_{email}.csv"
    return "user_activity_log.csv"

def save_user_data(df):
    """Save user data to CSV file"""
    try:
        df.to_csv(get_user_filename(), index=False)
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def load_user_data():
    """Load user data from CSV file"""
    filename = get_user_filename()
    try:
        if os.path.exists(filename):
            return pd.read_csv(filename, parse_dates=["date"])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")
        return pd.DataFrame()

def reset_user_data():
    """Reset user data by removing the file"""
    filename = get_user_filename()
    try:
        if os.path.exists(filename):
            os.remove(filename)
        st.session_state.activity_log = []
        return True
    except Exception as e:
        st.error(f"Error resetting data: {str(e)}")
        return False

@st.cache_data
def load_fitbit_data():
    """Load Fitbit dataset with error handling"""
    try:
        # Try to load actual files first
        activity_df = pd.read_csv("dailyActivity_merged.csv")
        intensity_df = pd.read_csv("dailyIntensities_merged.csv")
        sleep_df = pd.read_excel("sleepDay_merged.xlsx")

        activity_df["ActivityDate"] = pd.to_datetime(activity_df["ActivityDate"])
        intensity_df["ActivityDay"] = pd.to_datetime(intensity_df["ActivityDay"])
        sleep_df["SleepDay"] = pd.to_datetime(sleep_df["SleepDay"])

        activity_df = activity_df.rename(columns={"ActivityDate": "date", "TotalSteps": "steps", "Calories": "calories"})
        intensity_df = intensity_df.rename(columns={"ActivityDay": "date"})
        sleep_df = sleep_df.rename(columns={"SleepDay": "date"})
        sleep_df["sleep_hours"] = sleep_df["TotalMinutesAsleep"] / 60

        merged_df = pd.merge(activity_df, sleep_df[["Id", "date", "sleep_hours"]], on=["Id", "date"], how="left")
        merged_df = merged_df[merged_df["sleep_hours"].notna() & (merged_df["sleep_hours"] > 0)]

        return merged_df, intensity_df, sleep_df

    except FileNotFoundError:
        # Generate sample data if files don't exist
        st.warning("⚠️ Fitbit data files not found. Using sample data for demonstration.")
        return generate_sample_data()
    except Exception as e:
        st.error(f"Error loading Fitbit data: {str(e)}")
        return generate_sample_data()

def generate_sample_data():
    """Generate sample data for demonstration"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
    n_days = len(dates)
    
    # Generate realistic sleep hours (6-9 hours mostly, centered around 7.5)
    np.random.seed(42)  # For consistent results
    sleep_hours = np.random.normal(7.5, 1.0, n_days)  # Normal distribution around 7.5h
    sleep_hours = np.clip(sleep_hours, 5.0, 10.0)  # Keep within reasonable bounds (5-10 hours)
    
    # Generate realistic steps (most people do 6000-12000 steps)
    steps = np.random.normal(8500, 2000, n_days)
    steps = np.clip(steps, 3000, 15000).astype(int)
    
    # Generate realistic calories (based on steps and baseline metabolism)
    baseline_calories = np.random.normal(1800, 200, n_days)  # Base metabolic rate
    activity_calories = steps * 0.04  # Roughly 0.04 calories per step
    total_calories = baseline_calories + activity_calories
    total_calories = np.clip(total_calories, 1500, 3500).astype(int)
    
    # Sample activity data
    activity_df = pd.DataFrame({
        'Id': [1] * n_days,
        'date': dates,
        'steps': steps,
        'calories': total_calories,
        'sleep_hours': sleep_hours
    })
    
    # Sample intensity data (should add up to roughly 24 hours = 1440 minutes)
    intensity_df = pd.DataFrame({
        'Id': [1] * n_days,
        'date': dates,
        'SedentaryMinutes': np.random.randint(600, 900, n_days),  # 10-15 hours sedentary
        'LightlyActiveMinutes': np.random.randint(180, 300, n_days),  # 3-5 hours light activity
        'FairlyActiveMinutes': np.random.randint(15, 60, n_days),  # 15-60 minutes moderate
        'VeryActiveMinutes': np.random.randint(0, 45, n_days)  # 0-45 minutes intense
    })
    
    # Sample sleep data (should match activity_df sleep_hours)
    sleep_df = pd.DataFrame({
        'Id': [1] * n_days,
        'date': dates,
        'sleep_hours': sleep_hours,
        'TotalMinutesAsleep': (sleep_hours * 60).astype(int)  # Convert hours to minutes
    })
    
    return activity_df, intensity_df, sleep_df

def check_new_badges(df):
    """Check for new badge achievements"""
    new_badges = []

    if any(df["steps"] >= 10000) and "🥈 Step Champ" not in st.session_state.awarded_badges:
        new_badges.append("🥈 Step Champ")

    if any(df["sleep_hours"] >= 8) and "🥇 Sleeper Pro" not in st.session_state.awarded_badges:
        new_badges.append("🥇 Sleeper Pro")

    if df.shape[0] > 0 and "🥉 First Step" not in st.session_state.awarded_badges:
        new_badges.append("🥉 First Step")

    # Check for consistency streak
    if len(df) >= 7:
        dates = sorted(df["date"].dt.date.unique())
        streak_count = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                streak_count += 1
                if streak_count >= 7 and "🔥 Consistency" not in st.session_state.awarded_badges:
                    new_badges.append("🔥 Consistency")
                    break
            else:
                streak_count = 1

    # Update session state
    if new_badges:
        for badge in new_badges:
            st.session_state.awarded_badges.add(badge)
        st.session_state.new_badges_to_show = new_badges.copy()

def validate_inputs(steps, calories, sleep_hours):
    """Validate user inputs"""
    errors = []
    
    if steps < 0:
        errors.append("Steps cannot be negative")
    if steps > 50000:
        errors.append("Steps seem unusually high (>50,000)")
    
    if calories < 0:
        errors.append("Calories cannot be negative")
    if calories > 10000:
        errors.append("Calories seem unusually high (>10,000)")
    
    if sleep_hours < 0:
        errors.append("Sleep hours cannot be negative")
    if sleep_hours > 24:
        errors.append("Sleep hours cannot exceed 24")
    
    return errors

def log_activity_and_check_badges(activity_date, steps, calories, sleep_hours):
    """Log activity with validation and badge checking"""
    # Validate inputs
    errors = validate_inputs(steps, calories, sleep_hours)
    if errors:
        for error in errors:
            st.error(error)
        return False
    
    # Check for duplicate entries
    existing_dates = [entry['date'] for entry in st.session_state.activity_log]
    if activity_date in existing_dates:
        st.warning("An entry for this date already exists. Please delete it first or choose a different date.")
        return False
    
    new_log = {
        "date": activity_date,
        "steps": int(steps),
        "calories": int(calories),
        "sleep_hours": float(sleep_hours)
    }
    st.session_state.activity_log.append(new_log)

    df = pd.DataFrame(st.session_state.activity_log)
    df["date"] = pd.to_datetime(df["date"])

    if save_user_data(df):
        check_new_badges(df)
        
        # Show achievement toasts
        if st.session_state.get("new_badges_to_show"):
            for badge in st.session_state.new_badges_to_show:
                st.toast(f"🎉 Achievement Unlocked: {badge}")
            st.session_state.new_badges_to_show.clear()
        
        st.success("Activity logged successfully!")
        return True
    return False

# Create header banner
create_header_banner()

# LOGIN/REGISTER SYSTEM
if not st.session_state.user:    
    # Tab selection
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", key="login-tab", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("👤 Create Account", key="register-tab", use_container_width=True):
            st.session_state.auth_mode = "register"
            st.rerun()
        
    if st.session_state.auth_mode == "login":
        st.markdown("### Welcome Back!")
        st.markdown("Please login to access your health dashboard.")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email address")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submitted:
                if not all([email, password]):
                    st.error("Please fill in all fields.")
                else:
                    success, result = authenticate_user(email, password)
                    if success:
                        st.session_state.user = {"email": email}
                        st.session_state.user_profile = result
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result)  # This will show "User not found" or "Invalid password"

    
    elif st.session_state.auth_mode == "verify":
        st.markdown("### Email Verification")
        st.markdown("Please check your email for the 6-digit code we sent.")
    
        # Check if code has expired
        if st.session_state.code_expires_at and datetime.now() > st.session_state.code_expires_at:
            st.error("Verification code has expired. Please request a new one.")
            code_expired = True
        else:
            code_expired = False
            # Show countdown timer
            if st.session_state.code_expires_at:
                time_left = st.session_state.code_expires_at - datetime.now()
                minutes_left = int(time_left.total_seconds() // 60)
                seconds_left = int(time_left.total_seconds() % 60)
                st.info(f"Code will expires in: {minutes_left}:{seconds_left:02d}")

        code_input = st.text_input("Enter Verification Code", max_chars=6, disabled=code_expired)

        if st.button("Verify Code", disabled=code_expired):
            if code_input == st.session_state.verification_code:
                    if "pending_registration" not in st.session_state:
                        st.error("Missing registration information. Please try again.")
                        st.session_state.auth_mode = "register"
                        st.rerun()
                    else:
                        info = st.session_state.pending_registration
                        success, message = save_user_account(
                            info["email"], info["password"], info["username"],
                            info["age"], info["height"], info["weight"]
                        )
                        if success:
                            st.success("Account created successfully! You can now login.")
                            st.session_state.auth_mode = "login"
                            # Clean up verification data
                            for key in ["verification_code", "pending_registration", "code_expires_at", "last_code_sent_at", "verification_target"]:
                                st.session_state.pop(key, None)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.error("Incorrect code. Please check your email and try again.")

        # Resend code logic with cooldown
        can_resend = True
        if st.session_state.last_code_sent_at:
            time_since_last = datetime.now() - st.session_state.last_code_sent_at
            if time_since_last.total_seconds() < 60:  # 60 second cooldown
                can_resend = False
                seconds_left = 60 - int(time_since_last.total_seconds())
                resend_text = f"Resend Code ({seconds_left}s)"
            else:
                resend_text = "Resend Code"
        else:
            resend_text = "Resend Code"

        if st.button(resend_text, disabled=not can_resend):
            new_code = str(random.randint(100000, 999999))
            st.session_state.verification_code = new_code
            st.session_state.code_expires_at = datetime.now() + timedelta(minutes=10)
            st.session_state.last_code_sent_at = datetime.now()
            if send_verification_email(st.session_state.verification_target, new_code):
                st.success("New code sent. Check your inbox.")
                st.rerun()

    
    else:  # Register mode
        st.markdown("### 👤 Create Your Account")
        st.markdown("Join WellNest and start tracking your health journey!")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)

            with col1:
                email = st.text_input("Email", value=st.session_state.get("email_input", ""), placeholder="Enter your email address")
                username = st.text_input("Username", value=st.session_state.get("username_input", ""), placeholder="Enter your name")
                password = st.text_input("Password", type="password", placeholder="Create a password")

            with col2:
                age = st.number_input("Age", min_value=1, max_value=120, value=25)
                height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
                weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.1)

            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            st.session_state.email_input = email
            st.session_state.username_input = username  
            st.session_state.password_input = password
            st.session_state.confirm_password_input = confirm_password
            st.session_state.age_input = age
            st.session_state.height_input = height
            st.session_state.weight_input = weight

            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if not all([email, username, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif not email.endswith("@gmail.com") or email.count("@") != 1:
                st.error("Please enter a valid Gmail address.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                verification_code = str(random.randint(100000, 999999))
                st.session_state.verification_code = verification_code
                st.session_state.verification_target = email
                st.session_state.pending_registration = {
                    "email": email,
                    "username": username,
                    "password": password,
                    "age": age,
                    "height": height,
                    "weight": weight
                }

                if send_verification_email(email, verification_code):
                    st.success("Verification code sent to your email!")
                    st.session_state.auth_mode = "verify"
                    st.rerun()
                else:
                    st.error("Unable to send verification code.")

                        
    
    # Features section
    st.markdown("---")
    st.markdown("## Why Choose WellNest?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>Track Everything</h3>
            <p>Monitor your daily steps, calories burned, and sleep patterns all in one place.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>Earn Achievements</h3>
            <p>Stay motivated with our badge system and track your progress over time.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>Visual Insights</h3>
            <p>Beautiful charts and comparisons to understand your health trends.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# MAIN APPLICATION
# Load Fitbit data
fitbit_df, intensity_df, sleep_df = load_fitbit_data()

# Load user activity data
activity_data = load_user_data()
if not activity_data.empty:
    st.session_state.activity_log = activity_data.to_dict("records")

# Sidebar
logo_path =  "logo.jpg"
with st.sidebar:
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            st.image(logo, use_container_width=True)
        except Exception as e:
            st.write("WELLNEST")
    else:
        st.markdown("## WellNest")

    st.markdown(f"### Welcome, {st.session_state.user_profile['username'] if st.session_state.user_profile else 'User'}! 👋")
    
    page = st.radio("Navigate", ["User Profile", "Activity Logger", "Health Insights", "Compare with Fitbit"])
    st.sidebar.markdown("---")

    if st.sidebar.button("Log out"):
        st.session_state.user = None
        st.session_state.user_profile = None
        st.session_state.activity_log = []
        st.session_state.awarded_badges = set()
        st.session_state.new_badges_to_show = []
        st.rerun()


if page == "User Profile":
    st.title("USER PROFILE")

    if st.session_state.user and st.session_state.user_profile:
        profile = st.session_state.user_profile
        
        # Profile Header
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### Welcome, {profile['username']}! 👋")
            
            # Basic Info
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**Email:** {st.session_state.user['email']}")
                st.markdown(f"**Age:** {profile['age']} years")
                st.markdown(f"**Member Since:** {profile.get('registration_date', 'N/A')}")
            
            with info_col2:
                st.markdown(f"**Height:** {profile['height_cm']} cm")
                st.markdown(f"**Weight:** {profile['weight_kg']} kg")
                
                # BMI Calculation and Display
                bmi = profile['bmi']
                bmi_category, bmi_emoji = get_bmi_category(bmi)
                st.markdown(f"**BMI:** {bmi:.1f} ({bmi_category}) {bmi_emoji}")
        
        with col2:
            # Edit Profile Button
            if st.button("Edit Profile", type="secondary"):
                st.session_state.show_edit_profile = True
            
            # Achievements section
            if st.session_state.awarded_badges:
                st.markdown("### Achievements")
                for badge in st.session_state.awarded_badges:
                    st.markdown(f"- {badge}")
            else:
                st.info("No achievements yet. Start logging activities!")
        
        # Edit Profile Form (shows when edit button is clicked)
        if st.session_state.get("show_edit_profile", False):
            st.markdown("---")
            st.markdown("### Edit Your Profile")
            
            with st.form("edit_profile_form"):
                edit_col1, edit_col2 = st.columns(2)
                
                with edit_col1:
                    new_username = st.text_input("Username", value=profile['username'])
                    new_age = st.number_input("Age", min_value=1, max_value=120, value=profile['age'])
                    new_height = st.number_input("Height (cm)", min_value=50, max_value=250, value=profile['height_cm'])
                
                with edit_col2:
                    new_weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, value=profile['weight_kg'], step=0.1)
                
                update_col1, update_col2 = st.columns(2)
                with update_col1:
                    if st.form_submit_button("✅ Update Profile", type="primary"):
                        # Update profile data
                        updated_profile = profile.copy()
                        updated_profile.update({
                            "username": new_username,
                            "age": new_age,
                            "height_cm": new_height,
                            "weight_kg": new_weight,
                            "bmi": calculate_bmi(new_weight, new_height)
                        })
                        
                        st.session_state.user_profile = updated_profile
                        st.session_state.user["username"] = new_username
                        
                        # Update in users.json as well
                        users_file = "users.json"
                        if os.path.exists(users_file):
                            try:
                                with open(users_file, 'r') as f:
                                    users = json.load(f)
                                users[st.session_state.user['email']].update({
                                    "username": new_username,
                                    "age": new_age,
                                    "height_cm": new_height,
                                    "weight_kg": new_weight,
                                    "bmi": calculate_bmi(new_weight, new_height)
                                })
                                with open(users_file, 'w') as f:
                                    json.dump(users, f, indent=2)
                            except:
                                pass
                        
                        st.success("Profile updated successfully! 🎉")
                        st.session_state.show_edit_profile = False
                        st.rerun()
                
                with update_col2:
                    if st.form_submit_button("❌ Cancel"):
                        st.session_state.show_edit_profile = False
                        st.rerun()
        
        # Health Insights based on profile
        st.markdown("---")
        st.markdown("### Personalized Health Insights")
        
        if st.session_state.activity_log:
            df = pd.DataFrame(st.session_state.activity_log)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # Health metrics based on profile
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Entries", len(df))
            with col2:
                avg_steps = df['steps'].mean()
                st.metric("Avg Steps", f"{int(avg_steps):,}")
            with col3:
                avg_calories = df['calories'].mean()
                st.metric("Avg Calories", f"{int(avg_calories)}")
            with col4:
                avg_sleep = df['sleep_hours'].mean()
                st.metric("Avg Sleep", f"{avg_sleep:.1f}h")

            # Personalized recommendations based on age and BMI
            st.markdown("### 💡 Personalized Recommendations")
            
            recommendations = []
            
            # Age-based recommendations
            if profile['age'] < 18:
                recommendations.append("🧒 As a young person, aim for 8-10 hours of sleep and stay active with sports!")
            elif profile['age'] > 65:
                recommendations.append("👴 Focus on gentle exercises like walking and maintain 7-8 hours of sleep.")
            else:
                recommendations.append("💪 Aim for 150 minutes of moderate exercise per week and 7-9 hours of sleep.")
            
            # BMI-based recommendations
            if bmi < 18.5:
                recommendations.append("🍎 Consider consulting a nutritionist to reach a healthy weight.")
            elif bmi > 25:
                recommendations.append("🏃 Focus on increasing daily steps and reducing caloric intake.")
            else:
                recommendations.append("✅ Great job maintaining a healthy BMI! Keep up the good work!")
            
            # Activity-based recommendations
            if avg_steps < 8000:
                recommendations.append("👣 Try to increase your daily steps - aim for at least 8,000 steps per day.")
            if avg_sleep < 7:
                recommendations.append("😴 Consider improving your sleep hygiene to get 7-9 hours per night.")
            
            for rec in recommendations:
                st.info(rec)

            # Trends section (existing code)
            st.markdown("### Trend Analysis")
            if len(df) >= 6:
                recent = df.iloc[-3:].mean(numeric_only=True)
                previous = df.iloc[-6:-3].mean(numeric_only=True)

                trend_col1, trend_col2, trend_col3 = st.columns(3)
                
                with trend_col1:
                    steps_change = recent['steps'] - previous['steps']
                    st.metric("Steps Trend", f"{recent['steps']:.0f}", f"{steps_change:+.0f}")
                
                with trend_col2:
                    cal_change = recent['calories'] - previous['calories']
                    st.metric("Calories Trend", f"{recent['calories']:.0f}", f"{cal_change:+.0f}")
                
                with trend_col3:
                    sleep_change = recent['sleep_hours'] - previous['sleep_hours']
                    st.metric("Sleep Trend", f"{recent['sleep_hours']:.1f}h", f"{sleep_change:+.1f}h")
            else:
                st.info("Log more activities to see trend analysis (minimum 6 entries needed)")
        else:
            st.info("Start logging your daily activities to see personalized insights!")
    
    else:
        st.error("Profile data not found. Please log out and create your account again.")

elif page == "Activity Logger":
    st.title("ACTIVITY LOGGER")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Select Date")
        
        col_month, col_day, col_year = st.columns([2, 1, 1])
        
        with col_month:
            selected_month = st.selectbox("Month", 
                                        options=list(range(1, 13)),
                                        format_func=lambda x: datetime(2023, x, 1).strftime('%B'),
                                        index=datetime.today().month - 1)
        with col_day:
            max_day = 31
            if selected_month in [4, 6, 9, 11]:
                max_day = 30
            elif selected_month == 2:
                max_day = 29
            
            selected_day = st.selectbox("Day", 
                                      options=list(range(1, max_day + 1)),
                                      index=min(datetime.today().day - 1, max_day - 1))
        with col_year:
            selected_year = st.selectbox("Year", 
                                       options=list(range(2020, 2030)),
                                       index=list(range(2020, 2030)).index(datetime.today().year))
        
        try:
            activity_date = datetime(selected_year, selected_month, selected_day).date()
            st.success(f"Selected: {activity_date.strftime('%B %d, %Y')}")
        except ValueError:
            st.error("❌ Invalid date selected!")
            activity_date = datetime.today().date()
    
    with col2:
        st.markdown("### Activity Details")
        steps = st.number_input("👣 Steps Walked", min_value=0, max_value=50000, value=0, step=100)
        calories = st.number_input("🔥 Calories Burned", min_value=0, max_value=10000, value=0, step=50)
        sleep_hours = st.number_input("😴 Hours Slept", min_value=0.0, max_value=24.0, value=0.0, step=0.5)
        
        st.markdown("---")
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("Log Activity", type="primary", use_container_width=True):
                log_activity_and_check_badges(activity_date, steps, calories, sleep_hours)

        with btn_col2:
            if st.button("Reset All Data", use_container_width=True):
                if reset_user_data():
                    st.success("All data has been reset!")
                    st.rerun()

    # Display logged activities
    if st.session_state.activity_log:
        user_df = pd.DataFrame(st.session_state.activity_log)
        user_df["date"] = pd.to_datetime(user_df["date"])
        user_df = user_df.sort_values("date", ascending=False)

        st.markdown("---")
        st.subheader("Your Activity History")
        
        # Display data
        st.dataframe(user_df, use_container_width=True)

        # Charts
        st.markdown("### Your Progress Charts")
        chart_col1, chart_col2, chart_col3 = st.columns(3)
        
        with chart_col1:
            st.altair_chart(
                alt.Chart(user_df).mark_line(color="green", strokeWidth=3).encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("steps:Q", title="Steps"),
                    tooltip=["date", "steps"]
                ).properties(title="Steps Over Time", width=200, height=200),
                use_container_width=True
            )

        with chart_col2:
            st.altair_chart(
                alt.Chart(user_df).mark_area(color="orange", opacity=0.7).encode(
                    x=alt.X("date:T", title="Date"), 
                    y=alt.Y("calories:Q", title="Calories"),
                    tooltip=["date", "calories"]
                ).properties(title="Calories Burned", width=200, height=200),
                use_container_width=True
            )

        with chart_col3:
            st.altair_chart(
                alt.Chart(user_df).mark_bar(color="blue").encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("sleep_hours:Q", title="Sleep Hours"),
                    tooltip=["date", "sleep_hours"]
                ).properties(title="Sleep Hours", width=200, height=200),
                use_container_width=True
            )

elif page == "Health Insights":
    st.title("HEALTH INSIGHTS")
    st.markdown("*Based on fitness tracker data analysis*")

    # Summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Steps", f"{int(fitbit_df['steps'].mean()):,}")
    with col2:
        st.metric("Average Calories", f"{int(fitbit_df['calories'].mean())}")
    with col3:
        st.metric("Average Sleep", f"{sleep_df['sleep_hours'].mean():.1f} hrs")

    # Charts
    st.markdown("### Population Trends")
    
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.altair_chart(
            alt.Chart(fitbit_df.sample(min(100, len(fitbit_df)))).mark_line(strokeWidth=2).encode(
                x=alt.X('date:T', title="Date"), 
                y=alt.Y('steps:Q', title="Steps"),
                tooltip=["date", "steps"]
            ).properties(title="Steps Trend Over Time"),
            use_container_width=True
        )

    with row1_col2:
        st.altair_chart(
            alt.Chart(sleep_df.sample(min(100, len(sleep_df)))).mark_circle(size=60, color='skyblue').encode(
                x=alt.X('date:T', title="Date"),
                y=alt.Y('sleep_hours:Q', title="Sleep Hours"),
                tooltip=["date", "sleep_hours"]
            ).properties(title="Sleep Patterns"),
            use_container_width=True
        )

elif page == "Compare with Fitbit":
    st.title("🔍 COMPARE WITH POPULATION DATA")
    
    if not st.session_state.activity_log:
        st.info("Log some activities first to enable comparison with population data!")
    else:
        user_df = pd.DataFrame(st.session_state.activity_log)
        user_avg = user_df.mean(numeric_only=True)
        # Cleaned average values
        fitbit_avg = pd.Series({
            "steps": fitbit_df["steps"].mean(),
            "calories": fitbit_df["calories"].mean(),
            "sleep_hours": fitbit_df[fitbit_df["sleep_hours"] > 0]["sleep_hours"].mean()
        })


        st.markdown("### Your Performance vs. Population Average")
        
        # Comparison metrics with improved messaging
        col1, col2, col3 = st.columns(3)

        with col1:
            pop_avg_steps = int(fitbit_avg["steps"])
            user_steps = int(user_avg["steps"])
            steps_diff = user_steps - pop_avg_steps
            steps_diff_pct = (steps_diff / pop_avg_steps) * 100
            
            if steps_diff_pct > 10:
                steps_msg = f"📈 {steps_diff_pct:+.0f}% above average - Excellent! 🎉"
                steps_color = "normal"
            elif steps_diff_pct > -10:
                steps_msg = f"📊 {steps_diff_pct:+.0f}% - Right on target! ✅"
                steps_color = "normal"
            else:
                steps_msg = f"📉 {steps_diff_pct:+.0f}% - Room for improvement! 💪"
                steps_color = "inverse"
            
            st.metric("Your Avg Steps", f"{user_steps:,}", 
                     f"Pop avg: {pop_avg_steps:,}", 
                     delta_color=steps_color)
            st.caption(steps_msg)

        with col2:
            pop_avg_cal = int(fitbit_avg["calories"])
            user_cal = int(user_avg["calories"])
            cal_diff = user_cal - pop_avg_cal
            cal_diff_pct = (cal_diff / pop_avg_cal) * 100
            
            if cal_diff_pct > 10:
                cal_msg = f"🔥 {cal_diff_pct:+.0f}% above average - Great activity! ⭐"
                cal_color = "normal"
            elif cal_diff_pct > -10:
                cal_msg = f"⚖️ {cal_diff_pct:+.0f}% - Well balanced! ✅"
                cal_color = "normal"
            else:
                cal_msg = f"📈 {cal_diff_pct:+.0f}% - Try more activities! 🏃"
                cal_color = "inverse"
            
            st.metric("Your Avg Calories", f"{user_cal:,}", 
                     f"Pop avg: {pop_avg_cal:,}",
                     delta_color=cal_color)
            st.caption(cal_msg)

        with col3:
            pop_avg_sleep = fitbit_avg["sleep_hours"]
            user_sleep = user_avg["sleep_hours"]
            sleep_diff = user_sleep - pop_avg_sleep
            sleep_diff_pct = (sleep_diff / pop_avg_sleep) * 100
            
            if user_sleep >= 7.5:
                sleep_msg = f"😴 {sleep_diff_pct:+.0f}% - Great sleep habits! 🌟"
                sleep_color = "normal"
            elif user_sleep >= 6.5:
                sleep_msg = f"😊 {sleep_diff_pct:+.0f}% - Good sleep! ✅"
                sleep_color = "normal"
            else:
                sleep_msg = f"😪 {sleep_diff_pct:+.0f}% - Need more rest! 💤"
                sleep_color = "inverse"
            
            pop_avg_sleep = fitbit_avg["sleep_hours"]
            user_sleep = user_avg["sleep_hours"]
            sleep_diff = user_sleep - pop_avg_sleep

            # Avoid division by zero or tiny values
            if pop_avg_sleep < 0.5:
                sleep_diff_pct = 0
            else:
                sleep_diff_pct = (sleep_diff / pop_avg_sleep) * 100 if pop_avg_sleep > 0.5 else 0

            # Determine text + color
            if user_sleep >= 7.5:
                sleep_msg = f"😴 <span style='color:green'>{sleep_diff_pct:+.0f}%</span> - Great sleep habits! 🌟"
                sleep_color = "normal"
            elif user_sleep >= 6.5:
                sleep_msg = f"😊 <span style='color:gray'>{sleep_diff_pct:+.0f}%</span> - Good sleep! ✅"
                sleep_color = "normal"
            else:
                sleep_msg = f"😪 <span style='color:red'>{sleep_diff_pct:+.0f}%</span> - Need more rest! 💤"
                sleep_color = "inverse"

            st.metric("Your Avg Sleep", f"{user_sleep:.1f}h", 
                    f"Pop avg: {pop_avg_sleep:.1f}h",
                    delta_color=sleep_color)
            st.caption(sleep_msg, unsafe_allow_html=True)


        # Performance insights
        st.markdown("### 📊 Performance Insights")
        
        insights = []
        
        # Steps insights
        if user_steps >= 10000:
            insights.append("🎯 **Steps**: Excellent! You're hitting the recommended 10,000+ steps daily.")
        elif user_steps >= 8000:
            insights.append("👍 **Steps**: Good progress! You're close to the 10,000 step goal.")
        else:
            insights.append("💪 **Steps**: Try to increase your daily walking - aim for 8,000-10,000 steps.")
        
        # Calories insights
        if user_cal >= 2200:
            insights.append("🔥 **Calories**: High activity level! Great job staying active.")
        elif user_cal >= 1800:
            insights.append("⚖️ **Calories**: Moderate activity level - well balanced lifestyle.")
        else:
            insights.append("📈 **Calories**: Consider adding more physical activities to your routine.")
        
        # Sleep insights
        if user_sleep >= 8:
            insights.append("😴 **Sleep**: Excellent sleep habits! You're well-rested.")
        elif user_sleep >= 7:
            insights.append("✅ **Sleep**: Good sleep duration - within healthy range.")
        else:
            insights.append("💤 **Sleep**: Try to get 7-9 hours of sleep for optimal health.")
        
        for insight in insights:
            st.info(insight)

        # Comparison charts - Side by side
        st.markdown("### 📈 Visual Comparison")
        
        # Create two columns for side-by-side charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### 👤 Your Activity Data")
            
            # Prepare your data for visualization
            user_chart_data = pd.DataFrame({
                "Metric": ["Steps", "Calories", "Sleep Hours"],
                "Value": [user_avg["steps"], user_avg["calories"], user_avg["sleep_hours"]],
                "Color": ["#667eea", "#667eea", "#667eea"]
            })
            
            # Your data chart
            user_chart = alt.Chart(user_chart_data).mark_bar(
                color="#667eea",
                strokeWidth=2,
                stroke="#5a67d8"
            ).encode(
                x=alt.X("Metric:N", title="Metrics", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Value:Q", title="Average Value"),
                tooltip=["Metric:N", alt.Tooltip("Value:Q", format=".1f")]
            ).properties(
                width=300,
                height=400,
                title=alt.TitleParams(
                    text="Your Averages",
                    fontSize=16,
                    fontWeight="bold"
                )
            )
            
            st.altair_chart(user_chart, use_container_width=True)
        
        with chart_col2:
            st.markdown("#### 👥 Population Average Data")
            
            # Prepare population data for visualization
            pop_chart_data = pd.DataFrame({
                "Metric": ["Steps", "Calories", "Sleep Hours"],
                "Value": [fitbit_avg["steps"], fitbit_avg["calories"], fitbit_avg["sleep_hours"]],
                "Color": ["#764ba2", "#764ba2", "#764ba2"]
            })
            
            # Population data chart
            pop_chart = alt.Chart(pop_chart_data).mark_bar(
                color="#764ba2",
                strokeWidth=2,
                stroke="#6b46c1"
            ).encode(
                x=alt.X("Metric:N", title="Metrics", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Value:Q", title="Average Value"),
                tooltip=["Metric:N", alt.Tooltip("Value:Q", format=".1f")]
            ).properties(
                width=300,
                height=400,
                title=alt.TitleParams(
                    text="Population Averages", 
                    fontSize=16,
                    fontWeight="bold"
                )
            )
            
            st.altair_chart(pop_chart, use_container_width=True)
        
        # Additional health recommendations
        st.markdown("### 💡 Personalized Recommendations")
        
        recommendations = []
        
        # Based on comparison with population
        if user_steps < pop_avg_steps * 0.8:
            recommendations.append("🚶 **Increase Daily Steps**: Try taking stairs, parking farther away, or walking meetings.")
        
        if user_sleep < 7:
            recommendations.append("😴 **Improve Sleep**: Establish a bedtime routine and aim for 7-9 hours nightly.")
        
        if user_cal < pop_avg_cal * 0.8:
            recommendations.append("🏃 **Boost Activity**: Add 20-30 minutes of exercise to your daily routine.")
        
        # Positive reinforcement
        if user_steps > pop_avg_steps:
            recommendations.append("🎉 **Keep It Up**: Your step count is above average - maintain this great habit!")
        
        if user_sleep >= 7.5:
            recommendations.append("🌟 **Sleep Champion**: Excellent sleep habits - you're setting a great example!")
        
        if not recommendations:
            recommendations.append("✅ **Well Balanced**: You're maintaining good health habits across all metrics!")
        
        for rec in recommendations:
            st.success(rec)