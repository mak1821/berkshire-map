from fastapi import FastAPI, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd
import secrets
from fastapi import HTTPException, status

app = FastAPI(title="Berkshire Map API")

# ---------- BASIC AUTH SETUP ----------
security = HTTPBasic()
USERNAME = "admin"         # choose any username you like
PASSWORD = "secret123"     # choose any password you like

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, USERNAME)
    correct_pass = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


# ---------- LOAD DATA ON STARTUP ----------
CLIENTS_URL = "https://drive.google.com/uc?export=download&id=1aBewbYdmS1XVhY82SMy_S_XCSd3q_4J_"

CLINICS_URL = "https://drive.google.com/uc?export=download&id=12JjKcSid2LxdhAEDElqqFt1LvczpcRWa"
clients = pd.read_csv(CLIENTS_URL)
clients["date"] = pd.to_datetime(
    clients["date"].astype(str).str.strip(),
    errors="coerce",
    dayfirst=True
)
clinics = pd.read_csv(CLINICS_URL)


# ---------- ROUTES ----------
@app.get("/")
def root():
    return {"message": "✅ Berkshire API is running securely!"}


@app.get("/data")
def get_data(
    from_date: str = Query("2023-01-01"),
    to_date: str = Query("2025-11-13"),
    pct: str = Query("All Regions"),
    auth: bool = Depends(authenticate)
):
    """Return filtered data only for authenticated users"""
    df = clients[
        (clients["date"] >= pd.Timestamp(from_date))
        & (clients["date"] <= pd.Timestamp(to_date))
    ]
    if pct != "All Regions":
        df = df[df["pct"] == pct]

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point",
                         "coordinates": [r.longitude, r.latitude]},
            "properties": {
                "clientid": r.clientid,
                "pct": r.pct,
                "date": str(r.date.date()),
            },
        }
        for _, r in df.dropna(subset=["latitude", "longitude"]).iterrows()
    ]
    return {"type": "FeatureCollection", "features": features}