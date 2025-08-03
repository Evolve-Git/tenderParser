from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import sqlite3
from main import parse_tenders

app = FastAPI(title="Tenders API")

@app.get("/tenders/cache")
def getTendersCache(limit: int = Query(10, ge=1, le=100)):
    try:
        with sqlite3.connect("tenders.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenders LIMIT ?", (limit,))
            rows = cursor.fetchall()
            tenders = [dict(row) for row in rows]
        return JSONResponse(tenders)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/tenders")
def getTendersLive(limit: int = Query(10, ge=1, le=100)):
    try:
        BASE_URL = "https://www.b2b-center.ru"
        MARKET_URL = f"{BASE_URL}/market/"
        tenders = parse_tenders(limit)
        return JSONResponse(tenders)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)