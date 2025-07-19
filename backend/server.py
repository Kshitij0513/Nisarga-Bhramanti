from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import base64
from pathlib import Path
from pydantic import BaseModel, Field, validator, ValidationError
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date
from dateutil.parser import parse as parse_date

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Advanced validation utilities
def validate_aadhaar(aadhaar_number: str) -> bool:
    """Validate Aadhaar number with advanced checks including Verhoeff algorithm"""
    if not aadhaar_number or len(aadhaar_number) != 12:
        return False
    
    if not aadhaar_number.isdigit():
        return False
    
    # Check if all digits are the same (invalid)
    if len(set(aadhaar_number)) == 1:
        return False
    
    # Verhoeff algorithm implementation for Aadhaar
    verhoeff_table_d = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]
    
    verhoeff_table_p = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
        [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
    ]
    
    verhoeff_table_inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
    
    def verhoeff_checksum(number_string):
        c = 0
        for i, digit in enumerate(reversed(number_string)):
            c = verhoeff_table_d[c][verhoeff_table_p[i % 8][int(digit)]]
        return verhoeff_table_inv[c]
    
    # Check if checksum is valid
    return verhoeff_checksum(aadhaar_number) == 0

def validate_pan(pan: str) -> bool:
    """Validate PAN number format"""
    if not pan or len(pan) != 10:
        return False
    
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pattern, pan.upper()))

def validate_mobile(mobile: str) -> bool:
    """Validate Indian mobile number"""
    if not mobile:
        return False
    
    # Remove all non-digits
    mobile = re.sub(r'\D', '', mobile)
    
    # Check length and pattern
    if len(mobile) == 10 and mobile[0] in '6789':
        return True
    elif len(mobile) == 12 and mobile.startswith('91') and mobile[2] in '6789':
        return True
    elif len(mobile) == 13 and mobile.startswith('+91') and mobile[3] in '6789':
        return True
    
    return False

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# Pydantic Models
class Tour(BaseModel):
    tour_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    destination: str
    start_date: date
    end_date: date
    price: float
    transport_mode: str
    description: str
    max_capacity: int = 50
    booked_count: int = 0
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TourCreate(BaseModel):
    name: str
    destination: str
    start_date: str  # Will be converted to date
    end_date: str    # Will be converted to date
    price: float
    transport_mode: str
    description: str
    max_capacity: int = 50
    image_url: Optional[str] = None

