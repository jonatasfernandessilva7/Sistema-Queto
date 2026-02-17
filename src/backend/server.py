from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.backend.routes import Routes
from src.backend.database.InitializeConnectionWithDatabase import initialize_app
# the above line should only be uncommented if the database needs to be reinitialized

app = FastAPI(title="Queto System - Sistema de IA para Gerenciamento de Crises")

initialize_app()
# the above line should only be uncommented if the database needs to be reinitialized

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(Routes.router)