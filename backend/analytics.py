"""
backend/analytics.py
-----------------------
Aggregate SQL queries that power the Officer, Admin, and public
Analytics dashboards. Returns plain lists/dicts so the frontend can
feed them straight into pandas / plotly without extra transformation.
"""
from database.db import fetch_all, fetch_one


def kpi_summary():
    total = fetch_one("SELECT COUNT(*) c FROM complaints")["c"]
    resolved = fetch_one("SELECT COUNT(*) c FROM complaints WHERE status='Resolved'")["c"]
    pending = fetch_one("SELECT COUNT(*) c FROM complaints WHERE status NOT IN ('Resolved','Rejected')")["c"]
    citizens = fetch_one("SELECT COUNT(*) c FROM users WHERE role='citizen'")["c"]
    high_priority_open = fetch_one(
        "SELECT COUNT(*) c FROM complaints WHERE priority='High' AND status NOT IN ('Resolved','Rejected')"
    )["c"]
    avg_resolution_hours = fetch_one(
        """SELECT AVG( (julianday(resolved_at) - julianday(created_at)) * 24 ) as h
           FROM complaints WHERE resolved_at IS NOT NULL"""
    )["h"] or 0
    return {
        "total_complaints": total,
        "resolved": resolved,
        "pending": pending,
        "resolution_rate": round((resolved / total * 100), 1) if total else 0,
        "citizens": citizens,
        "high_priority_open": high_priority_open,
        "avg_resolution_hours": round(avg_resolution_hours, 1),
    }


def complaints_by_category():
    return fetch_all("SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC")


def complaints_by_status():
    return fetch_all("SELECT status, COUNT(*) as count FROM complaints GROUP BY status")


def complaints_by_priority():
    return fetch_all("SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority")


def complaints_by_ward():
    return fetch_all(
        "SELECT ward, COUNT(*) as count FROM complaints WHERE ward IS NOT NULL AND ward!='' "
        "GROUP BY ward ORDER BY count DESC"
    )


def complaints_daily_trend(days=30):
    return fetch_all(
        f"""SELECT date(created_at) as day, COUNT(*) as count
            FROM complaints
            WHERE created_at >= datetime('now', '-{int(days)} days')
            GROUP BY day ORDER BY day"""
    )


def complaints_monthly_trend():
    return fetch_all(
        """SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
           FROM complaints GROUP BY month ORDER BY month"""
    )


def officer_performance():
    return fetch_all(
        """SELECT u.full_name as officer, COUNT(c.id) as assigned,
                  SUM(CASE WHEN c.status='Resolved' THEN 1 ELSE 0 END) as resolved
           FROM users u LEFT JOIN complaints c ON c.assigned_officer_id = u.id
           WHERE u.role='officer' GROUP BY u.id"""
    )
