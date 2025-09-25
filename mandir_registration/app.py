from flask import Flask, request, render_template, redirect, url_for
import mysql.connector, qrcode, os
from datetime import datetime, date

app = Flask(__name__)

# Directory for saving QR codes inside static
QR_DIR = os.path.join("static", "qrcodes")
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
    checkin_time DATETIME,
    qr_file VARCHAR(255)
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

    # ✅ Ensure booking date is after today
    if datetime.strptime(slot_date, "%Y-%m-%d").date() <= date.today():
        return """
        <script>
            alert("⚠️ Please select a future date!");
            window.location.href = "/";
        </script>
    """

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

    qr_filename = f"qrcodes/booking_{booking_id}_{name}.png"
    save_path = os.path.join("static", qr_filename)
    qr_img.save(save_path)

    # Save QR filename in DB
    cur.execute("UPDATE bookings SET qr_file=%s WHERE booking_id=%s", (qr_filename, booking_id))
    conn.commit()

    return render_template("qr_page.html", booking_id=booking_id, qr_filename=qr_filename)

@app.route("/checkin")
def checkin():
    qr_text = request.args.get("code")
    booking_id = qr_text.split("|")[0]

    cur.execute("SELECT status, qr_file FROM bookings WHERE booking_id=%s", (booking_id,))
    row = cur.fetchone()

    if row and row[0] == "Pending":
        # Update status
        cur.execute("""
            UPDATE bookings
            SET status=%s, checkin_time=%s
            WHERE booking_id=%s
        """, ("Present", datetime.now(), booking_id))
        conn.commit()

        # ✅ Delete QR file from static folder
        qr_file = row[1]
        if qr_file:
            file_path = os.path.join("static", qr_file)
            if os.path.exists(file_path):
                os.remove(file_path)

        return f"Booking {booking_id} marked Present!"
    else:
        return "⚠️ Invalid or already used QR!"

@app.route("/status_check/<int:booking_id>")
def status_check(booking_id):
    cur.execute("SELECT status FROM bookings WHERE booking_id=%s", (booking_id,))
    row = cur.fetchone()
    if row:
        return {"status": row[0]}
    return {"status": "Not Found"}

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
