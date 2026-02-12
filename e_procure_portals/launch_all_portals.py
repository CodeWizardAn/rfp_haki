"""
Launch all 5 e-procurement portals simultaneously.
Each portal runs on its own port (5001-5005).
"""
import subprocess
import sys
import os
import time
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTAL_APP = os.path.join(BASE_DIR, "portal_app.py")

PORTALS = ["portal_1", "portal_2", "portal_3", "portal_4", "portal_5"]

processes = []


def launch_all():
    global processes
    print("=" * 70)
    print("  🚀 Launching All E-Procurement Portals")
    print("=" * 70)
    
    for portal_id in PORTALS:
        cmd = [sys.executable, PORTAL_APP, "--portal", portal_id]
        proc = subprocess.Popen(cmd, cwd=BASE_DIR)
        processes.append((portal_id, proc))
        print(f"  ✅ Started {portal_id} (PID: {proc.pid})")
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("  All portals are running:")
    print("    🏛️  GovProcure India      → http://localhost:5001")
    print("    🛒 TenderBazaar           → http://localhost:5002")
    print("    📋 eProcure Central       → http://localhost:5003")
    print("    🤝 BidConnect             → http://localhost:5004")
    print("    🧠 SmartTender Hub        → http://localhost:5005")
    print("=" * 70)
    print("\n  Press Ctrl+C to stop all portals.\n")
    
    try:
        while True:
            # Check if any process died
            for portal_id, proc in processes:
                if proc.poll() is not None:
                    print(f"  ⚠️  {portal_id} exited with code {proc.returncode}")
            time.sleep(2)
    except KeyboardInterrupt:
        shutdown()


def shutdown():
    print("\n\n  🛑 Shutting down all portals...")
    for portal_id, proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
            print(f"  ✅ Stopped {portal_id}")
        except Exception:
            proc.kill()
            print(f"  ⚠️  Force-killed {portal_id}")
    print("  All portals stopped.\n")


if __name__ == "__main__":
    launch_all()
