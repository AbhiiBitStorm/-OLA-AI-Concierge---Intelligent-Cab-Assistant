// ============================================
// OLA AI CONCIERGE - MAIN JAVASCRIPT
// ============================================

const API_BASE_URL = 'http://localhost:8000/api';
let userId = localStorage.getItem('ola_user_id') || generateUserId();
let currentBookingId = null;

// Generate unique user ID
function generateUserId() {
    const id = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('ola_user_id', id);
    return id;
}

// ============================================
// NAVIGATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Navigation buttons
    const navButtons = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.content-section');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetSection = btn.getAttribute('data-section');
            
            // Update active states
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            document.getElementById(`${targetSection}-section`).classList.add('active');
        });
    });
    
    // Message input enter key
    const messageInput = document.getElementById('messageInput');
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Booking form submission
    const bookingForm = document.getElementById('bookingForm');
    bookingForm.addEventListener('submit', handleBookingSubmit);
});

// ============================================
// CHAT FUNCTIONALITY
// ============================================

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    messageInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to backend
    fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            user_id: userId,
            context_type: 'general'
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        
        // Add bot response
        addMessageToChat(data.response, 'bot');
        
        // Handle special intents
        if (data.intent === 'booking' && data.extracted_details) {
            handleBookingIntent(data.extracted_details);
        }
        
        // Show quick actions if available
        if (data.quick_actions) {
            addQuickActions(data.quick_actions);
        }
    })
    .catch(error => {
        hideTypingIndicator();
        console.error('Error:', error);
        addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
        showToast('Connection error. Please check if backend is running.', 'error');
    });
}

