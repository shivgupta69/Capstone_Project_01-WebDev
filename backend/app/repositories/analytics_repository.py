from backend.app.utils.db import get_db


def ensure_study_logs_table():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            hours_studied REAL NOT NULL DEFAULT 0,
            tasks_completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def insert_daily_study_log(user_id, log_date, hours_studied, tasks_completed):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO study_logs (user_id, log_date, hours_studied, tasks_completed)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, log_date, hours_studied, tasks_completed),
    )
    conn.commit()
    conn.close()


def fetch_daily_analytics_rows(user_id, days):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            log_date,
            COALESCE(SUM(hours_studied), 0) AS hours_total,
            COALESCE(SUM(tasks_completed), 0) AS tasks_total
        FROM study_logs
        WHERE user_id = ?
          AND log_date BETWEEN date('now', 'localtime', ?) AND date('now', 'localtime')
        GROUP BY log_date
        ORDER BY log_date ASC
        """,
        (user_id, f"-{days - 1} days"),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
