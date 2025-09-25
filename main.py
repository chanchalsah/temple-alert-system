from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import asyncpg, os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

app = FastAPI(title="Temple Alert System")

# Database config
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# -------------------------
# Pydantic models
# -------------------------
class Alert(BaseModel):
    zone: str
    severity: str
    type: str
    message: str
    recipients: List[str]

class Pilgrim(BaseModel):
    name: str
    phone: str
    email: str
    registered: bool = False
    zone: str
    disability_status: bool = False

class CrowdDensity(BaseModel):
    zone: str
    estimated_count: int

# -------------------------
# Startup / Shutdown
# -------------------------
@app.on_event("startup")
async def startup():
    app.state.db = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        host=DB_HOST,
        min_size=1,
        max_size=5
    )

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()

# -------------------------
# ALERTS endpoints
# -------------------------
@app.post("/alerts")
async def create_alert(alert: Alert):
    query = """
        INSERT INTO alerts (zone, severity, type, message, recipients, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6)
    """
    try:
        async with app.state.db.acquire() as conn:
            await conn.execute(query, alert.zone, alert.severity, alert.type, alert.message, alert.recipients, datetime.utcnow())
        return {"status": "sent", "alert": alert.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_alerts(limit: int = 10):
    query = """
        SELECT alert_id, zone, severity, type, message, recipients, timestamp, status
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT $1
    """
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch(query, limit)
    return [
        {
            "alert_id": row["alert_id"],
            "zone": row["zone"],
            "severity": row["severity"],
            "type": row["type"],
            "message": row["message"],
            "recipients": row["recipients"],
            "timestamp": row["timestamp"].isoformat(),
            "status": row["status"]
        }
        for row in rows
    ]

# -------------------------
# PILGRIMS endpoints
# -------------------------
@app.post("/pilgrims")
async def create_pilgrim(pilgrim: Pilgrim):
    query = """
        INSERT INTO pilgrims (name, phone, email, registered, zone, disability_status)
        VALUES ($1, $2, $3, $4, $5, $6)
    """
    try:
        async with app.state.db.acquire() as conn:
            await conn.execute(query, pilgrim.name, pilgrim.phone, pilgrim.email, pilgrim.registered, pilgrim.zone, pilgrim.disability_status)
        return {"status": "added", "pilgrim": pilgrim.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pilgrims")
async def get_pilgrims():
    query = "SELECT * FROM pilgrims ORDER BY name"
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch(query)
    return [
        {
            "pilgrim_id": row["pilgrim_id"],
            "name": row["name"],
            "phone": row["phone"],
            "email": row["email"],
            "registered": row["registered"],
            "zone": row["zone"],
            "disability_status": row["disability_status"]
        }
        for row in rows
    ]

# -------------------------
# CROWD DENSITY endpoints
# -------------------------
@app.post("/crowd_density")
async def add_crowd_density(data: CrowdDensity):
    query = """
        INSERT INTO crowd_density (zone, estimated_count, timestamp)
        VALUES ($1, $2, $3)
    """
    try:
        async with app.state.db.acquire() as conn:
            await conn.execute(query, data.zone, data.estimated_count, datetime.utcnow())
        return {"status": "added", "data": data.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crowd_density")
async def get_crowd_density():
    query = """
        SELECT id, zone, estimated_count, timestamp
        FROM crowd_density
        ORDER BY timestamp DESC
        LIMIT 20
    """
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch(query)
    return [
        {
            "id": row["id"],
            "zone": row["zone"],
            "estimated_count": row["estimated_count"],
            "timestamp": row["timestamp"].isoformat()
        }
        for row in rows
    ]

# -------------------------
# Root endpoint
# -------------------------
@app.get("/")
async def root():
    return {"message": "Temple Alert API is running"}