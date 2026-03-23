#!/usr/bin/env python3
"""
Auto Alive - Keeps Your App Running 24/7
Monitors and restarts if needed
"""

import os
import sys
import time
import subprocess
import requests
import logging
from datetime import datetime

# =================================================================================================
# CONFIGURATION
# =================================================================================================

APP_URL = os.getenv("APP_URL", "https://kinva-master.onrender.com")
HEALTH_ENDPOINT = "/api/health"
CHECK_INTERVAL = 60  # seconds
MAX_RETRIES = 3
LOG_FILE = "auto_alive.log"

# =================================================================================================
# LOGGING
# =================================================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =================================================================================================
# AUTO ALIVE FUNCTIONS
# =================================================================================================

def check_alive():
    """Check if app is alive"""
    try:
        url = f"{APP_URL}{HEALTH_ENDPOINT}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ App is alive - {datetime.now()}")
            return True
        else:
            logger.warning(f"⚠️ App returned {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ App is dead: {e}")
        return False

def restart_locally():
    """Restart local app"""
    try:
        # Kill existing process
        subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
        time.sleep(2)
        
        # Start new process
        subprocess.Popen(
            ["uvicorn", "kinva_master:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        logger.info("🔄 Local app restarted")
        return True
    except Exception as e:
        logger.error(f"Failed to restart: {e}")
        return False

def trigger_render_deploy():
    """Trigger Render redeploy (optional)"""
    # Add your Render API key here if you want auto redeploy
    render_api_key = os.getenv("RENDER_API_KEY", "")
    render_service_id = os.getenv("RENDER_SERVICE_ID", "")
    
    if not render_api_key or not render_service_id:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {render_api_key}"}
        url = f"https://api.render.com/v1/services/{render_service_id}/deploys"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201:
            logger.info("🚀 Render redeploy triggered")
            return True
    except:
        pass
    
    return False

# =================================================================================================
# MAIN LOOP
# =================================================================================================

def main():
    """Main auto alive loop"""
    logger.info("=" * 50)
    logger.info("🟢 AUTO ALIVE MONITOR STARTED")
    logger.info(f"📡 Monitoring: {APP_URL}")
    logger.info(f"⏱️ Check interval: {CHECK_INTERVAL}s")
    logger.info("=" * 50)
    
    failures = 0
    
    while True:
        try:
            is_alive = check_alive()
            
            if not is_alive:
                failures += 1
                logger.warning(f"⚠️ Failure #{failures}")
                
                if failures >= MAX_RETRIES:
                    logger.error("❌ Max retries reached! Restarting...")
                    
                    # Try to restart
                    if restart_locally():
                        failures = 0
                        logger.info("✅ Restart successful")
                    else:
                        logger.error("❌ Restart failed")
            else:
                failures = 0
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("🛑 Auto alive stopped")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
