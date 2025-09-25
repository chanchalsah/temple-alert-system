from flask import Flask, render_template, request
from datetime import date, datetime
import mysql.connector, qrcode, os

app = Flask(__name__)

# Database connection
conn = mysql.connector.connect(
    host="localhost", user="root", password="ginger", database="mandir_db"
)
cur = conn.cursor()

# QR folder
QR_DIR = os.path.join("static", "qrcodes")
os.makedirs(QR_DIR, exist_ok=True)

# Create table if not exists (with qr_file)
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

# ----------------- ROUTES -----------------

# Step 1: Show basic info form
@app.route("/")
def home():
    return render_template("register.html", min_date=date.today().strftime("%Y-%m-%d"))

# Step 2: Show slots based on date and availability
@app.route("/choose_slot", methods=["POST"])
def choose_slot():
    name = request.form["name"]
    family = request.form["family"]
    slot_date = request.form["slot_date"]

    # Date validation
    if datetime.strptime(slot_date, "%Y-%m-%d").date() < date.today():
        return """
        <script>
            alert("⚠️ Please select a future date!");
            window.location.href = "/";
        </script>
        """

    slots = ["8-9 AM", "9-10 AM"]
    slot_availability = {}
    for slot in slots:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE slot_date=%s AND slot_time=%s", (slot_date, slot))
        count = cur.fetchone()[0]
        slot_availability[slot] = count < 10

    return render_template("choose_slot.html", name=name, family=family, slot_date=slot_date, slots=slot_availability)

# Step 3: Final registration & QR generation
@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    family = request.form["family"]
    slot_date = request.form["slot_date"]
    slot_time = request.form["slot_time"]

    # Insert booking
    cur.execute(
        "INSERT INTO bookings (name,family_members,slot_date,slot_time,status) VALUES (%s,%s,%s,%s,'Pending')",
        (name, family, slot_date, slot_time)
    )
    conn.commit()
    booking_id = cur.lastrowid

    # Generate QR
    server_ip = "172.30.10.119"  # replace with your IP/domain
    qr_data = f"http://{server_ip}:5000/checkin?code={booking_id}"
    qr_img = qrcode.make(qr_data)
    qr_filename = f"qrcodes/booking_{booking_id}_{name}.png"
    save_path = os.path.join(QR_DIR, f"booking_{booking_id}_{name}.png")
    qr_img.save(save_path)

    cur.execute("UPDATE bookings SET qr_file=%s WHERE booking_id=%s", (qr_filename, booking_id))
    conn.commit()

    return render_template("qr_page.html", booking_id=booking_id, qr_filename=qr_filename)

# ----------------- CHECKIN (any scanner can update) -----------------
@app.route("/checkin")
def checkin():
    qr_text = request.args.get("code")
    booking_id = qr_text

    cur.execute("SELECT status, qr_file FROM bookings WHERE booking_id=%s", (booking_id,))
    row = cur.fetchone()

    if row and row[0] == "Pending":
        cur.execute("UPDATE bookings SET status=%s, checkin_time=%s WHERE booking_id=%s",
                    ("Present", datetime.now(), booking_id))
        conn.commit()

        # Delete QR file
        qr_file = row[1]
        if qr_file:
            file_path = os.path.join("static", qr_file)
            if os.path.exists(file_path):
                os.remove(file_path)

        return f"Booking {booking_id} marked Present!"
    else:
        return "⚠️ Invalid or already used QR!"

# ----------------- USER STATUS POLLING -----------------
@app.route("/status_check/<int:booking_id>")
def status_check(booking_id):
    cur.execute("SELECT status FROM bookings WHERE booking_id=%s", (booking_id,))
    row = cur.fetchone()
    if row:
        return {"status": row[0]}
    return {"status": "Not Found"}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
