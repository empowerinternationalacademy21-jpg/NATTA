#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   CHOM — UNFILTERED                                          ║
║   Personal blog with Python Flask backend                    ║
║                                                              ║
║   SETUP (one time):                                          ║
║     pip install flask                                        ║
║                                                              ║
║   RUN:                                                       ║
║     python3 start.py                                         ║
║                                                              ║
║   OPEN:                                                      ║
║     http://localhost:5000                                    ║
║                                                              ║
║   ADMIN LOGIN (click "Open Studio" on the blog):             ║
║     Username:  chom123                                       ║
║     Password:  godislove1234                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from app import app, init_db

init_db()
print(__doc__)
app.run(debug=False, host='0.0.0.0', port=5000)
