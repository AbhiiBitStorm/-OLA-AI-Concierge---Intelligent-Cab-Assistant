import os
from llama_cpp import Llama
from typing import Dict, List
import re
import time

class MistralAssistant:
    _instance = None
    _model = None
    _initialized = False
    
    # Response cache for common queries
    _response_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MistralAssistant, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "..", "model", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
        model_path = os.path.abspath(model_path)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"⚡ Loading Optimized Mistral-7B...")
        
        try:
            self._model = Llama(
                model_path=model_path,
                n_ctx=1024,          # Reduced context for speed
                n_threads=8,         # Max threads for speed
                n_gpu_layers=0,
                verbose=False,
                n_batch=256,         # Smaller batch for faster inference
                use_mlock=True,      # Lock model in RAM
                use_mmap=True        # Use memory mapping
            )
            print("   ✅ Optimized model loaded!")
            self._initialized = True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise
        
        # Quick response templates
        self.quick_responses = {
            "greeting": "Hello! I'm your Ola AI assistant. How can I help you book a cab today?",
            "booking": "I'll help you book a cab. Please provide pickup and drop locations.",
            "fare": "I can calculate the fare for you. Please share your journey details.",
            "track": "You can track your ride using your booking ID.",
            "support": "I'm here to help! What issue are you facing?",
            "thanks": "You're welcome! Have a safe journey! 🚖",
            "cancel": "To cancel your booking, please provide the booking ID."
        }
    
    def generate_response(self, user_input: str, context_type: str = "general", history: List[Dict] = None) -> str:
        """Super fast response generation"""
        
        # Check cache first
        cache_key = f"{user_input.lower()[:50]}_{context_type}"
        if cache_key in self._response_cache:
            print("⚡ Using cached response")
            return self._response_cache[cache_key]
        
        # Quick pattern matching for instant responses
        user_lower = user_input.lower()
        
        # Instant responses for common queries
        if any(word in user_lower for word in ["hi", "hello", "hey", "namaste"]):
            return self.quick_responses["greeting"]
        
        if any(word in user_lower for word in ["thank", "thanks", "thx"]):
            return self.quick_responses["thanks"]
        
        if "track" in user_lower and "booking" in user_lower:
            return self.quick_responses["track"]
        
        if "cancel" in user_lower:
            return self.quick_responses["cancel"]
        
        # For booking queries - use rule-based + minimal AI
        if any(word in user_lower for word in ["book", "ride", "cab", "taxi"]):
            details = self.extract_booking_details(user_input)
            if details["pickup_location"] and details["drop_location"]:
                cab = details["cab_type"] or "mini"
                return f"Great! I can book a {cab} cab from {details['pickup_location']} to {details['drop_location']}. The estimated fare is ₹{self._quick_fare(10)} for 10km. Shall I confirm the booking?"
            else:
                return "I'll help you book a cab. Please tell me your pickup and drop locations."
        
        # For fare queries - instant calculation
        if any(word in user_lower for word in ["fare", "price", "cost", "charge"]):
            return "I can calculate the fare instantly! Mini: ₹8/km, Prime: ₹12/km, Auto: ₹7/km. Please share your route details."
        
        # Only use AI for complex queries
        if not self._model:
            return "How can I help you with your cab booking?"
        
        try:
            # Minimal AI generation
            start_time = time.time()
            
            simple_prompt = f"[INST] You are Ola assistant. Answer briefly in 1-2 sentences.\nUser: {user_input}\nAssistant: [/INST]"
            
            output = self._model(
                simple_prompt,
                max_tokens=80,        # Reduced from 200
                temperature=0.5,      # Lower for faster, more focused responses
                top_p=0.8,
                stop=["User:", "[INST]", "\n\n"],
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            response = response.replace("[/INST]", "").strip()
            
            elapsed = time.time() - start_time
            print(f"⚡ AI response in {elapsed:.2f}s")
            
            # Cache the response
            if len(self._response_cache) < 100:  # Keep cache small
                self._response_cache[cache_key] = response
            
            return response if response else "How can I help you today?"
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return "I can help you book a cab, calculate fares, or track your ride. What would you like?"
    
    def extract_booking_details(self, user_input: str) -> Dict:
        """Fast regex-based extraction"""
        details = {
            "pickup_location": None,
            "drop_location": None,
            "cab_type": None,
            "time": None
        }
        
        text_lower = user_input.lower()
        
        # Cab type
        if "mini" in text_lower:
            details["cab_type"] = "mini"
        elif "prime" in text_lower:
            details["cab_type"] = "prime"
        elif "auto" in text_lower:
            details["cab_type"] = "auto"
        
        # Locations
        from_patterns = [
            r'from\s+([A-Za-z\s]+?)(?:\s+to|\s+at|$)',
            r'pickup\s+([A-Za-z\s]+?)(?:\s+to|\s+at|$)',
        ]
        to_patterns = [
            r'to\s+([A-Za-z\s]+?)(?:\s+at|\s+for|$)',
            r'drop\s+([A-Za-z\s]+?)(?:\s+at|\s+for|$)',
        ]
        
        for pattern in from_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["pickup_location"] = match.group(1).strip().title()
                break
        
        for pattern in to_patterns:
            match = re.search(pattern, text_lower)
            if match:
                details["drop_location"] = match.group(1).strip().title()
                break
        
        return details
    
    def _quick_fare(self, distance: int) -> int:
        """Instant fare calculation"""
        return 40 + (8 * distance)
    
    def calculate_fare_estimate(self, pickup: str, drop: str, cab_type: str) -> Dict:
        """Instant fare calculation"""
        fares = {
            "mini": {"base": 40, "per_km": 8},
            "prime": {"base": 60, "per_km": 12},
            "auto": {"base": 25, "per_km": 7}
        }
        
        cab_fare = fares.get(cab_type.lower(), fares["mini"])
        
        # Quick distance estimation
        estimated_distance = 10  # Default
        
        total = cab_fare["base"] + (cab_fare["per_km"] * estimated_distance)
        
        return {
            "distance_km": estimated_distance,
            "base_fare": cab_fare["base"],
            "per_km": cab_fare["per_km"],
            "estimated_total": int(total),
            "surge_multiplier": 1.0
        }