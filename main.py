from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Snow Lens Bouncer API",
    description="Secure cloud proxy for Bimodal Framework Prompts and Credit Metering",
    version="1.0.0",
)

# Enable CORS for desktop client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "service": "Snow Lens Bouncer API"}

@app.get("/health")
def health_check():
    return {"health": "ok"}