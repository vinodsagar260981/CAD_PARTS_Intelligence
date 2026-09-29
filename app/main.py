from fastapi import FastAPI
from app.routes.cad import router as cad_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="CAD Part Inspector API")

app.mount("/images", StaticFiles(directory="app/images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(cad_router)


@app.get("/")
def root():
    return {
        "message": "CAD Part Inspector API is running"
    }
    
    
