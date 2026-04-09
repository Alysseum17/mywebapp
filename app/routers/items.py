from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app import database

router = APIRouter(prefix="/items", tags=["items"])


class ItemCreate(BaseModel):
    name: str
    quantity: int


def wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


@router.get("")
def list_items(request: Request):
    conn = database.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM items ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if wants_html(request):
        rows_html = "".join(
            f"<tr><td>{r['id']}</td><td>{r['name']}</td></tr>"
            for r in rows
        )
        return HTMLResponse(f"""
        <html><body>
            <h1>Inventory</h1>
            <table border="1" cellpadding="6">
                <tr><th>ID</th><th>Name</th></tr>
                {rows_html}
            </table>
        </body></html>
        """)

    return JSONResponse(rows)


@router.post("", status_code=201)
def create_item(body: ItemCreate):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (name, quantity) VALUES (%s, %s)",
        (body.name, body.quantity),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return JSONResponse({"id": new_id, "name": body.name, "quantity": body.quantity})


@router.get("/{item_id}")
def get_item(item_id: int, request: Request):
    conn = database.get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    row["created_at"] = str(row["created_at"])

    if wants_html(request):
        return HTMLResponse(f"""
        <html><body>
            <h1>Item #{row['id']}</h1>
            <table border="1" cellpadding="6">
                <tr><th>ID</th><td>{row['id']}</td></tr>
                <tr><th>Name</th><td>{row['name']}</td></tr>
                <tr><th>Quantity</th><td>{row['quantity']}</td></tr>
                <tr><th>Created At</th><td>{row['created_at']}</td></tr>
            </table>
        </body></html>
        """)

    return JSONResponse(row)
