import streamlit as st
import requests
import qrcode
from PIL import Image
from io import BytesIO
import base64

BASE_URL = "http://127.0.0.1:8000"  # FastAPI backend

st.title("Temple Alert System")

menu = ["Register Pilgrim", "Scan QR (Attendance)", "View Alerts", "Crowd Density"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------------------
# Pilgrim Registration + QR
# ------------------------------
if choice == "Register Pilgrim":
    st.header("Pilgrim Registration")
    name = st.text_input("Name")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    zone = st.text_input("Zone")
    disability = st.checkbox("Disability Status")

    if st.button("Register"):
        data = {
            "name": name,
            "phone": phone,
            "email": email,
            "zone": zone,
            "disability_status": disability
        }
        response = requests.post(f"{BASE_URL}/pilgrims", json=data)
        if response.status_code == 200:
            pilgrim = response.json()["pilgrim"]
            st.success(f"Pilgrim Registered! ID: {pilgrim.get('pilgrim_id', 'N/A')}")

            # Generate QR Code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(pilgrim.get("pilgrim_id", ""))
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            st.image(img, caption="QR Code", use_column_width=True)

            # Download QR as PNG
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            st.download_button(
                label="Download QR Code",
                data=buffer,
                file_name=f"{name}_qr.png",
                mime="image/png"
            )
        else:
            st.error(response.text)

# ------------------------------
# Simulated QR Scanning (Attendance)
# ------------------------------
elif choice == "Scan QR (Attendance)":
    st.header("Scan Pilgrim QR")
    uploaded_file = st.file_uploader("Upload QR Code Image", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        try:
            img = Image.open(uploaded_file)
            import pyzbar.pyzbar as pyzbar

            decoded = pyzbar.decode(img)
            if decoded:
                pilgrim_id = decoded[0].data.decode('utf-8')
                st.success(f"QR Scanned! Pilgrim ID: {pilgrim_id}")

                # Call backend to mark registered/present (optional)
                st.info("Attendance marked (simulation)")
            else:
                st.error("Could not decode QR code.")
        except Exception as e:
            st.error(f"Error reading QR: {e}")

# ------------------------------
# View Alerts
# ------------------------------
elif choice == "View Alerts":
    st.header("Temple Alerts")
    response = requests.get(f"{BASE_URL}/alerts")
    if response.status_code == 200:
        alerts = response.json().get("alerts", [])
        for alert in alerts:
            st.write(f"**Zone:** {alert['zone']}")
            st.write(f"**Severity:** {alert['severity']}")
            st.write(f"**Type:** {alert['type']}")
            st.write(f"**Message:** {alert['message']}")
            st.write(f"**Time:** {alert['timestamp']}")
            st.markdown("---")
    else:
        st.error("Could not fetch alerts.")

# ------------------------------
# Crowd Density
# ------------------------------
elif choice == "Crowd Density":
    st.header("Crowd Density")
    response = requests.get(f"{BASE_URL}/crowd_density")
    if response.status_code == 200:
        densities = response.json().get("crowd_density", [])
        for d in densities:
            st.write(f"**Zone:** {d['zone']} → **Estimated Count:** {d['estimated_count']}")
            st.write(f"**Time:** {d['timestamp']}")
            st.markdown("---")
    else:
        st.error("Could not fetch crowd data.")