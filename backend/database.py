from tinydb import TinyDB, Query

class OlaDatabase:
    def __init__(self):
        self.db = TinyDB('../data/ola_database.json')
        self.bookings = self.db.table('bookings')
        self.users = self.db.table('users')
        self.fares = self.db.table('fares')
        self.chats = self.db.table('chats')
    
    def add_booking(self, data):
        return self.bookings.insert(data)
    
    def get_booking(self, booking_id):
        Booking = Query()
        return self.bookings.search(Booking.id == booking_id)
    
    def update_booking(self, booking_id, data):
        Booking = Query()
        return self.bookings.update(data, Booking.id == booking_id)