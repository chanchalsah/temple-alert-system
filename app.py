import streamlit as st
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000"  # FastAPI backend

st.set_page_config(page_title="Temple Alert System Dashboard", layout="wide")
st.title("Temple Alert System Dashboard")

# ----------------------------
# Latest Alerts
# ----------------------------
st.header("Latest Alerts")
try:
    response = requests.get(f"{API_URL}/alerts")
    response.raise_for_status()
    alerts = response.json()  # Backend returns a list
    for alert in alerts:
        # Skip dummy placeholders
        if alert["zone"] == "string":
            continue

        # Highlight based on severity
        severity = alert.get("severity", "").upper()
        message = f"Zone: {alert['zone']} | Type: {alert['type']}\n{alert['message']}"

        if severity == "RED":
            st.error(message)  # Red box
        elif severity == "ORANGE":
            st.warning(message)  # Orange box
        elif severity == "YELLOW":
            st.info(message)  # Yellow/info box
        else:
            st.info(message)  # Default info box

except Exception as e:
    st.error(f"Error fetching alerts: {e}")

st.markdown("---")

# ----------------------------
# Pilgrim Registration Form
# ----------------------------
st.header("Register Pilgrim")
with st.form("pilgrim_form"):
    name = st.text_input("Name")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    zone = st.text_input("Zone")
    disability_status = st.checkbox("Disability Status")
    registered = st.checkbox("Registered", value=True)

    submitted = st.form_submit_button("Register Pilgrim")
    if submitted:
        payload = {
            "name": name,
            "phone": phone,
            "email": email,
            "zone": zone,
            "disability_status": disability_status,
            "registered": registered
        }
        try:
            resp = requests.post(f"{API_URL}/pilgrims", json=payload)
            resp.raise_for_status()
            st.success(f"Pilgrim {name} registered successfully!")
        except Exception as e:
            st.error(f"Failed to register pilgrim: {e}")

st.markdown("---")

# ----------------------------
# Crowd Density Form
# ----------------------------
st.header("Record Crowd Density")
with st.form("crowd_form"):
    zone_cd = st.text_input("Zone for Density")
    estimated_count = st.number_input("Estimated Count", min_value=0, value=0)

    submitted_cd = st.form_submit_button("Record Density")
    if submitted_cd:
        payload_cd = {"zone": zone_cd, "estimated_count": estimated_count}
        try:
            resp_cd = requests.post(f"{API_URL}/crowd_density", json=payload_cd)
            resp_cd.raise_for_status()
            st.success(f"Crowd density recorded for {zone_cd}: {estimated_count}")
        except Exception as e:
            st.error(f"Failed to record density: {e}")

st.markdown("---")

# ----------------------------
# QR Check-in Simulation
# ----------------------------
st.header("QR Check-in Simulation")
st.info("Enter pilgrim email to simulate QR check-in.")

qr_email = st.text_input("Pilgrim Email for QR Check-in")
if st.button("Check-in"):
    try:
        payload = {
            "name": "QR_Scan",
            "phone": "0000000000",
            "email": qr_email,
            "zone": "Gate_1",
            "disability_status": False,
            "registered": True
        }
        resp = requests.post(f"{API_URL}/pilgrims", json=payload)
        resp.raise_for_status()
        st.success(f"Pilgrim {qr_email} checked in at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        st.error(f"Failed QR check-in: {e}")