import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("⚡ OLA AI CONCIERGE - ULTRA FAST MODE")
    print("=" * 60)
    
    model_path = os.path.join(os.path.dirname(__file__), "..", "model", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    if not os.path.exists(model_path):
        print("❌ Model not found!")
        sys.exit(1)
    
    print(f"✅ Model: {os.path.basename(model_path)}")
    print("")
    print("📍 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("")
    print("⚡ Optimizations enabled:")
    print("   - Response caching")
    print("   - Rule-based responses")
    print("   - Reduced tokens (80)")
    print("   - Max threads (8)")
    print("   - Model pre-loading")
    print("")
    print("Press CTRL+C to stop")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="warning"  # Reduced logging for speed
    )