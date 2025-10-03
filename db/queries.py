from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Iterable, Dict, Any, Tuple
from datetime import date
from .db import get_connection

def dollars_to_cents(amount: float | str) -> int:
    d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(d * 100)

def cents_to_dollars(cents: int) -> str:
    d = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
    return f"{d}"

def ensure_category(name: str) -> int:
    sql_sel = "SELECT id FROM categories WHERE name = ?"
    sql_ins = "INSERT INTO categories(name) VALUES (?)"
    with get_connection() as conn:
        cur = conn.execute(sql_sel, (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur = conn.execute(sql_ins, (name,))
        return cur.lastrowid

def add_transaction(*,
        user_id: int = 1,
        type_: str, #income or expense
        category: Optional[str],
        amount_dollars: float | str,
        date_iso: str,
        notes: Optional[str] = None,
        currency: str = "USD") -> int:
     if type_ not in ("income", "expense"):
         raise ValueError("type_ must be 'income' or 'expense'")
     amount_cents = dollars_to_cents(amount_dollars)
     category_id = ensure_category(category) if category else None
     sql = """ 
     INSERT INTO transactions(user_id, category_id, type, amount_cents, currency, date, notes)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     """
     with get_connection() as conn:
         cur = conn.execute(sql, (user_id, category_id, type_, amount_cents, currency, date_iso, notes))
         return cur.lastrowid
     
def get_transaction(tx_id: int) -> Optional[dict]:
    sql = """
    SELECT t.*, c.name AS category_name
    FROM transactions t
    LEFT JOIN categories c ON c.id = t.category_id
    WHERE t.id = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (tx_id,)).fetchone()
        return dict(row) if row else None

def list_transactions(
        *,
        user_id: int = 1,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        type_: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
) -> list[dict]:
    where = ["t.user_id = ?"]
    params: list[Any] = [user_id]

    if start_date:
        where.append("t.date >= ?")
        params.append(start_date)
    if end_date:
        where.append("t.date <= ?")
        params.append(end_date)
    if type_:
        where.append("t.type = ?")
        params.append(type_)
    if category:
        where.append("c.name = ?")
        params.append(category)
    
    sql = f"""
    SELECT t.*, c.name AS category_name
    FROM transactions t
    LEFT JOIN categories c ON c.id = t.category_id
    WHERE {' AND '.join(where)}
    ORDER BY t.date DESC, t.id DESC
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

def update_transaction(
        tx_id: int,
        *,
        type_: Optional[str] = None,
        category: Optional[str] = None,
        amount_dollars: Optional[float | str] = None,
        date_iso: Optional[str] = None,
        notes: Optional[str] = None,
        currency: Optional[str] = None,
) -> int:
    sets = []
    params: list[Any] = []

    if type_:
        if type_ not in ("income", "expense"):
            raise ValueError("type_ must be income or expense")
        sets.append("type = ?")
        params.append(type_)
    if category is not None:
        cat_id = ensure_category(category) if category else None
        sets.append("category_id = ?")
        params.append(cat_id)
    if amount_dollars is not None:
        sets.append("amount_cents = ?")
        params.append(dollars_to_cents(amount_dollars))
    if date_iso:
        sets.append("date = ?")
        params.append(date_iso)
    if notes is not None:
        sets.append("notes = ?")
        params.append(notes)
    if currency:
        sets.append("currency = ?")
        params.append(currency)

    if not sets:
        return 0

    sql = f"UPDATE transactions SET {', '.join(sets)} WHERE id = ?"
    params.append(tx_id)

    with get_connection() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.rowcount

def delete_transaction(tx_id: int) -> int:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        conn.commit()
        return cur.rowcount

# --------- Analytics helpers ----------
def monthly_income_expense(user_id: int, year: int, month: int) -> dict:
    start = f"{year:04d}-{month:02d}-01"
    # SQLite trick: next month, day 1, minus one day = last day of this month
    end = f"{year:04d}-{month:02d}-31"
    sql = """
    SELECT type, SUM(amount_cents) AS total_cents
    FROM transactions
    WHERE user_id = ?
      AND date >= ?
      AND date <= ?
    GROUP BY type
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (user_id, start, end)).fetchall()
        out = {"income": "0.00", "expense": "0.00"}
        for r in rows:
            out[r["type"]] = cents_to_dollars(r["total_cents"] or 0)
        return out

def category_breakdown(user_id: int, start_date: str, end_date: str) -> list[tuple[str,str]]:
    sql = """
    SELECT c.name AS category, SUM(t.amount_cents) AS total_cents
    FROM transactions t
    LEFT JOIN categories c ON c.id = t.category_id
    WHERE t.user_id = ? AND t.date >= ? AND t.date <= ? AND t.type = 'expense'
    GROUP BY c.name
    ORDER BY total_cents DESC NULLS LAST
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (user_id, start_date, end_date)).fetchall()
        return [(r["category"] or "Uncategorized", cents_to_dollars(r["total_cents"] or 0)) for r in rows]
