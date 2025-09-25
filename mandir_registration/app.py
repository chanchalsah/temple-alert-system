from flask import Flask, request, send_file, render_template
import mysql.connector, qrcode, os
from datetime import datetime

app = Flask(__name__)

# Directory for saving QR codes
QR_DIR = "qrcodes"
os.makedirs(QR_DIR, exist_ok=True)

# MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ginger",
    database="mandir_db"
)
cur = conn.cursor()

# Create bookings table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    family_members TEXT,
    slot_date DATE NOT NULL,
    slot_time VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending',
    checkin_time DATETIME
);
""")
conn.commit()

@app.route("/")
def home():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    family = request.form["family"]
    slot_date = request.form["slot_date"]
    slot_time = request.form["slot_time"]

    # Save booking
    cur.execute("""
        INSERT INTO bookings (name, family_members, slot_date, slot_time, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, family, slot_date, slot_time, "Pending"))
    conn.commit()
    booking_id = cur.lastrowid

    # Generate QR
    server_ip = "172.30.10.119"  # replace with your machine IP or domain
    qr_data = f"http://{server_ip}:5000/checkin?code={booking_id}|{name}|{slot_date}|{slot_time}|{family}"
    qr_img = qrcode.make(qr_data)
    filename = os.path.join(QR_DIR, f"booking_{booking_id}.png")
    qr_img.save(filename)

    return send_file(filename, mimetype="image/png")

@app.route("/checkin")
def checkin():
    qr_text = request.args.get("code")
    booking_id = qr_text.split("|")[0]

    cur.execute("SELECT status FROM bookings WHERE booking_id=%s", (booking_id,))
    row = cur.fetchone()

    if row and row[0] == "Pending":
        cur.execute("""
            UPDATE bookings
            SET status=%s, checkin_time=%s
            WHERE booking_id=%s
        """, ("Present", datetime.now(), booking_id))
        conn.commit()
        return f" Booking {booking_id} marked Present!"
    else:
        return "⚠️ Invalid or already used QR!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

