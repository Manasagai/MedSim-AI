import sqlite3
import os

DB_NAME = "medsim.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create scenarios table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            specialty TEXT NOT NULL,
            learner_level TEXT NOT NULL,
            learning_objective TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            case_type TEXT NOT NULL,
            scenario_data TEXT NOT NULL,
            published BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(instructor_id) REFERENCES users(id)
        )
    ''')

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            scenario_id INTEGER NOT NULL,
            score INTEGER,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(scenario_id) REFERENCES scenarios(id)
        )
    ''')

    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# User / Auth helpers
# ---------------------------------------------------------------------------

def create_user(full_name: str, email: str, password_hash: str, role: str) -> int | None:
    """Inserts a new user and returns their id. Returns None if email already exists."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (full_name, email, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # duplicate email
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """Returns the user row as a dict, or None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ---------------------------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------------------------

def save_scenario(instructor_id: int, title: str, specialty: str, learner_level: str,
                  learning_objective: str, difficulty: str, case_type: str,
                  scenario_data: str, published: bool = False) -> int:
    """Inserts a new scenario and returns its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO scenarios
            (instructor_id, title, specialty, learner_level, learning_objective,
             difficulty, case_type, scenario_data, published)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (instructor_id, title, specialty, learner_level, learning_objective,
         difficulty, case_type, scenario_data, int(published))
    )
    conn.commit()
    scenario_id = cursor.lastrowid
    conn.close()
    return scenario_id


def get_scenario_by_id(scenario_id: int) -> dict | None:
    """Returns a single scenario row as a dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_instructor_scenarios(instructor_id: int) -> list:
    """Returns all scenarios created by an instructor, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, title, specialty, learner_level, difficulty, learning_objective,
               case_type, published, created_at
        FROM scenarios
        WHERE instructor_id = ?
        ORDER BY created_at DESC
        """,
        (instructor_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_published_scenarios() -> list:
    """Returns all published scenarios (for students), newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT s.id, s.title, s.specialty, s.learner_level, s.difficulty,
               s.learning_objective, s.case_type, s.scenario_data, s.created_at,
               u.full_name AS instructor_name
        FROM scenarios s
        JOIN users u ON s.instructor_id = u.id
        WHERE s.published = 1
        ORDER BY s.created_at DESC
        """
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def toggle_publish_scenario(scenario_id: int, instructor_id: int) -> None:
    """Toggles the published flag of a scenario owned by the instructor."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE scenarios
        SET published = CASE WHEN published = 1 THEN 0 ELSE 1 END
        WHERE id = ? AND instructor_id = ?
        """,
        (scenario_id, instructor_id)
    )
    conn.commit()
    conn.close()


def set_publish_scenario(scenario_id: int, instructor_id: int, published: bool) -> None:
    """Explicitly sets the published state of a scenario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE scenarios SET published = ? WHERE id = ? AND instructor_id = ?",
        (int(published), scenario_id, instructor_id)
    )
    conn.commit()
    conn.close()


def delete_scenario(scenario_id: int, instructor_id: int) -> None:
    """Deletes a scenario owned by the instructor (and its sessions)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE scenario_id = ?", (scenario_id,))
    cursor.execute(
        "DELETE FROM scenarios WHERE id = ? AND instructor_id = ?",
        (scenario_id, instructor_id)
    )
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Instructor stats
# ---------------------------------------------------------------------------

def get_instructor_stats(instructor_id: int) -> dict:
    """Returns real dashboard statistics for an instructor."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM scenarios WHERE instructor_id = ?",
        (instructor_id,)
    )
    total_scenarios = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM scenarios WHERE instructor_id = ? AND published = 1",
        (instructor_id,)
    )
    published_cases = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM sessions s
        JOIN scenarios sc ON s.scenario_id = sc.id
        WHERE sc.instructor_id = ? AND s.completed = 1
        """,
        (instructor_id,)
    )
    student_attempts = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT AVG(s.score) FROM sessions s
        JOIN scenarios sc ON s.scenario_id = sc.id
        WHERE sc.instructor_id = ? AND s.completed = 1 AND s.score IS NOT NULL
        """,
        (instructor_id,)
    )
    avg_row = cursor.fetchone()[0]
    avg_score = round(avg_row) if avg_row is not None else 0

    conn.close()
    return {
        "total_scenarios": total_scenarios,
        "published_cases": published_cases,
        "student_attempts": student_attempts,
        "avg_score": avg_score,
    }

# ---------------------------------------------------------------------------
# Session / Student progress helpers
# ---------------------------------------------------------------------------

def save_session(student_id: int, scenario_id: int, score: int) -> int:
    """Saves a completed student session and returns its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO sessions (student_id, scenario_id, score, completed)
        VALUES (?, ?, ?, 1)
        """,
        (student_id, scenario_id, score)
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def get_student_stats(student_id: int) -> dict:
    """Returns completed simulation count and average score for a student."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM sessions WHERE student_id = ? AND completed = 1",
        (student_id,)
    )
    completed = cursor.fetchone()[0]

    cursor.execute(
        "SELECT AVG(score) FROM sessions WHERE student_id = ? AND completed = 1 AND score IS NOT NULL",
        (student_id,)
    )
    avg_row = cursor.fetchone()[0]
    avg_score = round(avg_row) if avg_row is not None else None

    conn.close()
    return {"completed": completed, "avg_score": avg_score}


def get_student_sessions(student_id: int) -> list:
    """Returns completed sessions for a student with scenario details, newest first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT se.id, se.score, se.created_at,
               sc.title, sc.specialty, sc.difficulty
        FROM sessions se
        JOIN scenarios sc ON se.scenario_id = sc.id
        WHERE se.student_id = ? AND se.completed = 1
        ORDER BY se.created_at DESC
        """,
        (student_id,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
