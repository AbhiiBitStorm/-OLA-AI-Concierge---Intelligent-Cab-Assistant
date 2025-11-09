from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_model import MistralAssistant
from services import SimpleDatabase

# Initialize FastAPI
app = FastAPI(title="OLA AI Concierge API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PRE-INITIALIZE - Load model at startup
print("⚡ Pre-loading AI model for fast responses...")
ai_assistant = MistralAssistant()
db = SimpleDatabase()
print("✅ System ready!")

# Request Models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    context_type: Optional[str] = "general"

class BookingRequest(BaseModel):
    user_id: str
    pickup: str
    drop: str
    cab_type: str = "mini"
    schedule_time: Optional[str] = None

class FareRequest(BaseModel):
    pickup: str
    drop: str
    cab_type: str = "mini"

@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("⚡ OLA AI CONCIERGE - ULTRA FAST MODE")
    print("="*60)
    print("🚀 Server ready at: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")

@app.get("/")
async def root():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return HTMLResponse("""
    <html>
        <head>
            <title>OLA AI Concierge</title>
            <style>
                body {
                    font-family: Arial;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #000, #1a1a1a);
                    color: white;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 20px;
                }
                h1 { color: #00D100; }
                a {
                    display: inline-block;
                    margin: 10px;
                    padding: 15px 30px;
                    background: #00D100;
                    color: black;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚡ OLA AI Concierge - ULTRA FAST</h1>
                <p>Lightning-fast AI responses powered by Mistral-7B</p>
                <a href="/docs">📚 API Docs</a>
                <a href="/health">💚 Health</a>
            </div>
        </body>
    </html>
    """)

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Ultra-fast chat endpoint"""
    try:
        user_id = request.user_id or str(uuid.uuid4())
        
        # Get minimal history (only last 2)
        history = db.get_user_history(user_id)[-2:] if request.user_id else []
        
        # Generate fast response
        response = ai_assistant.generate_response(
            request.message, 
            request.context_type,
            history
        )
        
        # Save async (don't wait)
        db.save_conversation(user_id, request.message, response)
        
        # Check booking intent (fast keyword check)
        is_booking = any(w in request.message.lower() for w in ["book", "ride", "cab", "taxi"])
        
        result = {
            "response": response,
            "user_id": user_id,
            "intent": "booking" if is_booking else "general",
            "timestamp": datetime.now().isoformat()
        }
        
        if is_booking:
            details = ai_assistant.extract_booking_details(request.message)
            result["extracted_details"] = details
            result["quick_actions"] = ["Book Now", "Change Location"]
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "response": "I can help you book a cab! Where would you like to go?",
            "user_id": request.user_id or str(uuid.uuid4()),
            "intent": "general"
        }

@app.post("/api/book")
async def book_ride(request: BookingRequest):
    """Instant booking"""
    try:
        booking_data = {
            "user_id": request.user_id,
            "pickup": request.pickup,
            "drop": request.drop,
            "cab_type": request.cab_type,
            "status": "confirmed",
            "driver": {
                "name": "Rajesh Kumar",
                "rating": 4.8,
                "vehicle": "Swift Dzire",
                "number": "MH 01 AB 1234",
                "phone": "+91 98765XXXXX"
            },
            "otp": str(uuid.uuid4())[:4].upper(),
            "eta": "5 mins"
        }
        
        booking_id = db.add_booking(booking_data)
        
        # Instant fare calculation
        fare_info = ai_assistant.calculate_fare_estimate(
            request.pickup, request.drop, request.cab_type
        )
        
        return {
            "booking_id": booking_id,
            "message": f"✅ Booking confirmed! Your {request.cab_type} arrives in 5 mins.",
            "booking_details": booking_data,
            "fare_estimate": fare_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/track/{booking_id}")
async def track_ride(booking_id: int):
    """Instant tracking"""
    booking = db.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        "booking_id": booking_id,
        "status": booking.get("status", "active"),
        "driver_location": {
            "lat": 19.0760 + (0.001 * booking_id),
            "lng": 72.8777 + (0.001 * booking_id)
        },
        "eta": booking.get("eta", "2 mins"),
        "driver": booking.get("driver", {})
    }

@app.post("/api/fare")
async def calculate_fare(request: FareRequest):
    """Instant fare calculation"""
    fare_info = ai_assistant.calculate_fare_estimate(
        request.pickup, request.drop, request.cab_type
    )
    
    return {
        "fare_details": fare_info,
        "explanation": f"Estimated {fare_info['distance_km']}km journey with {request.cab_type}",
        "payment_options": ["Cash", "UPI", "Card", "Ola Money"],
        "promo_codes": ["OLANEW", "RIDE50"]
    }

@app.post("/api/support")
async def customer_support(request: ChatRequest):
    """Fast support"""
    response = ai_assistant.generate_response(request.message, "support")
    
    urgent = any(w in request.message.lower() for w in ["accident", "emergency", "lost"])
    
    return {
        "response": response,
        "is_urgent": urgent,
        "ticket_id": str(uuid.uuid4())[:8].upper(),
        "helpful_articles": ["Refund policy", "Lost items", "Safety"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "loaded",
        "mode": "ultra-fast",
        "timestamp": datetime.now().isoformat()
    }

# Mount static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")