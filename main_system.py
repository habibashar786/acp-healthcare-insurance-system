"""
ACP Healthcare Insurance System - Main FastAPI Application
Production-ready API for healthcare insurance management
Revised and fixed version for Windows compatibility
"""

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import enum
import os
import sys
from dotenv import load_dotenv
import logging
import uvicorn
from contextlib import asynccontextmanager

# Fix for Windows Unicode issues
if sys.platform == "win32":
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')

# Load environment variables
load_dotenv()

# Configure logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    encoding='utf-8' if sys.platform == "win32" else None
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./acp_healthcare.db")
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AGENT = "agent"
    CUSTOMER = "customer"
    PROVIDER = "provider"

class PolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class ClaimStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"

class PlanType(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    address = Column(Text)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    policies = relationship("Policy", back_populates="user")
    claims = relationship("Claim", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class InsurancePlan(Base):
    __tablename__ = "insurance_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    description = Column(Text)
    monthly_premium = Column(Float, nullable=False)
    annual_premium = Column(Float, nullable=False)
    coverage_amount = Column(Float, nullable=False)
    deductible = Column(Float, default=0)
    copay_percentage = Column(Float, default=20)
    max_out_of_pocket = Column(Float)
    benefits = Column(Text)  # JSON string
    exclusions = Column(Text)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    policies = relationship("Policy", back_populates="plan")

class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("insurance_plans.id"))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(PolicyStatus), default=PolicyStatus.PENDING)
    premium_amount = Column(Float, nullable=False)
    payment_frequency = Column(String, default="monthly")
    beneficiaries = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="policies")
    plan = relationship("InsurancePlan", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")
    payments = relationship("Payment", back_populates="policy")

class Claim(Base):
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    policy_id = Column(Integer, ForeignKey("policies.id"))
    claim_date = Column(DateTime, default=datetime.utcnow)
    service_date = Column(DateTime)
    provider_name = Column(String)
    diagnosis_code = Column(String)
    procedure_code = Column(String)
    claim_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, default=0)
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.SUBMITTED)
    notes = Column(Text)
    documents = Column(Text)  # JSON string with document URLs
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="claims", foreign_keys=[user_id])
    policy = relationship("Policy", back_populates="claims")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    policy_id = Column(Integer, ForeignKey("policies.id"))
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(String)
    transaction_id = Column(String)
    status = Column(String, default="completed")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="payments")
    policy = relationship("Policy", back_populates="payments")

# Pydantic Models with Updated Config
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

class InsurancePlanBase(BaseModel):
    name: str
    plan_type: PlanType
    description: Optional[str] = None
    monthly_premium: float = Field(..., gt=0)
    annual_premium: float = Field(..., gt=0)
    coverage_amount: float = Field(..., gt=0)
    deductible: float = Field(0, ge=0)
    copay_percentage: float = Field(20, ge=0, le=100)
    max_out_of_pocket: Optional[float] = None
    benefits: Optional[Dict[str, Any]] = None
    exclusions: Optional[List[str]] = None

class InsurancePlanCreate(InsurancePlanBase):
    pass

class InsurancePlanResponse(InsurancePlanBase):
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PolicyBase(BaseModel):
    plan_id: int
    start_date: datetime
    payment_frequency: str = "monthly"
    beneficiaries: Optional[List[Dict[str, str]]] = None

class PolicyCreate(PolicyBase):
    pass

class PolicyResponse(PolicyBase):
    id: int
    policy_number: str
    user_id: int
    end_date: datetime
    status: PolicyStatus
    premium_amount: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ClaimBase(BaseModel):
    policy_id: int
    service_date: datetime
    provider_name: str
    diagnosis_code: Optional[str] = None
    procedure_code: Optional[str] = None
    claim_amount: float = Field(..., gt=0)
    notes: Optional[str] = None

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    status: Optional[ClaimStatus] = None
    approved_amount: Optional[float] = None
    notes: Optional[str] = None

class ClaimResponse(ClaimBase):
    id: int
    claim_number: str
    user_id: int
    claim_date: datetime
    status: ClaimStatus
    approved_amount: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class PaymentBase(BaseModel):
    policy_id: int
    amount: float = Field(..., gt=0)
    payment_method: str
    transaction_id: Optional[str] = None
    description: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    payment_reference: str
    user_id: int
    payment_date: datetime
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Dependency functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Utility functions
def generate_policy_number():
    import random
    import string
    return 'POL' + ''.join(random.choices(string.digits, k=10))

def generate_claim_number():
    import random
    import string
    return 'CLM' + ''.join(random.choices(string.digits, k=10))

def generate_payment_reference():
    import random
    import string
    return 'PAY' + ''.join(random.choices(string.digits, k=10))

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ACP Healthcare Insurance System...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified successfully")
    
    # Create default admin user if not exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                email="admin@acp-health.com",
                username="admin",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created")
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
    finally:
        db.close()
    
    logger.info("System ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ACP Healthcare Insurance System...")

