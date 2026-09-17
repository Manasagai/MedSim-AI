import bcrypt
import database


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def login_user(email: str, password: str) -> dict | None:
    """
    Attempts to log in a user.
    Returns the user dict on success, or None on failure.
    """
    user = database.get_user_by_email(email.strip().lower())
    if user is None:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def register_user(full_name: str, email: str, password: str, role: str) -> dict | None:
    """
    Registers a new user.
    Returns the new user dict on success, or None if the email already exists.
    """
    email = email.strip().lower()
    password_hash = hash_password(password)
    user_id = database.create_user(full_name, email, password_hash, role)
    if user_id is None:
        return None  # email already taken
    return {"id": user_id, "full_name": full_name, "email": email, "role": role}
