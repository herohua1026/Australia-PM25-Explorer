"""Local or Railway launcher; same start.py convention as American Double Hero."""
import os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parent
port=int(os.environ.get('PORT','8502'))
host=os.environ.get('HOST','0.0.0.0' if 'RAILWAY_ENVIRONMENT' in os.environ else '127.0.0.1')
raise SystemExit(subprocess.call([sys.executable,'-m','streamlit','run',str(root/'app.py'),'--server.address='+host,'--server.port='+str(port),'--server.headless=true','--browser.gatherUsageStats=false'],cwd=root))
