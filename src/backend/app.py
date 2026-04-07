from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.api.routes import auth

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Running!"}