# App configuration with lifespan
app = FastAPI(
    title="ACP Healthcare Insurance System",
    description="Comprehensive healthcare insurance management platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "ACP Healthcare Insurance System API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/api/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ACP Healthcare Insurance System"
    }

# Authentication endpoints
@app.post("/register", response_model=UserResponse, tags=["Authentication"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone=user.phone,
        address=user.address,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user registered: {user.username}")
    return db_user

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    user_response = UserResponse.model_validate(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@app.get("/me", response_model=UserResponse, tags=["Users"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Insurance Plans endpoints
@app.post("/plans", response_model=InsurancePlanResponse, tags=["Insurance Plans"])
def create_plan(
    plan: InsurancePlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    import json
    db_plan = InsurancePlan(
        **plan.model_dump(exclude={'benefits', 'exclusions'}),
        benefits=json.dumps(plan.benefits) if plan.benefits else None,
        exclusions=json.dumps(plan.exclusions) if plan.exclusions else None
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    
    logger.info(f"New insurance plan created: {plan.name}")
    return db_plan

@app.get("/plans", response_model=List[InsurancePlanResponse], tags=["Insurance Plans"])
def get_plans(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    plans = db.query(InsurancePlan).filter(InsurancePlan.is_active == True).offset(skip).limit(limit).all()
    return plans

@app.get("/plans/{plan_id}", response_model=InsurancePlanResponse, tags=["Insurance Plans"])
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(InsurancePlan).filter(InsurancePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

# Policy endpoints
@app.post("/policies", response_model=PolicyResponse, tags=["Policies"])
def create_policy(
    policy: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    import json
    
    # Get the plan
    plan = db.query(InsurancePlan).filter(InsurancePlan.id == policy.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Insurance plan not found")
    
    # Calculate end date (1 year from start)
    end_date = policy.start_date + timedelta(days=365)
    
    # Determine premium amount based on payment frequency
    if policy.payment_frequency == "monthly":
        premium_amount = plan.monthly_premium
    else:
        premium_amount = plan.annual_premium
    
    db_policy = Policy(
        policy_number=generate_policy_number(),
        user_id=current_user.id,
        plan_id=policy.plan_id,
        start_date=policy.start_date,
        end_date=end_date,
        premium_amount=premium_amount,
        payment_frequency=policy.payment_frequency,
        beneficiaries=json.dumps(policy.beneficiaries) if policy.beneficiaries else None,
        status=PolicyStatus.PENDING
    )
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    
    logger.info(f"New policy created: {db_policy.policy_number} for user {current_user.username}")
    return db_policy

@app.get("/policies", response_model=List[PolicyResponse], tags=["Policies"])
def get_policies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == UserRole.ADMIN:
        policies = db.query(Policy).offset(skip).limit(limit).all()
    else:
        policies = db.query(Policy).filter(Policy.user_id == current_user.id).offset(skip).limit(limit).all()
    return policies

@app.get("/policies/{policy_id}", response_model=PolicyResponse, tags=["Policies"])
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Check permission
    if current_user.role != UserRole.ADMIN and policy.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this policy")
    
    return policy

@app.patch("/policies/{policy_id}/activate", response_model=PolicyResponse, tags=["Policies"])
def activate_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.status = PolicyStatus.ACTIVE
    db.commit()
    db.refresh(policy)
    
    logger.info(f"Policy activated: {policy.policy_number}")
    return policy

# Claims endpoints
@app.post("/claims", response_model=ClaimResponse, tags=["Claims"])
def create_claim(
    claim: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify policy belongs to user
    policy = db.query(Policy).filter(Policy.id == claim.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if policy.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to create claim for this policy")
    
    if policy.status != PolicyStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Policy is not active")
    
    db_claim = Claim(
        claim_number=generate_claim_number(),
        user_id=current_user.id,
        **claim.model_dump()
    )
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    
    logger.info(f"New claim created: {db_claim.claim_number} for policy {policy.policy_number}")
    return db_claim

@app.get("/claims", response_model=List[ClaimResponse], tags=["Claims"])
def get_claims(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ClaimStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Claim)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Claim.user_id == current_user.id)
    
    if status:
        query = query.filter(Claim.status == status)
    
    claims = query.offset(skip).limit(limit).all()
    return claims

@app.get("/claims/{claim_id}", response_model=ClaimResponse, tags=["Claims"])
def get_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if current_user.role != UserRole.ADMIN and claim.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this claim")
    
    return claim

@app.patch("/claims/{claim_id}", response_model=ClaimResponse, tags=["Claims"])
def update_claim(
    claim_id: int,
    claim_update: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # Only admin or agent can update claims
    if current_user.role not in [UserRole.ADMIN, UserRole.AGENT]:
        raise HTTPException(status_code=403, detail="Not authorized to update claims")
    
    update_data = claim_update.model_dump(exclude_unset=True)
    if update_data.get("status"):
        claim.status = update_data["status"]
        claim.reviewed_by = current_user.id
        claim.review_date = datetime.utcnow()
    
    if update_data.get("approved_amount") is not None:
        claim.approved_amount = update_data["approved_amount"]
    
    if update_data.get("notes"):
        claim.notes = update_data["notes"]
    
    claim.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(claim)
    
    logger.info(f"Claim updated: {claim.claim_number} by {current_user.username}")
    return claim

# Payments endpoints
@app.post("/payments", response_model=PaymentResponse, tags=["Payments"])
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify policy
    policy = db.query(Policy).filter(Policy.id == payment.policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if policy.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to make payment for this policy")
    
    db_payment = Payment(
        payment_reference=generate_payment_reference(),
        user_id=current_user.id,
        **payment.model_dump()
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    
    logger.info(f"Payment created: {db_payment.payment_reference} for policy {policy.policy_number}")
    return db_payment

@app.get("/payments", response_model=List[PaymentResponse], tags=["Payments"])
def get_payments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == UserRole.ADMIN:
        payments = db.query(Payment).offset(skip).limit(limit).all()
    else:
        payments = db.query(Payment).filter(Payment.user_id == current_user.id).offset(skip).limit(limit).all()
    return payments

# Dashboard endpoints
@app.get("/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == UserRole.ADMIN:
        total_users = db.query(User).count()
        total_policies = db.query(Policy).count()
        active_policies = db.query(Policy).filter(Policy.status == PolicyStatus.ACTIVE).count()
        total_claims = db.query(Claim).count()
        pending_claims = db.query(Claim).filter(Claim.status == ClaimStatus.SUBMITTED).count()
        total_revenue = db.query(Payment).count() * 1000  # Simplified calculation
        
        return {
            "total_users": total_users,
            "total_policies": total_policies,
            "active_policies": active_policies,
            "total_claims": total_claims,
            "pending_claims": pending_claims,
            "total_revenue": total_revenue
        }
    else:
        user_policies = db.query(Policy).filter(Policy.user_id == current_user.id).count()
        user_active_policies = db.query(Policy).filter(
            Policy.user_id == current_user.id,
            Policy.status == PolicyStatus.ACTIVE
        ).count()
        user_claims = db.query(Claim).filter(Claim.user_id == current_user.id).count()
        user_payments = db.query(Payment).filter(Payment.user_id == current_user.id).count()
        
        return {
            "total_policies": user_policies,
            "active_policies": user_active_policies,
            "total_claims": user_claims,
            "total_payments": user_payments
        }

# Admin endpoints
@app.get("/admin/users", response_model=List[UserResponse], tags=["Admin"])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.patch("/admin/users/{user_id}/deactivate", response_model=UserResponse, tags=["Admin"])
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    
    logger.info(f"User deactivated: {user.username} by admin {current_user.username}")
    return user

# Reports endpoints
@app.get("/reports/claims-summary", tags=["Reports"])
def get_claims_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Claim)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Claim.user_id == current_user.id)
    
    if start_date:
        query = query.filter(Claim.claim_date >= start_date)
    if end_date:
        query = query.filter(Claim.claim_date <= end_date)
    
    claims = query.all()
    
    summary = {
        "total_claims": len(claims),
        "total_claimed_amount": sum(c.claim_amount for c in claims),
        "total_approved_amount": sum(c.approved_amount for c in claims),
        "by_status": {
            "submitted": len([c for c in claims if c.status == ClaimStatus.SUBMITTED]),
            "under_review": len([c for c in claims if c.status == ClaimStatus.UNDER_REVIEW]),
            "approved": len([c for c in claims if c.status == ClaimStatus.APPROVED]),
            "rejected": len([c for c in claims if c.status == ClaimStatus.REJECTED]),
            "paid": len([c for c in claims if c.status == ClaimStatus.PAID])
        }
    }
    
    return summary

@app.get("/reports/revenue-summary", tags=["Reports"])
def get_revenue_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin)
):
    query = db.query(Payment)
    
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    
    payments = query.all()
    
    summary = {
        "total_payments": len(payments),
        "total_revenue": sum(p.amount for p in payments),
        "average_payment": sum(p.amount for p in payments) / len(payments) if payments else 0,
        "by_method": {}
    }
    
    # Group by payment method
    from collections import defaultdict
    method_totals = defaultdict(float)
    for payment in payments:
        method_totals[payment.payment_method] += payment.amount
    
    summary["by_method"] = dict(method_totals)
    
    return summary

# Error handlers - Fixed version
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8001))  # Changed default port to 8001
    
    logger.info(f"Starting Production ACP Healthcare Insurance System on port {port}")
    logger.info(f"System accessible at http://localhost:{port}")
    logger.info(f"API documentation at http://localhost:{port}/api/docs")
    
    uvicorn.run(
        "main_system:app",
        host="0.0.0.0",
        port=port,
        reload=bool(os.getenv("DEBUG", False)),
        log_level="info"
    )