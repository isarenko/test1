from fastapi import FastAPI, Query
from datetime import date
import psycopg2
import redis
import json
import uuid
import os

from openpyxl import Workbook
from pydantic import BaseModel
from typing import List
from fastapi.responses import FileResponse, StreamingResponse

app = FastAPI()


r = redis.Redis(
    host="redis_cache",
    port=6379,
    decode_responses=True
)


def get_db_connection():
    return psycopg2.connect(
        host="postgres_db",
        database="test1",
        user="postgres",
        password="1234"
    )


def get_tree(selected_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if selected_date:
        cursor.execute("""
            SELECT id, name, parent_id
            FROM spp_elements
            WHERE %s BETWEEN valid_from AND valid_to
              AND is_active = true
            ORDER BY id
        """, (selected_date,))
    else:
        cursor.execute("""
            SELECT id, name, parent_id
            FROM spp_elements
            WHERE is_active = true
            ORDER BY id
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return build_tree(rows)


def build_tree(rows):
    nodes = {}

    for id, name, parent_id in rows:
        nodes[id] = {
            "id": id,
            "name": name,
            "children": []
        }

    roots = []

    for id, name, parent_id in rows:
        node = nodes[id]

        if parent_id is None:
            roots.append(node)
        elif parent_id in nodes:
            nodes[parent_id]["children"].append(node)

    return roots


class CalculateRequest(BaseModel):
    selected_ids: List[int]
    amount: float


def get_tree_as_dict(rows):
    nodes = {}

    for id, name, parent_id in rows:
        nodes[id] = {
            "id": id,
            "name": name,
            "parent_id": parent_id,
            "children": [],
            "value": 0
        }

    for id, name, parent_id in rows:
        if parent_id is not None and parent_id in nodes:
            nodes[parent_id]["children"].append(nodes[id])

    return nodes


def distribute(node, amount):
    children = node["children"]

    if not children:
        node["value"] = round(amount, 2)
        return node["value"]

    share = amount / len(children)
    total = 0

    for c in children:
        total += distribute(c, share)

    node["value"] = round(total, 2)
    return node["value"]


@app.get("/tree")
def tree(date: date = Query(None)):
    return get_tree(date)


@app.post("/calculate")
def calculate(data: CalculateRequest):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, parent_id
        FROM spp_elements
        WHERE is_active = true
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    nodes = get_tree_as_dict(rows)

    if not data.selected_ids:
        return {"error": "empty selection"}

    calc_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    branch_amount = data.amount / len(data.selected_ids)

    result = []

    for sid in data.selected_ids:
        if sid not in nodes:
            return {"error": f"Node {sid} not found"}

        node = nodes[sid]

        # важно: копия чтобы не ломать дерево
        node_copy = json.loads(json.dumps(node))

        distribute(node_copy, branch_amount)
        result.append(node_copy)

    payload = {
        "calc_id": calc_id,
        "session_id": session_id,
        "status": "processing",
        "spp_version": "v1",
        "total": data.amount,
        "selected_ids": data.selected_ids,
        "result": result
    }

    r.setex(calc_id, 3600, json.dumps(payload))

    return payload


@app.post("/save/{calc_id}")
def save(calc_id: str):

    data = r.get(calc_id)

    if not data:
        return {"error": "not found"}

    parsed = json.loads(data)
    parsed["status"] = "saved"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO calculations (calc_id, session_id, status, data)
        VALUES (%s, %s, %s, %s)
    """, (
        parsed["calc_id"],
        parsed["session_id"],
        parsed["status"],
        json.dumps(parsed)
    ))

    conn.commit()
    cursor.close()
    conn.close()

    # SSE channel per session
    r.publish(
        f"calc_updates_{parsed['session_id']}",
        json.dumps(parsed)
    )

    return {"status": "saved", "calc_id": calc_id}


@app.get("/calculations")
def calculations():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT calc_id, session_id, status, created_at
        FROM calculations
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "calc_id": r[0],
            "session_id": r[1],
            "status": r[2],
            "created_at": r[3]
        }
        for r in rows
    ]


@app.get("/calculations/{calc_id}")
def get_calc(calc_id: str):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT data
        FROM calculations
        WHERE calc_id = %s
    """, (calc_id,))

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        return {"error": "not found"}

    return row[0]


@app.get("/export/{calc_id}")
def export(calc_id: str):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT data
        FROM calculations
        WHERE calc_id = %s
    """, (calc_id,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {"error": "not found"}

    import json

    data = row[0]

    # ✅ FIX: если пришла строка
    if isinstance(data, str):
        data = json.loads(data)

    wb = Workbook()
    ws = wb.active
    ws.title = "Calculation"

    ws.append(["Path", "Node", "Value"])

    def walk(node, path=""):
        current_path = f"{path}/{node['name']}" if path else node["name"]

        ws.append([
            current_path,
            node["name"],
            node.get("value", 0)
        ])

        for child in node.get("children", []):
            walk(child, current_path)

    for node in data["result"]:
        walk(node)

    file_path = f"/tmp/{calc_id}.xlsx"

    wb.save(file_path)

    return FileResponse(
        file_path,
        filename="result.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/stream/{session_id}")
def stream(session_id: str):

    pubsub = r.pubsub()
    pubsub.subscribe(f"calc_updates_{session_id}")

    def event_stream():
        for msg in pubsub.listen():
            if msg["type"] == "message":
                yield f"data: {msg['data']}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
