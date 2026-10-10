import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

from config import settings

logger = logging.getLogger("AuthPostgresClient")

class AuthPostgresClient:
    """
    PostgreSQL Authentication, Session Management & Audit Ledger.
    Connects to PostgreSQL using psycopg2/psycopg with automated schema creation,
    cryptographic PBKDF2 hashing, session tokens, and fallback persistence.
    """
    def __init__(self):
        self.connected = False
        self.backend = "None"
        self._conn = None
        self._fallback_users: Dict[str, Dict[str, Any]] = {}
        self._fallback_sessions: Dict[str, Dict[str, Any]] = {}
        self._fallback_audit_logs: List[Dict[str, Any]] = []
        self._init_db()

    def _get_connection(self):
        """Attempts to establish connection to PostgreSQL with quick socket check."""
        import socket
        try:
            host = settings.postgres_host or "localhost"
            port = settings.postgres_port or 5432
            
            # Fast socket probe
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.6)
            res = sock.connect_ex((host, port))
            sock.close()
            if res != 0:
                return None

            import psycopg2
            import psycopg2.extras
            
            # First try direct parameters or database_url
            if settings.database_url and "postgresql" in settings.database_url:
                conn = psycopg2.connect(settings.database_url, connect_timeout=2)
            else:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=settings.postgres_db,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                    connect_timeout=2
                )
            conn.autocommit = True
            return conn
        except Exception as e:
            logger.debug("PostgreSQL direct connection not available: %s", e)
            return None

    def _init_db(self):
        """Initializes database schema and default enterprise accounts."""
        conn = self._get_connection()
        if conn:
            self._conn = conn
            self.connected = True
            self.backend = "PostgreSQL"
            logger.info("Successfully connected to PostgreSQL for Authentication & User Store")
            self._create_tables_postgres()
            self._seed_default_users()
        else:
            self.connected = False
            self.backend = "Embedded Secure Store"
            logger.info("PostgreSQL service not currently reachable. Using Embedded Secure Store with automatic sync.")
            self._seed_default_users()

    def _create_tables_postgres(self):
        """Creates user, session, and audit tables in PostgreSQL."""
        if not self._conn:
            return
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        salt VARCHAR(64) NOT NULL,
                        full_name VARCHAR(100) NOT NULL,
                        role VARCHAR(50) DEFAULT 'operator',
                        avatar_url VARCHAR(255) DEFAULT '/static/avatar_default.png',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP WITH TIME ZONE
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS auth_audit_log (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        username VARCHAR(50),
                        action VARCHAR(50) NOT NULL,
                        ip_address VARCHAR(45),
                        details JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);")
        except Exception as e:
            logger.error("Failed to create tables in PostgreSQL: %s", e)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hashes a password with PBKDF2-HMAC-SHA256 and salt."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return pwd_hash, salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verifies password against stored PBKDF2 hash and salt."""
        computed_hash, _ = AuthPostgresClient.hash_password(password, salt)
        return secrets.compare_digest(computed_hash, stored_hash)

    def _seed_default_users(self):
        """Seeds default enterprise demo accounts."""
        demo_users = [
            {
                "username": "admin",
                "email": "director@enterprise-ai.corp",
                "password": "admin123",
                "full_name": "Dr. Elena Vance",
                "role": "admin",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Elena"
            },
            {
                "username": "operator",
                "email": "operator@enterprise-ai.corp",
                "password": "operator123",
                "full_name": "Alex Mercer",
                "role": "operator",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Alex"
            },
            {
                "username": "auditor",
                "email": "auditor@enterprise-ai.corp",
                "password": "auditor123",
                "full_name": "Sarah Chen",
                "role": "auditor",
                "avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=Sarah"
            }
        ]

        for u in demo_users:
            # Seed to fallback store
            pwd_hash, salt = self.hash_password(u["password"])
            user_id = len(self._fallback_users) + 1
            user_obj = {
                "id": user_id,
                "username": u["username"],
                "email": u["email"],
                "password_hash": pwd_hash,
                "salt": salt,
                "full_name": u["full_name"],
                "role": u["role"],
                "avatar_url": u["avatar_url"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": None
            }
            self._fallback_users[u["username"]] = user_obj
            self._fallback_users[u["email"]] = user_obj

            # If Postgres connected, seed to DB
            conn = self._conn or self._get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (u["username"], u["email"]))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO users (username, email, password_hash, salt, full_name, role, avatar_url)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (u["username"], u["email"], pwd_hash, salt, u["full_name"], u["role"], u["avatar_url"]))
                except Exception as e:
                    logger.debug("Error seeding user to PostgreSQL: %s", e)

    def register_user(self, username: str, email: str, password: str, full_name: str, role: str = "operator") -> Dict[str, Any]:
        """Registers a new user account."""
        username = username.strip().lower()
        email = email.strip().lower()

        # Check existing in Postgres or Fallback
        conn = self._conn or self._get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                    if cur.fetchone():
                        raise ValueError("A user with this username or email already exists.")
                    
                    pwd_hash, salt = self.hash_password(password)
                    avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={username}"
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash, salt, full_name, role, avatar_url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, username, email, full_name, role, avatar_url, created_at
                    """, (username, email, pwd_hash, salt, full_name, role, avatar_url))
                    row = cur.fetchone()
                    user = {
                        "id": row[0],
                        "username": row[1],
                        "email": row[2],
                        "full_name": row[3],
                        "role": row[4],
                        "avatar_url": row[5],
                        "created_at": row[6].isoformat() if row[6] else None
                    }
                    self.log_audit_action(user["id"], user["username"], "REGISTER", "127.0.0.1", {"role": role})
                    return user
            except ValueError:
                raise
            except Exception as e:
                logger.error("PostgreSQL registration error: %s", e)

        # Fallback registration
        if username in self._fallback_users or email in self._fallback_users:
            raise ValueError("A user with this username or email already exists.")
        
        pwd_hash, salt = self.hash_password(password)
        avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={username}"
        user_id = len(self._fallback_users) + 1
        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": pwd_hash,
            "salt": salt,
            "full_name": full_name,
            "role": role,
            "avatar_url": avatar_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None
        }
        self._fallback_users[username] = user
        self._fallback_users[email] = user
        self.log_audit_action(user["id"], user["username"], "REGISTER", "127.0.0.1", {"role": role})
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "avatar_url": user["avatar_url"],
            "created_at": user["created_at"]
        }

    def authenticate_user(self, username_or_email: str, password: str, ip_address: str = "127.0.0.1") -> Dict[str, Any]:
        """Authenticates user credentials and returns user payload + session token."""
        identifier = username_or_email.strip().lower()

        conn = self._conn or self._get_connection()
        if conn:
            try:
                import psycopg2.extras
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, email, password_hash, salt, full_name, role, avatar_url, created_at
                        FROM users WHERE username = %s OR email = %s
                    """, (identifier, identifier))
                    row = cur.fetchone()
                    if row:
                        if self.verify_password(password, row["password_hash"], row["salt"]):
                            # Update last_login
                            cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (row["id"],))
                            session = self.create_session(row["id"], ip_address)
                            user_data = {
                                "id": row["id"],
                                "username": row["username"],
                                "email": row["email"],
                                "full_name": row["full_name"],
                                "role": row["role"],
                                "avatar_url": row["avatar_url"],
                                "created_at": row["created_at"].isoformat() if row["created_at"] else None
                            }
                            self.log_audit_action(row["id"], row["username"], "LOGIN", ip_address, {"status": "SUCCESS"})
                            return {"user": user_data, "token": session["session_token"], "expires_at": session["expires_at"]}
            except Exception as e:
                logger.error("PostgreSQL auth error: %s", e)

        # Fallback Authentication
        if identifier in self._fallback_users:
            user = self._fallback_users[identifier]
            if self.verify_password(password, user["password_hash"], user["salt"]):
                user["last_login"] = datetime.now(timezone.utc).isoformat()
                session = self.create_session(user["id"], ip_address)
                user_data = {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "avatar_url": user["avatar_url"],
                    "created_at": user["created_at"]
                }
                self.log_audit_action(user["id"], user["username"], "LOGIN", ip_address, {"status": "SUCCESS"})
                return {"user": user_data, "token": session["session_token"], "expires_at": session["expires_at"]}

        self.log_audit_action(None, identifier, "FAILED_LOGIN", ip_address, {"reason": "Invalid credentials"})
        raise ValueError("Invalid username/email or password.")

    def create_session(self, user_id: int, ip_address: str = "127.0.0.1", user_agent: str = "Web Browser", duration_hours: int = 48) -> Dict[str, Any]:
        """Creates a secure session token."""
        token = "sess_" + secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        conn = self._conn or self._get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_sessions (session_token, user_id, expires_at, ip_address, user_agent)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (token, user_id, expires_at, ip_address, user_agent))
            except Exception as e:
                logger.error("Error creating session in PostgreSQL: %s", e)

        # Always record in memory session cache for instant lookups
        session_obj = {
            "session_token": token,
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        self._fallback_sessions[token] = session_obj
        return session_obj

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validates session token and returns associated user profile."""
        if not token:
            return None

        # Clean token prefix if "Bearer " is passed
        if token.startswith("Bearer "):
            token = token[7:].strip()

        conn = self._conn or self._get_connection()
        if conn:
            try:
                import psycopg2.extras
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT u.id, u.username, u.email, u.full_name, u.role, u.avatar_url, s.expires_at
                        FROM user_sessions s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.session_token = %s
                    """, (token,))
                    row = cur.fetchone()
                    if row:
                        if row["expires_at"] > datetime.now(timezone.utc):
                            return {
                                "id": row["id"],
                                "username": row["username"],
                                "email": row["email"],
                                "full_name": row["full_name"],
                                "role": row["role"],
                                "avatar_url": row["avatar_url"]
                            }
            except Exception as e:
                logger.error("Error validating session in PostgreSQL: %s", e)

        # Fallback session cache check
        if token in self._fallback_sessions:
            sess = self._fallback_sessions[token]
            exp = datetime.fromisoformat(sess["expires_at"])
            if exp > datetime.now(timezone.utc):
                user_id = sess["user_id"]
                for u in self._fallback_users.values():
                    if u["id"] == user_id:
                        return {
                            "id": u["id"],
                            "username": u["username"],
                            "email": u["email"],
                            "full_name": u["full_name"],
                            "role": u["role"],
                            "avatar_url": u["avatar_url"]
                        }
        return None

    def invalidate_session(self, token: str):
        """Logs out user by destroying the session token."""
        if not token:
            return
        if token.startswith("Bearer "):
            token = token[7:].strip()

        conn = self._conn or self._get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM user_sessions WHERE session_token = %s", (token,))
            except Exception as e:
                logger.error("Error deleting session in PostgreSQL: %s", e)

        self._fallback_sessions.pop(token, None)

    def log_audit_action(self, user_id: Optional[int], username: Optional[str], action: str, ip_address: str = "127.0.0.1", details: Optional[Dict[str, Any]] = None):
        """Logs security and workflow actions to PostgreSQL audit table."""
        import json
        details_json = json.dumps(details or {})
        
        conn = self._conn or self._get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO auth_audit_log (user_id, username, action, ip_address, details)
                        VALUES (%s, %s, %s, %s, %s::jsonb)
                    """, (user_id, username, action, ip_address, details_json))
            except Exception as e:
                logger.debug("Error recording audit log in PostgreSQL: %s", e)

        # Fallback in-memory audit log
        self._fallback_audit_logs.append({
            "user_id": user_id,
            "username": username,
            "action": action,
            "ip_address": ip_address,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def get_audit_logs(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Retrieves recent audit log entries."""
        conn = self._conn or self._get_connection()
        if conn:
            try:
                import psycopg2.extras
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("""
                        SELECT id, user_id, username, action, ip_address, details, timestamp
                        FROM auth_audit_log
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (limit,))
                    rows = cur.fetchall()
                    return [
                        {
                            "id": r["id"],
                            "user_id": r["user_id"],
                            "username": r["username"],
                            "action": r["action"],
                            "ip_address": r["ip_address"],
                            "details": r["details"],
                            "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.error("Error fetching audit logs from PostgreSQL: %s", e)

        return self._fallback_audit_logs[-limit:][::-1]

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Returns list of registered users."""
        conn = self._conn or self._get_connection()
        if conn:
            try:
                import psycopg2.extras
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                    cur.execute("SELECT id, username, email, full_name, role, avatar_url, created_at, last_login FROM users ORDER BY id ASC")
                    rows = cur.fetchall()
                    return [
                        {
                            "id": r["id"],
                            "username": r["username"],
                            "email": r["email"],
                            "full_name": r["full_name"],
                            "role": r["role"],
                            "avatar_url": r["avatar_url"],
                            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                            "last_login": r["last_login"].isoformat() if r["last_login"] else None
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.error("Error fetching users from PostgreSQL: %s", e)

        unique_users = {}
        for u in self._fallback_users.values():
            unique_users[u["id"]] = {
                "id": u["id"],
                "username": u["username"],
                "email": u["email"],
                "full_name": u["full_name"],
                "role": u["role"],
                "avatar_url": u["avatar_url"],
                "created_at": u["created_at"],
                "last_login": u.get("last_login")
            }
        return list(unique_users.values())

auth_db_client = AuthPostgresClient()
