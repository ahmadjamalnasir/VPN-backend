#!/usr/bin/env python3
"""
Prime VPN API Server Startup Script
"""
import uvicorn
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting Prime VPN API Server...")
    print("📚 Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Health check at: http://localhost:8000/health")
    print("⚡ API endpoints at: http://localhost:8000/api/v1/")
    print("\n" + "="*50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )