"""
Launcher script for Clinic Helpdesk KB Portal.
Starts the FastAPI backend and Streamlit frontend concurrently or individually.

Usage:
    python run.py            # Starts both FastAPI and Streamlit
    python run.py --backend  # Starts only FastAPI backend
    python run.py --frontend # Starts only Streamlit frontend
"""
import sys
import os
import subprocess
import time
import argparse


def start_backend(python_exe: str):
    print("🚀 Starting FastAPI backend on http://127.0.0.1:8000 ...")
    cmd = [python_exe, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    return subprocess.Popen(cmd)


def start_frontend(python_exe: str):
    print("🌐 Starting Streamlit frontend on http://127.0.0.1:8501 ...")
    cmd = [python_exe, "-m", "streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.headless", "true"]
    return subprocess.Popen(cmd)


def main():
    parser = argparse.ArgumentParser(description="Clinic Helpdesk KB Portal Launcher")
    parser.add_argument("--backend", action="store_true", help="Launch only FastAPI backend")
    parser.add_argument("--frontend", action="store_true", help="Launch only Streamlit frontend")
    args = parser.parse_args()

    python_exe = sys.executable

    procs = []
    try:
        if args.backend:
            p = start_backend(python_exe)
            procs.append(p)
            p.wait()
        elif args.frontend:
            p = start_frontend(python_exe)
            procs.append(p)
            p.wait()
        else:
            # Launch both
            p_back = start_backend(python_exe)
            procs.append(p_back)
            time.sleep(3)  # Allow backend to initialize database & embeddings
            p_front = start_frontend(python_exe)
            procs.append(p_front)

            print("\n✨ Clinic Helpdesk KB Portal is LIVE!")
            print("👉 Patient & Admin Web Portal: http://127.0.0.1:8501")
            print("👉 API Documentation (Swagger): http://127.0.0.1:8000/docs")
            print("\nPress Ctrl+C to terminate both servers.\n")

            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down Clinic Helpdesk KB Portal...")
        for p in procs:
            p.terminate()
            p.wait()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()
