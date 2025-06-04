#!/usr/bin/env python3

import requests
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)

def health_check():
    """Check if the application is healthy"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            logging.info("✅ Application is healthy")
            return True
        else:
            logging.error(f"❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"❌ Health check failed: {e}")
        return False

def tigergraph_check():
    """Check TigerGraph connection"""
    try:
        response = requests.get('http://localhost:5000/api/test-connection', timeout=10)
        data = response.json()
        if data.get('status') == 'success':
            logging.info("✅ TigerGraph connection is healthy")
            return True
        else:
            logging.error(f"❌ TigerGraph check failed: {data.get('message')}")
            return False
    except Exception as e:
        logging.error(f"❌ TigerGraph check failed: {e}")
        return False

if __name__ == "__main__":
    while True:
        print(f"\n🔍 Running health checks at {datetime.now()}")
        
        app_healthy = health_check()
        tg_healthy = tigergraph_check()
        
        if not app_healthy or not tg_healthy:
            logging.error("❌ System is unhealthy!")
            # Here you could add alerting logic (email, Slack, etc.)
        
        time.sleep(300)  # Check every 5 minutes