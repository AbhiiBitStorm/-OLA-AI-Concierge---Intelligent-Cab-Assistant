import json
import os
from datetime import datetime
from typing import Dict, List
from threading import Thread

class SimpleDatabase:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(current_dir, "..", "data")
        self.data_path = os.path.abspath(self.data_path)
        self.ensure_files()
    
    def ensure_files(self):
        os.makedirs(self.data_path, exist_ok=True)
        
        files = {
            "bookings.json": {"bookings": [], "last_id": 0},
            "users.json": {"users": {}},
            "conversations.json": {"chats": []}
        }
        
        for filename, default_data in files.items():
            filepath = os.path.join(self.data_path, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f)
    
    def read_data(self, filename: str) -> Dict:
        filepath = os.path.join(self.data_path, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def write_data(self, filename: str, data: Dict):
        filepath = os.path.join(self.data_path, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Write error: {e}")
    
    def add_booking(self, booking_data: Dict) -> int:
        data = self.read_data("bookings.json")
        booking_id = data.get("last_id", 0) + 1
        booking_data["id"] = booking_id
        booking_data["timestamp"] = datetime.now().isoformat()
        
        if "bookings" not in data:
            data["bookings"] = []
        data["bookings"].append(booking_data)
        data["last_id"] = booking_id
        
        self.write_data("bookings.json", data)
        return booking_id
    
    def get_booking(self, booking_id: int) -> Dict:
        data = self.read_data("bookings.json")
        for booking in data.get("bookings", []):
            if booking.get("id") == booking_id:
                return booking
        return None
    
    def save_conversation(self, user_id: str, message: str, response: str):
        """Async save - doesn't block response"""
        def _save():
            data = self.read_data("conversations.json")
            if "chats" not in data:
                data["chats"] = []
            
            data["chats"].append({
                "user_id": user_id,
                "message": message,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 500
            if len(data["chats"]) > 500:
                data["chats"] = data["chats"][-500:]
            
            self.write_data("conversations.json", data)
        
        # Run in background
        Thread(target=_save, daemon=True).start()
    
    def get_user_history(self, user_id: str) -> List[Dict]:
        data = self.read_data("conversations.json")
        chats = data.get("chats", [])
        user_chats = [c for c in chats if c.get("user_id") == user_id]
        return user_chats[-5:] if user_chats else []