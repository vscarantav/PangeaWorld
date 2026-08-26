# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PangeaWorld API")

# Configure CORS so the React frontend can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "PangeaWorld Game Server is running."}
