#!/usr/bin/env python3
"""
Prime VPN API Server Startup Script with Auto Setup
"""
import subprocess
import sys
import os
from pathlib import Path

def setup_environment():
    """Setup virtual environment and install dependencies"""
    venv_path = Path(".venv")
    
    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
    
    # Determine the correct python executable path
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Install dependencies
    if Path("requirements.txt").exists():
        print("📥 Installing dependencies...")
        subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], check=True)
    
    return str(python_exe)

if __name__ == "__main__":
    try:
        # Setup environment
        python_exe = setup_environment()
        
        print("🚀 Starting Prime VPN API Server...")
        print("📚 Documentation will be available at: http://localhost:8000/docs")
        print("🔍 Health check at: http://localhost:8000/health")
        print("⚡ API endpoints at: http://localhost:8000/api/v1/")
        print("\n" + "="*50)
        
        # Start server using virtual environment python
        subprocess.run([
            python_exe, "-c",
            "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True, log_level='info', access_log=True)"
        ])
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)