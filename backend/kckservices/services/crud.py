from typing import Any
from uuid import UUID
import psycopg
from fastapi import HTTPException
from psycopg import sql

# Small reusable CRUD helpers for the simple tables (cars, rental_services, promotions).
# Table and column names go through sql.Identifier, values through %s placeholders,
# so nothing user-supplied is ever pasted into the SQL text.

def _table(name: str) -> sql.Identifier:
    return sql.Identifier("public", name)

def _raise_db_error(e: psycopg.Error, label: str):
    if isinstance(e, psycopg.errors.UniqueViolation):
        raise HTTPException(status_code=409, detail=f"A {label} with the same unique value already exists.")
    if isinstance(e, psycopg.errors.ForeignKeyViolation):
        raise HTTPException(status_code=409, detail=f"This {label} is still used by other records (e.g. bookings).")
    if isinstance(e, psycopg.errors.CheckViolation):
        raise HTTPException(status_code=422, detail=f"Invalid {label} values: {e.diag.message_primary}")
    raise e

def to_db(data: dict[str, Any]) -> dict[str, Any]:
    # psycopg needs UUIDs as strings
    return {k: (str(v) if isinstance(v, UUID) else v) for k, v in data.items()}

def get_row(conn, table: str, row_id, label: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {} WHERE id = %s;").format(_table(table)), (str(row_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"{label.capitalize()} not found.")
    return row

def insert_row(conn, table: str, data: dict[str, Any], label: str) -> dict:
    data = to_db(data)
    columns = list(data.keys())
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *;").format(
        _table(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(query, [data[c] for c in columns])
            row = cur.fetchone()
        conn.commit()
        return row
    except psycopg.Error as e:
        _raise_db_error(e, label)

def update_row(conn, table: str, row_id, data: dict[str, Any], label: str) -> dict:
    if not data:
        return get_row(conn, table, row_id, label)
    data = to_db(data)
    query = sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING *;").format(
        _table(table),
        sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(c)) for c in data),
    )
    try:
        with conn.cursor() as cur:
            cur.execute(query, [*data.values(), str(row_id)])
            row = cur.fetchone()
    except psycopg.Error as e:
        _raise_db_error(e, label)
    if not row:
        raise HTTPException(status_code=404, detail=f"{label.capitalize()} not found.")
    conn.commit()
    return row

def delete_row(conn, table: str, row_id, label: str) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DELETE FROM {} WHERE id = %s RETURNING id;").format(_table(table)), (str(row_id),))
            deleted = cur.fetchone()
    except psycopg.Error as e:
        _raise_db_error(e, label)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"{label.capitalize()} not found.")
    conn.commit()
