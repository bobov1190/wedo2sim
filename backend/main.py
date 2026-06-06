from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncpg, json

app = FastAPI(title="WeDo 2.0 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "postgresql://neondb_owner:npg_GIyClbNQO74q@ep-sweet-pond-a2y1ztoo-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require"

async def db():
    return await asyncpg.connect(DB)

@app.on_event("startup")
async def startup():
    conn = await db()
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL DEFAULT 'Новый проект',
            lego_state JSONB NOT NULL DEFAULT '{"pieces":[]}',
            code_state JSONB NOT NULL DEFAULT '{"blocks":{},"idN":0}',
            thumbnail TEXT DEFAULT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.close()

class ProjectCreate(BaseModel):
    name: str = "Новый проект"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    lego_state: Optional[dict] = None
    code_state: Optional[dict] = None
    thumbnail: Optional[str] = None

@app.get("/api/projects")
async def list_projects():
    conn = await db()
    try:
        rows = await conn.fetch("""
            SELECT id, name, thumbnail, created_at, updated_at,
                   jsonb_array_length(COALESCE(lego_state->'pieces','[]'::jsonb)) as piece_count
            FROM projects ORDER BY updated_at DESC
        """)
        result = []
        for r in rows:
            d = dict(r)
            if d['created_at']: d['created_at'] = d['created_at'].isoformat()
            if d['updated_at']: d['updated_at'] = d['updated_at'].isoformat()
            result.append(d)
        return result
    finally:
        await conn.close()

@app.post("/api/projects")
async def create_project(data: ProjectCreate):
    conn = await db()
    try:
        row = await conn.fetchrow(
            "INSERT INTO projects (name) VALUES ($1) RETURNING id, name, created_at, updated_at",
            data.name
        )
        d = dict(row)
        d['created_at'] = d['created_at'].isoformat()
        d['updated_at'] = d['updated_at'].isoformat()
        return d
    finally:
        await conn.close()

@app.get("/api/projects/{pid}")
async def get_project(pid: int):
    conn = await db()
    try:
        row = await conn.fetchrow("SELECT * FROM projects WHERE id=$1", pid)
        if not row: raise HTTPException(404, "Not found")
        d = dict(row)
        if d['created_at']: d['created_at'] = d['created_at'].isoformat()
        if d['updated_at']: d['updated_at'] = d['updated_at'].isoformat()
        if isinstance(d['lego_state'], str): d['lego_state'] = json.loads(d['lego_state'])
        if isinstance(d['code_state'], str): d['code_state'] = json.loads(d['code_state'])
        return d
    finally:
        await conn.close()

@app.put("/api/projects/{pid}")
async def update_project(pid: int, data: ProjectUpdate):
    conn = await db()
    try:
        parts, vals, i = [], [], 1
        if data.name is not None:
            parts.append(f"name=${i}"); vals.append(data.name); i+=1
        if data.lego_state is not None:
            parts.append(f"lego_state=${i}"); vals.append(json.dumps(data.lego_state)); i+=1
        if data.code_state is not None:
            parts.append(f"code_state=${i}"); vals.append(json.dumps(data.code_state)); i+=1
        if data.thumbnail is not None:
            parts.append(f"thumbnail=${i}"); vals.append(data.thumbnail); i+=1
        if not parts: return {"ok": True}
        parts.append("updated_at=NOW()")
        vals.append(pid)
        row = await conn.fetchrow(
            f"UPDATE projects SET {','.join(parts)} WHERE id=${i} RETURNING id,name,updated_at", *vals
        )
        if not row: raise HTTPException(404, "Not found")
        d = dict(row)
        d['updated_at'] = d['updated_at'].isoformat()
        return d
    finally:
        await conn.close()

@app.delete("/api/projects/{pid}")
async def delete_project(pid: int):
    conn = await db()
    try:
        await conn.execute("DELETE FROM projects WHERE id=$1", pid)
        return {"ok": True}
    finally:
        await conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