function addMessageToChat(text, sender) {
    const messagesContainer = document.getElementById('messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = `avatar ${sender}-avatar`;
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = formatMessage(text);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessage(text) {
    // Convert markdown-like syntax to HTML
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert line breaks
    text = text.replace(/\n/g, '<br>');
    
    // Wrap in paragraph
    return `<p>${text}</p>`;
}

function addQuickActions(actions) {
    const messagesContainer = document.getElementById('messages');
    
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'quick-actions-container';
    actionsDiv.style.cssText = `
        display: flex;
        gap: 10px;
        padding: 10px 0;
        flex-wrap: wrap;
        margin-left: 52px;
    `;
    
    actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'quick-action-btn';
        btn.textContent = action;
        btn.style.cssText = `
            background: var(--ola-green);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.3s;
        `;
        btn.onclick = () => {
            sendQuickMessage(action);
            actionsDiv.remove();
        };
        actionsDiv.appendChild(btn);
    });
    
    messagesContainer.appendChild(actionsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function sendQuickMessage(message) {
    document.getElementById('messageInput').value = message;
    sendMessage();
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'flex';
    const messagesContainer = document.getElementById('messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'none';
}

function clearChat() {
    const messagesContainer = document.getElementById('messages');
    
    // Keep only welcome message
    const messages = messagesContainer.querySelectorAll('.message');
    messages.forEach((msg, index) => {
        if (index > 0) msg.remove();
    });
    
    showToast('Chat cleared successfully!');
}

// ============================================
// BOOKING FUNCTIONALITY
// ============================================

async function handleBookingSubmit(e) {
    e.preventDefault();
    
    const pickup = document.getElementById('pickup').value;
    const drop = document.getElementById('drop').value;
    const cabType = document.getElementById('cabType').value;
    const scheduleTime = document.getElementById('scheduleTime').value;
    
    showLoading();
    
    try {
        // First get fare estimate
        const fareResponse = await fetch(`${API_BASE_URL}/fare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pickup: pickup,
                drop: drop,
                cab_type: cabType
            })
        });
        
        const fareData = await fareResponse.json();
        
        // Show fare estimate
        displayFareEstimate(fareData);
        
        // Confirm booking
        setTimeout(async () => {
            const bookingResponse = await fetch(`${API_BASE_URL}/book`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    pickup: pickup,
                    drop: drop,
                    cab_type: cabType,
                    schedule_time: scheduleTime
                })
            });
            
            const bookingData = await bookingResponse.json();
            
            hideLoading();
            
            // Show confirmation
            displayBookingConfirmation(bookingData);
            
            // Save booking ID
            currentBookingId = bookingData.booking_id;
            
            showToast('🎉 Booking confirmed! Driver on the way.', 'success');
            
        }, 1500);
        
    } catch (error) {
        hideLoading();
        console.error('Booking error:', error);
        showToast('Booking failed. Please try again.', 'error');
    }
}

function displayFareEstimate(fareData) {
    const fareCard = document.getElementById('fareCard');
    const fareDetails = document.getElementById('fareDetails');
    
    fareDetails.innerHTML = `
        <div style="display: grid; gap: 15px;">
            <div style="display: flex; justify-content: space-between;">
                <span>📏 Distance:</span>
                <strong>${fareData.fare_details.distance_km} km</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>🚗 Base Fare:</span>
                <strong>₹${fareData.fare_details.base_fare}</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>📊 Per km charge:</span>
                <strong>₹${fareData.fare_details.per_km}/km</strong>
            </div>
            ${fareData.fare_details.surge_multiplier > 1 ? `
                <div style="display: flex; justify-content: space-between; color: var(--warning);">
                    <span>⚡ Surge Pricing:</span>
                    <strong>${fareData.fare_details.surge_multiplier}x</strong>
                </div>
            ` : ''}
            <hr>
            <div style="display: flex; justify-content: space-between; font-size: 18px; color: var(--ola-green);">
                <span>💰 Total Estimate:</span>
                <strong>₹${fareData.fare_details.estimated_total}</strong>
            </div>
            <div style="margin-top: 10px; padding: 10px; background: var(--bg-secondary); border-radius: 8px;">
                <small><i class="fas fa-info-circle"></i> ${fareData.explanation}</small>
            </div>
        </div>
    `;
    
    fareCard.style.display = 'block';
}

function displayBookingConfirmation(bookingData) {
    const confirmationDiv = document.getElementById('bookingConfirmation');
    const confirmationDetails = document.getElementById('confirmationDetails');
    
    const driver = bookingData.booking_details.driver;
    
    confirmationDetails.innerHTML = `
        <div style="background: var(--bg-secondary); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h4 style="margin-bottom: 15px;">📋 Booking Details</h4>
            <p><strong>Booking ID:</strong> #${bookingData.booking_id}</p>
            <p><strong>From:</strong> ${bookingData.booking_details.pickup}</p>
            <p><strong>To:</strong> ${bookingData.booking_details.drop}</p>
            <p><strong>Cab Type:</strong> ${bookingData.booking_details.cab_type.toUpperCase()}</p>
            <p><strong>OTP:</strong> <span style="font-size: 24px; color: var(--ola-green); font-weight: 700;">${bookingData.booking_details.otp}</span></p>
        </div>
        
        <div style="background: var(--bg-secondary); padding: 20px; border-radius: 12px;">
            <h4 style="margin-bottom: 15px;">🚗 Driver Details</h4>
            <p><strong>Name:</strong> ${driver.name}</p>
            <p><strong>Rating:</strong> ⭐ ${driver.rating}</p>
            <p><strong>Vehicle:</strong> ${driver.vehicle} (${driver.number})</p>
            <p><strong>Contact:</strong> ${driver.phone}</p>
            <p style="color: var(--ola-green); font-weight: 600; margin-top: 10px;">
                🕐 Arriving in ${bookingData.booking_details.eta}
            </p>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 20px;">
            <button onclick="trackRideFromBooking(${bookingData.booking_id})" 
                    style="padding: 12px; background: var(--ola-green); color: white; border: none; border-radius: 8px; cursor: pointer;">
                <i class="fas fa-location-arrow"></i> Track Ride
            </button>
            <button onclick="cancelBooking(${bookingData.booking_id})" 
                    style="padding: 12px; background: var(--danger); color: white; border: none; border-radius: 8px; cursor: pointer;">
                <i class="fas fa-times"></i> Cancel
            </button>
        </div>
    `;
    
    confirmationDiv.style.display = 'block';
    
    // Scroll to confirmation
    confirmationDiv.scrollIntoView({ behavior: 'smooth' });
}

function handleBookingIntent(details) {
    // Switch to booking tab and pre-fill form
    document.querySelector('[data-section="booking"]').click();
    
    if (details.pickup_location) {
        document.getElementById('pickup').value = details.pickup_location;
    }
    if (details.drop_location) {
        document.getElementById('drop').value = details.drop_location;
    }
    if (details.cab_type) {
        document.getElementById('cabType').value = details.cab_type.toLowerCase();
    }
}

// ============================================
// TRACKING FUNCTIONALITY
// ============================================

async function trackRide() {
    const bookingId = document.getElementById('bookingId').value;
    
    if (!bookingId) {
        showToast('Please enter a booking ID', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/track/${bookingId}`);
        const data = await response.json();
        
        hideLoading();
        
        displayTrackingInfo(data);
        
    } catch (error) {
        hideLoading();
        console.error('Tracking error:', error);
        showToast('Booking not found', 'error');
    }
}

function trackRideFromBooking(bookingId) {
    document.getElementById('bookingId').value = bookingId;
    document.querySelector('[data-section="track"]').click();
    
    setTimeout(() => {
        trackRide();
    }, 300);
}

function displayTrackingInfo(data) {
    const trackingInfo = document.getElementById('trackingInfo');
    const driverDetails = document.getElementById('driverDetails');
    const rideStatus = document.getElementById('rideStatus');
    
    const driver = data.driver;
    
    driverDetails.innerHTML = `
        <h3>${driver.name}</h3>
        <p>⭐ ${driver.rating} Rating</p>
        <p>${driver.vehicle} - ${driver.number}</p>
        <p><i class="fas fa-phone"></i> ${driver.phone}</p>
    `;
    
    rideStatus.innerHTML = `
        <div style="display: grid; gap: 15px; padding: 20px; background: var(--bg-secondary); border-radius: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><i class="fas fa-info-circle"></i> Status:</span>
                <strong style="color: var(--ola-green); text-transform: uppercase;">${data.status}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><i class="fas fa-clock"></i> ETA:</span>
                <strong>${data.eta}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><i class="fas fa-map-marker-alt"></i> Location:</span>
                <strong>Lat: ${data.driver_location.lat.toFixed(4)}, Lng: ${data.driver_location.lng.toFixed(4)}</strong>
            </div>
        </div>
    `;
    
    trackingInfo.style.display = 'block';
}

function cancelBooking(bookingId) {
    if (confirm('Are you sure you want to cancel this booking?')) {
        showLoading();
        
        // Simulate cancel API call
        setTimeout(() => {
            hideLoading();
            showToast('Booking cancelled successfully', 'success');
            document.getElementById('bookingConfirmation').style.display = 'none';
        }, 1000);
    }
}

// ============================================
// SUPPORT FUNCTIONALITY
// ============================================

function sendSupportMessage(issue) {
    // Switch to chat and send support message
    document.querySelector('[data-section="chat"]').click();
    
    setTimeout(() => {
        const supportMessage = `I need help with: ${issue}`;
        document.getElementById('messageInput').value = supportMessage;
        sendMessage();
    }, 300);
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };
    
    toast.textContent = `${icons[type] || icons.info} ${message}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============================================
// WEBSOCKET (Optional - Real-time chat)
// ============================================

function connectWebSocket() {
    const ws = new WebSocket('ws://localhost:8000/ws/chat');
    
    ws.onopen = () => {
        console.log('✅ WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
            addMessageToChat(data.response, 'bot');
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
    };
    
    return ws;
}

// Initialize WebSocket (uncomment to use)
// const wsConnection = connectWebSocket();

// ============================================
// VOICE INPUT (Optional Enhancement)
// ============================================

document.querySelector('.voice-btn')?.addEventListener('click', () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'en-IN';
        recognition.interimResults = false;
        
        recognition.onstart = () => {
            document.querySelector('.voice-btn i').className = 'fas fa-microphone-slash';
            document.querySelector('.voice-btn').style.background = 'var(--danger)';
            showToast('Listening...', 'info');
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById('messageInput').value = transcript;
            showToast('Voice input captured!', 'success');
        };
        
        recognition.onerror = (event) => {
            showToast('Voice input error', 'error');
        };
        
        recognition.onend = () => {
            document.querySelector('.voice-btn i').className = 'fas fa-microphone';
            document.querySelector('.voice-btn').style.background = 'white';
        };
        
        recognition.start();
    } else {
        showToast('Voice input not supported in this browser', 'error');
    }
});

// ============================================
// INITIALIZE
// ============================================

console.log('%c🚖 OLA AI Concierge Initialized', 'color: #00D100; font-size: 16px; font-weight: bold;');
console.log('%cUser ID:', 'color: #666;', userId);
console.log('%cBackend:', 'color: #666;', API_BASE_URL);

// Welcome message in console
console.log(`
╔══════════════════════════════════════╗
║   OLA AI CONCIERGE - READY! 🚀       ║
║   Powered by Mistral-7B              ║
╚══════════════════════════════════════╝
`);