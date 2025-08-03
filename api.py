from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI(title="Tenders API")

@app.get("/tenders")
def get_tenders():
    try:
        with sqlite3.connect("tenders.db") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenders")
            rows = cursor.fetchall()
            tenders = [dict(row) for row in rows]
        return JSONResponse(tenders)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)