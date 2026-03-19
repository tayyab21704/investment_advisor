import os
import sqlite3
import jwt
import warnings
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from src.api.models import UserRegistrationRequest, UserLoginRequest, AuthResponse, UserProfileUpdateRequest

load_dotenv()

router = APIRouter()

# --- Config ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

DB_DIR = os.path.join(os.path.dirname(__file__), "../../data")
os.makedirs(DB_DIR, exist_ok=True)
SQLITE_DB_PATH = os.path.join(DB_DIR, "users.db")

# --- Security ---
# Suppress passlib warning caused by bcrypt >= 4.x removing __about__
warnings.filterwarnings("ignore", ".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", ".*trapped.*bcrypt.*")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def _truncate(password: str) -> bytes:
    """
    bcrypt has a hard 72-byte limit.
    Encode to UTF-8 and truncate to avoid ValueError.
    """
    return password.encode("utf-8")[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_truncate(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(_truncate(password))


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- DB Helper ---
def get_db_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            behavioral_risk_score INTEGER,
            financial_risk_score INTEGER,
            actual_risk_capacity INTEGER,
            monthly_income REAL,
            monthly_expenses REAL,
            monthly_surplus REAL,
            existing_debt REAL,
            debt_to_income_ratio REAL,
            liquidity_required_pct REAL,
            max_single_asset_pct REAL,
            max_high_risk_allocation_pct REAL,
            investment_horizon_years INTEGER,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Initialize DB on load
init_db()


# --- Endpoints ---

@router.post("/register", response_model=AuthResponse)
def register_user(request: UserRegistrationRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check existing
    cursor.execute("SELECT id FROM users WHERE email = ?", (request.email.lower(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(request.password)

    now = datetime.utcnow().isoformat()
    try:
        cursor.execute('''
            INSERT INTO users (
                name, email, hashed_password, behavioral_risk_score, financial_risk_score,
                actual_risk_capacity, monthly_income, monthly_expenses, monthly_surplus,
                existing_debt, debt_to_income_ratio, liquidity_required_pct,
                max_single_asset_pct, max_high_risk_allocation_pct, investment_horizon_years,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.name, request.email.lower(), hashed_password,
            request.behavioral_risk_score, request.financial_risk_score,
            request.actual_risk_capacity, request.monthly_income, request.monthly_expenses,
            request.monthly_surplus, request.existing_debt, request.debt_to_income_ratio,
            request.liquidity_required_pct, request.max_single_asset_pct,
            request.max_high_risk_allocation_pct, request.investment_horizon_years,
            now
        ))
        conn.commit()
        user_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

    access_token = create_access_token(
        data={"sub": request.email.lower()},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return AuthResponse(
        token=access_token,
        user_id=str(user_id),
        name=request.name,
        email=request.email.lower()
    )


@router.post("/login", response_model=AuthResponse)
def login_user(request: UserLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (request.email.lower(),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return AuthResponse(
        token=access_token,
        user_id=str(user["id"]),
        name=user["name"],
        email=user["email"]
    )


@router.get("/profile")
def get_user_profile(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = dict(user)
    del user_dict["hashed_password"]
    return user_dict

@router.put("/profile")
def update_user_profile(
    request: UserProfileUpdateRequest,
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        cursor.execute('''
            UPDATE users SET
                name = ?, behavioral_risk_score = ?, financial_risk_score = ?,
                actual_risk_capacity = ?, monthly_income = ?, monthly_expenses = ?,
                monthly_surplus = ?, existing_debt = ?, debt_to_income_ratio = ?,
                liquidity_required_pct = ?, max_single_asset_pct = ?, 
                max_high_risk_allocation_pct = ?, investment_horizon_years = ?
            WHERE email = ?
        ''', (
            request.name, request.behavioral_risk_score, request.financial_risk_score,
            request.actual_risk_capacity, request.monthly_income, request.monthly_expenses,
            request.monthly_surplus, request.existing_debt, request.debt_to_income_ratio,
            request.liquidity_required_pct, request.max_single_asset_pct,
            request.max_high_risk_allocation_pct, request.investment_horizon_years,
            email
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

    return {"message": "Profile updated successfully"}