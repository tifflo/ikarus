from fastapi import FastAPI, Response, UploadFile, Request, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from tempfile import NamedTemporaryFile

from datetime import date
from pydantic import BaseModel
from typing import Optional, List, Dict

from functools import wraps
import json
# from ikarus import set_flight
# from ikarus import get_airport_matches, calculate_emissions

from src import make_history, build_key, get_airport_matches

from env import COOKIE_NAME

#  uvicorn main:app --reload

# Initialize the FastAPI app
app = FastAPI(
    title="ikarus.flights",
    description="This is ikarus.flights documentation",
    version="1.0.0"
)


# Allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow only the frontend's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)



class AirportMatch(BaseModel):
    matched: List[str]
    iata: str

class SuggestionAirportResponse(BaseModel):
    icaos: Dict[str, AirportMatch]

def get_cookie(request):
    cookie_value = request.cookies.get(COOKIE_NAME)
    if cookie_value:
        return json.loads(cookie_value)
    return None

def session_check(func):
    @wraps(func)
    async def session_check_wrapper(request: Request, *args, **kwargs):
        if get_cookie(request) is not None:
            return await func(request, *args, **kwargs)  # Call the decorated function
        raise HTTPException(
            status_code=400,
            detail="session not found - use /create or /upload"
        )
    return session_check_wrapper

@app.post("/history", tags=["History"])
async def create_history(response: Response):
    '''
    Create a new session. This will always be an empty session. This will create or overwrite an existing session.
    '''
    response.set_cookie(key=COOKIE_NAME, value=json.dumps({"ORDER": []}),  httponly=True, secure=True, samesite='Lax')
    return {"message": "created"}

@app.put("/history", tags=["History"])
async def upload_history(file: UploadFile, response: Response):
    '''
    Upload an existsing record to continue to add to it within a session. This will create or overwrite an existing session.
    '''
    content = await file.read()
    flight_history= json.loads(content.decode('utf-8'))
    response.set_cookie(key=COOKIE_NAME, value=json.dumps({"ORDER":flight_history["ORDER"]}))
    return  {"message": "uploaded"}

@app.get("/history", tags=["History"])
@session_check
async def download_history(request: Request):
    '''
    Download an existing session file.
    '''
    flight_history = get_cookie(request)
    full_history = make_history(flight_history["ORDER"])
    with NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".json") as tmpfile:
        json.dump(full_history, tmpfile, ensure_ascii=False, indent=4)
        tmpfile_path = tmpfile.name
    return FileResponse(tmpfile_path, media_type="application/json", filename="flight_history.json", headers={"Content-Disposition": "attachment; filename=flight_history.json"})

@app.delete("/history", tags=["History"])
async def delete_history(response: Response):
    '''
    Delete an existing session file.
    '''
    response.delete_cookie(COOKIE_NAME)
    return {"message": "deleted"}


@app.post("/flight", tags=["Flight"])
@session_check
async def add_flight(request: Request = None,
                response: Response = None, 
                departure: str = Query(..., description="The IATA departure code"), 
                arrival: str = Query(..., description="The IATA arrival code"),
                date: date = Query(..., description="The flight date (in YYYY-MM-DD format)"),
                order: Optional[str] = Query('after', description="Insert a flight befor or after an existing flight."
                                    "Order can be 'before', 'after", 
                                    regex="^(before|after)$"),
                sort_key: Optional[str] = Query(None, description="The flight key (YYYY-MM-DD_DEP_ARR) to look for")):
    '''
    Add a flight to an existing session.
    '''
    flight_history = get_cookie(request)
    try:
        key = build_key(date, departure, arrival)
        if key in flight_history["ORDER"]:
            raise HTTPException(
            status_code=409,
            detail=f"{key} already exists"
        )
        flight_history["ORDER"].append(key)
    except HTTPException as e:
        raise e
    response.set_cookie(key=COOKIE_NAME, value=json.dumps(flight_history))
    return {"message": f"Flight added successfully."}


@app.get("/flight", tags=["Flight"])
@session_check
async def get_flight(request: Request = None
                 ):
    '''
    Get a list of all set flights
    '''
    flight_history = get_cookie(request)
    full_history = make_history(flight_history["ORDER"])
    return JSONResponse(
        content=full_history["FLIGHTS"],
        status_code=200
    )


@app.get("/stats", tags=["Airport"])
@session_check
async def get_stats(request: Request = None
                 ):
    '''
    Get the flight stats
    '''
    flight_history = get_cookie(request)
    full_history = make_history(flight_history["ORDER"])
    return JSONResponse(
        content=full_history["STATS"],
        status_code=200
    )

@app.get("/airport", tags=["Airport"], response_model=SuggestionAirportResponse)
async def fetch_airports(query: str):
    '''
    Get a list of matching airports and provide a selection
    '''
    airport_icaos = get_airport_matches(query,  True)

    return SuggestionAirportResponse(icaos=airport_icaos)