class Customer(BaseModel):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tour_id: str
    
    # Personal Details
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    
    # Contact Details
    email: str
    mobile: str
    address: str
    city: str
    state: str
    pincode: str
    
    # Identity Documents
    aadhaar_number: str
    pan_number: Optional[str] = None
    
    # Travel Details
    emergency_contact_name: str
    emergency_contact_number: str
    special_requirements: Optional[str] = None
    
    # Payment Details
    payment_status: str = "pending"  # pending, paid, partial
    amount_paid: float = 0.0
    payment_method: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('aadhaar_number')
    def validate_aadhaar_number(cls, v):
        if not validate_aadhaar(v):
            raise ValueError('Invalid Aadhaar number format or checksum')
        return v
    
    @validator('pan_number')
    def validate_pan_number(cls, v):
        if v and not validate_pan(v):
            raise ValueError('Invalid PAN number format')
        return v
    
    @validator('email')
    def validate_email_field(cls, v):
        if not validate_email(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('mobile')
    def validate_mobile_number(cls, v):
        if not validate_mobile(v):
            raise ValueError('Invalid mobile number format')
        return v

class CustomerCreate(BaseModel):
    tour_id: str
    first_name: str
    last_name: str
    date_of_birth: str  # Will be converted to date
    gender: str
    email: str
    mobile: str
    address: str
    city: str
    state: str
    pincode: str
    aadhaar_number: str
    pan_number: Optional[str] = None
    emergency_contact_name: str
    emergency_contact_number: str
    special_requirements: Optional[str] = None
    payment_method: Optional[str] = None

class Expense(BaseModel):
    expense_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tour_id: Optional[str] = None
    category: str  # transport, accommodation, food, guides, etc.
    description: str
    amount: float
    date: date
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExpenseCreate(BaseModel):
    tour_id: Optional[str] = None
    category: str
    description: str
    amount: float
    date: str  # Will be converted to date

# Initialize sample data
@api_router.on_event("startup")
async def initialize_sample_data():
    """Initialize sample tours if database is empty"""
    tours_count = await db.tours.count_documents({})
    if tours_count == 0:
        sample_tours = [
            {
                "tour_id": str(uuid.uuid4()),
                "name": "Magical Bhutan Adventure",
                "destination": "Thimphu, Paro, Punakha - Bhutan",
                "start_date": datetime(2025, 3, 15),
                "end_date": datetime(2025, 3, 22),
                "price": 85000.0,
                "transport_mode": "Flight + Local Transport",
                "description": "Experience the mystical kingdom of Bhutan with visits to ancient monasteries, stunning landscapes, and rich cultural heritage. Includes visits to Tiger's Nest Monastery, Punakha Dzong, and local markets.",
                "max_capacity": 25,
                "booked_count": 0,
                "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2070",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "tour_id": str(uuid.uuid4()),
                "name": "Sri Lanka Cultural Paradise",
                "destination": "Colombo, Kandy, Galle - Sri Lanka",
                "start_date": datetime(2025, 4, 10),
                "end_date": datetime(2025, 4, 18),
                "price": 65000.0,
                "transport_mode": "Flight + AC Bus",
                "description": "Discover the pearl of the Indian Ocean with golden beaches, ancient temples, tea plantations, and wildlife safaris. Visit Temple of the Tooth, Sigiriya Rock, and enjoy beach time in Galle.",
                "max_capacity": 30,
                "booked_count": 0,
                "image_url": "https://images.unsplash.com/photo-1581833971358-2c8b550f87b3?q=80&w=2071",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for tour in sample_tours:
            await db.tours.insert_one(tour)

# Tour Routes
# Helper function to convert datetime objects back to date objects for Pydantic models
def convert_datetime_to_date_for_tour(tour_data):
    """Convert datetime objects to date objects for tour data"""
    if 'start_date' in tour_data and isinstance(tour_data['start_date'], datetime):
        tour_data['start_date'] = tour_data['start_date'].date()
    if 'end_date' in tour_data and isinstance(tour_data['end_date'], datetime):
        tour_data['end_date'] = tour_data['end_date'].date()
    return tour_data

def convert_datetime_to_date_for_customer(customer_data):
    """Convert datetime objects to date objects for customer data"""
    if 'date_of_birth' in customer_data and isinstance(customer_data['date_of_birth'], datetime):
        customer_data['date_of_birth'] = customer_data['date_of_birth'].date()
    return customer_data

def convert_datetime_to_date_for_expense(expense_data):
    """Convert datetime objects to date objects for expense data"""
    if 'date' in expense_data and isinstance(expense_data['date'], datetime):
        expense_data['date'] = expense_data['date'].date()
    return expense_data

@api_router.get("/tours", response_model=List[Tour])
async def get_tours():
    tours = await db.tours.find().to_list(1000)
    return [Tour(**convert_datetime_to_date_for_tour(tour)) for tour in tours]

@api_router.post("/tours", response_model=Tour)
async def create_tour(tour_data: TourCreate):
    tour_dict = tour_data.dict()
    # Convert date strings to date objects
    tour_dict['start_date'] = parse_date(tour_dict['start_date']).date()
    tour_dict['end_date'] = parse_date(tour_dict['end_date']).date()
    tour_dict['created_at'] = datetime.utcnow()
    tour_dict['updated_at'] = datetime.utcnow()
    
    tour_obj = Tour(**tour_dict)
    
    # Convert date objects to datetime for MongoDB storage
    tour_dict_for_db = tour_obj.dict()
    tour_dict_for_db['start_date'] = datetime.combine(tour_dict_for_db['start_date'], datetime.min.time())
    tour_dict_for_db['end_date'] = datetime.combine(tour_dict_for_db['end_date'], datetime.min.time())
    
    await db.tours.insert_one(tour_dict_for_db)
    return tour_obj

@api_router.get("/tours/{tour_id}", response_model=Tour)
async def get_tour(tour_id: str):
    tour = await db.tours.find_one({"tour_id": tour_id})
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return Tour(**convert_datetime_to_date_for_tour(tour))

@api_router.put("/tours/{tour_id}", response_model=Tour)
async def update_tour(tour_id: str, tour_data: TourCreate):
    tour_dict = tour_data.dict()
    tour_dict['start_date'] = parse_date(tour_dict['start_date']).date()
    tour_dict['end_date'] = parse_date(tour_dict['end_date']).date()
    tour_dict['updated_at'] = datetime.utcnow()
    
    # Convert date objects to datetime for MongoDB storage
    tour_dict['start_date'] = datetime.combine(tour_dict['start_date'], datetime.min.time())
    tour_dict['end_date'] = datetime.combine(tour_dict['end_date'], datetime.min.time())
    
    result = await db.tours.update_one(
        {"tour_id": tour_id}, 
        {"$set": tour_dict}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    updated_tour = await db.tours.find_one({"tour_id": tour_id})
    return Tour(**convert_datetime_to_date_for_tour(updated_tour))

@api_router.delete("/tours/{tour_id}")
async def delete_tour(tour_id: str):
    result = await db.tours.delete_one({"tour_id": tour_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tour not found")
    return {"message": "Tour deleted successfully"}

# Customer Routes
@api_router.get("/customers", response_model=List[Customer])
async def get_customers(tour_id: Optional[str] = Query(None)):
    filter_query = {}
    if tour_id:
        filter_query["tour_id"] = tour_id
    
    customers = await db.customers.find(filter_query).to_list(1000)
    return [Customer(**convert_datetime_to_date_for_customer(customer)) for customer in customers]

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer_data: CustomerCreate):
    customer_dict = customer_data.dict()
    # Convert date string to date object
    customer_dict['date_of_birth'] = parse_date(customer_dict['date_of_birth']).date()
    customer_dict['created_at'] = datetime.utcnow()
    customer_dict['updated_at'] = datetime.utcnow()
    
    # Create customer with validation (this will trigger Pydantic validation)
    try:
        customer_obj = Customer(**customer_dict)
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    # Validate tour exists (after Pydantic validation)
    tour = await db.tours.find_one({"tour_id": customer_dict['tour_id']})
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    # Convert date objects to datetime for MongoDB storage
    customer_dict_for_db = customer_obj.dict()
    customer_dict_for_db['date_of_birth'] = datetime.combine(customer_dict_for_db['date_of_birth'], datetime.min.time())
    
    await db.customers.insert_one(customer_dict_for_db)
    
    # Update tour booked count
    await db.tours.update_one(
        {"tour_id": customer_dict['tour_id']},
        {"$inc": {"booked_count": 1}}
    )
    
    return customer_obj

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**convert_datetime_to_date_for_customer(customer))

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_data: CustomerCreate):
    customer_dict = customer_data.dict()
    customer_dict['date_of_birth'] = parse_date(customer_dict['date_of_birth']).date()
    customer_dict['updated_at'] = datetime.utcnow()
    
    # Convert date objects to datetime for MongoDB storage
    customer_dict['date_of_birth'] = datetime.combine(customer_dict['date_of_birth'], datetime.min.time())
    
    result = await db.customers.update_one(
        {"customer_id": customer_id}, 
        {"$set": customer_dict}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    updated_customer = await db.customers.find_one({"customer_id": customer_id})
    return Customer(**convert_datetime_to_date_for_customer(updated_customer))

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    # Get customer to find tour_id
    customer = await db.customers.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    result = await db.customers.delete_one({"customer_id": customer_id})
    
    # Update tour booked count
    await db.tours.update_one(
        {"tour_id": customer["tour_id"]},
        {"$inc": {"booked_count": -1}}
    )
    
    return {"message": "Customer deleted successfully"}

# Expense Routes
@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses(tour_id: Optional[str] = Query(None)):
    filter_query = {}
    if tour_id:
        filter_query["tour_id"] = tour_id
    
    expenses = await db.expenses.find(filter_query).to_list(1000)
    return [Expense(**convert_datetime_to_date_for_expense(expense)) for expense in expenses]

@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense_data: ExpenseCreate):
    expense_dict = expense_data.dict()
    expense_dict['date'] = parse_date(expense_dict['date']).date()
    expense_dict['created_at'] = datetime.utcnow()
    
    expense_obj = Expense(**expense_dict)
    
    # Convert date objects to datetime for MongoDB storage
    expense_dict_for_db = expense_obj.dict()
    expense_dict_for_db['date'] = datetime.combine(expense_dict_for_db['date'], datetime.min.time())
    
    await db.expenses.insert_one(expense_dict_for_db)
    return expense_obj

# Dashboard and Analytics Routes
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Get basic counts
    total_tours = await db.tours.count_documents({})
    total_customers = await db.customers.count_documents({})
    total_revenue = await db.customers.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_paid"}}}
    ]).to_list(1)
    
    total_expenses = await db.expenses.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]).to_list(1)
    
    revenue = total_revenue[0]["total"] if total_revenue else 0
    expenses = total_expenses[0]["total"] if total_expenses else 0
    
    # Get tour-wise data
    tour_stats = await db.customers.aggregate([
        {"$group": {
            "_id": "$tour_id",
            "customer_count": {"$sum": 1},
            "revenue": {"$sum": "$amount_paid"}
        }},
        {"$lookup": {
            "from": "tours",
            "localField": "_id",
            "foreignField": "tour_id",
            "as": "tour_info"
        }},
        {"$unwind": "$tour_info"}
    ]).to_list(100)
    
    return {
        "total_tours": total_tours,
        "total_customers": total_customers,
        "total_revenue": revenue,
        "total_expenses": expenses,
        "profit": revenue - expenses,
        "tour_stats": tour_stats
    }

# Validation Routes
@api_router.post("/validate/aadhaar")
async def validate_aadhaar_endpoint(aadhaar_data: dict):
    aadhaar_number = aadhaar_data.get("aadhaar_number", "")
    is_valid = validate_aadhaar(aadhaar_number)
    return {"valid": is_valid}

@api_router.post("/validate/pan")
async def validate_pan_endpoint(pan_data: dict):
    pan_number = pan_data.get("pan_number", "")
    is_valid = validate_pan(pan_number)
    return {"valid": is_valid}

@api_router.post("/validate/mobile")
async def validate_mobile_endpoint(mobile_data: dict):
    mobile_number = mobile_data.get("mobile", "")
    is_valid = validate_mobile(mobile_number)
    return {"valid": is_valid}

@api_router.post("/validate/email")
async def validate_email_endpoint(email_data: dict):
    email = email_data.get("email", "")
    is_valid = validate_email(email)
    return {"valid": is_valid}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()