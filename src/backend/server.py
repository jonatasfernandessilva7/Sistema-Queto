from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.backend.routes import api 
# from src.backend.db.initialize_db import initialize_app
# a linha acima só deve ser descomentada caso o banco tenha que ser reinicializado

app = FastAPI(title="Queto System - AI System CyberCrisis Management")

# initialize_app()
# a linha acima só deve ser descomentada caso o banco tenha que ser reinicializado

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)