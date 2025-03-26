from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.auth.transport import requests
from google.cloud import firestore
import google.oauth2.id_token

app = FastAPI()

# Initialize Firestore DB
db = firestore.Client()

firebase_request_adapter = requests.Request()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory="templates")

# Index Route
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
            return RedirectResponse(url="/dashboard")  
        except ValueError:
            pass  # Invalid token

    return templates.TemplateResponse("index.html", {"request": request, "user_token": user_token})

# Login Page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Signup Page
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# Middleware function to check authentication
async def get_current_user(request: Request):
    id_token = request.cookies.get("token")
    if not id_token:
        return None  # No token, user not logged in

    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
        return user_token
    except ValueError:
        return None  # Invalid token


# Dashboard Route (Only logged-in users)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("dashboard.html", {"request": request, "user_email": user_token['email']})


# Add Driver Page Route (Only logged-in users)
@app.get("/add-driver", response_class=HTMLResponse)
async def add_driver_page(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("add_driver.html", {"request": request})


# API to Add Driver to Firestore (Only logged-in users)
# API to Add Driver to Firestore (Only logged-in users)
@app.post("/add-driver")
async def add_driver(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    total_pole_positions: int = Form(...),
    total_race_wins: int = Form(...),
    total_points_scored: float = Form(...),
    total_world_titles: int = Form(...),
    total_fastest_laps: int = Form(...),
    team: str = Form(...),
    user_token: dict = Depends(get_current_user)  # Check user authentication
):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        # Check if a driver with the same name already exists
        existing_drivers = db.collection("drivers").where("name", "==", name).stream()
        if any(existing_drivers):  # If any driver with the same name exists
            return JSONResponse(content={"error": "A driver with this name already exists!"}, status_code=400)

        # If no existing driver is found, proceed to add a new one
        driver_data = {
            "name": name,
            "age": age,
            "total_pole_positions": total_pole_positions,
            "total_race_wins": total_race_wins,
            "total_points_scored": total_points_scored,
            "total_world_titles": total_world_titles,
            "total_fastest_laps": total_fastest_laps,
            "team": team
        }

        db.collection("drivers").add(driver_data)
        return JSONResponse(content={"message": "Driver added successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Add Team Page Route (Only logged-in users)
@app.get("/add-team", response_class=HTMLResponse)
async def add_team_page(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("add_team.html", {"request": request})

# API to Add Team to Firestore (Only logged-in users)
@app.post("/add-team")
async def add_team(
    request: Request,
    name: str = Form(...),
    year_founded: int = Form(...),
    total_pole_positions: int = Form(...),
    total_race_wins: int = Form(...),
    total_constructor_titles: int = Form(...),
    finishing_position_last_season: int = Form(...),
    user_token: dict = Depends(get_current_user)  # Check user authentication
):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        # Check if a team with the same name already exists
        existing_teams = db.collection("teams").where("name", "==", name).stream()
        if any(existing_teams):  # If any team with the same name exists
            return JSONResponse(content={"error": "A team with this name already exists!"}, status_code=400)

        # If no existing team is found, proceed to add a new one
        team_data = {
            "name": name,
            "year_founded": year_founded,
            "total_pole_positions": total_pole_positions,
            "total_race_wins": total_race_wins,
            "total_constructor_titles": total_constructor_titles,
            "finishing_position_last_season": finishing_position_last_season
        }

        db.collection("teams").add(team_data)
        return JSONResponse(content={"message": "Team added successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Query Drivers Page Route (Accessible to Everyone)
@app.get("/query-drivers", response_class=HTMLResponse)
async def query_drivers_page(request: Request):
    return templates.TemplateResponse("query_drivers.html", {"request": request})

# API to Query Drivers from Firestore (Accessible to Everyone)
@app.post("/query-drivers")
async def query_drivers(
    request: Request,
    attribute: str = Form(...),
    comparison: str = Form(...),
    value: float = Form(...)
):
    try:
        # Convert comparison operator to Firestore query filter
        query_ref = db.collection("drivers")

        if comparison == "=":
            query_ref = query_ref.where(attribute, "==", value)
        elif comparison == "<":
            query_ref = query_ref.where(attribute, "<", value)
        elif comparison == ">":
            query_ref = query_ref.where(attribute, ">", value)
        else:
            return JSONResponse(content={"error": "Invalid comparison operator."}, status_code=400)

        results = query_ref.stream()
        drivers = [{"id": doc.id, **doc.to_dict()} for doc in results]

        if not drivers:
            return JSONResponse(content={"message": "No matching drivers found!"}, status_code=404)

        return JSONResponse(content={"drivers": drivers}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Route to View Driver Details (Accessible to Everyone)
@app.get("/driver/{driver_id}", response_class=HTMLResponse)
async def driver_details_page(request: Request, driver_id: str):
    try:
        driver_ref = db.collection("drivers").document(driver_id)
        driver_doc = driver_ref.get()

        if not driver_doc.exists:
            return JSONResponse(content={"error": "Driver not found"}, status_code=404)

        driver_data = driver_doc.to_dict()
        return templates.TemplateResponse("driver_details.html", {"request": request, "driver": driver_data})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Query Teams Page Route (Accessible to Everyone)
@app.get("/query-teams", response_class=HTMLResponse)
async def query_teams_page(request: Request):
    return templates.TemplateResponse("query_teams.html", {"request": request})

# API to Query Teams from Firestore (Accessible to Everyone)
@app.post("/query-teams")
async def query_teams(
    request: Request,
    attribute: str = Form(...),
    comparison: str = Form(...),
    value: float = Form(...)
):
    try:
        # Convert comparison operator to Firestore query filter
        query_ref = db.collection("teams")

        if comparison == "=":
            query_ref = query_ref.where(attribute, "==", value)
        elif comparison == "<":
            query_ref = query_ref.where(attribute, "<", value)
        elif comparison == ">":
            query_ref = query_ref.where(attribute, ">", value)
        else:
            return JSONResponse(content={"error": "Invalid comparison operator."}, status_code=400)

        results = query_ref.stream()
        teams = [{"id": doc.id, **doc.to_dict()} for doc in results]

        if not teams:
            return JSONResponse(content={"message": "No matching teams found!"}, status_code=404)

        return JSONResponse(content={"teams": teams}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Route to View Team Details (Accessible to Everyone)
@app.get("/team/{team_id}", response_class=HTMLResponse)
async def team_details_page(request: Request, team_id: str):
    try:
        team_ref = db.collection("teams").document(team_id)
        team_doc = team_ref.get()

        if not team_doc.exists:
            return JSONResponse(content={"error": "Team not found"}, status_code=404)

        team_data = team_doc.to_dict()
        return templates.TemplateResponse("team_details.html", {"request": request, "team": team_data})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Route to View List of Drivers (Only for Logged-in Users)
@app.get("/drivers", response_class=HTMLResponse)
async def drivers_list_page(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("drivers_list.html", {"request": request})

# API to Fetch List of Drivers from Firestore (Only for Logged-in Users)
@app.get("/api/drivers")
async def get_drivers(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        drivers_ref = db.collection("drivers").stream()
        drivers = [{"id": doc.id, **doc.to_dict()} for doc in drivers_ref]

        if not drivers:
            return JSONResponse(content={"message": "No drivers found!"}, status_code=404)

        return JSONResponse(content={"drivers": drivers}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# API to Get Driver Details by ID
@app.get("/api/driver/{driver_id}")
async def get_driver(driver_id: str):
    try:
        driver_ref = db.collection("drivers").document(driver_id).get()
        if not driver_ref.exists:
            return JSONResponse(content={"error": "Driver not found"}, status_code=404)
        return JSONResponse(content={"driver": driver_ref.to_dict()}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Route to Display Edit Driver Page
@app.get("/edit-driver", response_class=HTMLResponse)
async def edit_driver_page(request: Request, driver_id: str = Query(..., alias="id")):
    return templates.TemplateResponse("edit_driver.html", {"request": request, "driver_id": driver_id})

# API to Update a Driver's Information
@app.post("/api/update-driver/{driver_id}")
async def update_driver(
    request: Request,
    driver_id: str,
    name: str = Form(None),
    age: int = Form(None),
    total_pole_positions: int = Form(None),
    total_race_wins: int = Form(None),
    total_points_scored: float = Form(None),
    total_world_titles: int = Form(None),
    total_fastest_laps: int = Form(None),
    team: str = Form(None),
    user_token: dict = Depends(get_current_user)
):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        driver_ref = db.collection("drivers").document(driver_id)
        driver_doc = driver_ref.get()

        if not driver_doc.exists:
            return JSONResponse(content={"error": "Driver not found!"}, status_code=404)

        driver_data = {}

        # Check for duplicate name (excluding the current driver)
        if name:
            existing_drivers = db.collection("drivers").where("name", "==", name).stream()
            for existing_driver in existing_drivers:
                if existing_driver.id != driver_id:  # Ensure it's not the current driver
                    return JSONResponse(content={"error": "A driver with this name already exists!"}, status_code=400)
            driver_data["name"] = name

        # Ensure each attribute is updated only if provided
        if age is not None: driver_data["age"] = age
        if total_pole_positions is not None: driver_data["total_pole_positions"] = total_pole_positions
        if total_race_wins is not None: driver_data["total_race_wins"] = total_race_wins
        if total_points_scored is not None: driver_data["total_points_scored"] = total_points_scored
        if total_world_titles is not None: driver_data["total_world_titles"] = total_world_titles
        if total_fastest_laps is not None: driver_data["total_fastest_laps"] = total_fastest_laps
        if team is not None: driver_data["team"] = team

        if not driver_data:
            return JSONResponse(content={"message": "No changes made."}, status_code=400)

        driver_ref.update(driver_data)
        return JSONResponse(content={"message": f"Driver {name if name else driver_id} has been updated successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# API to Delete a Driver
@app.post("/api/delete-driver/{driver_id}")
async def delete_driver(request: Request, driver_id: str, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        db.collection("drivers").document(driver_id).delete()
        return JSONResponse(content={"message": "Driver has been deleted successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Route to View List of Teams (Only for Logged-in Users)
@app.get("/teams", response_class=HTMLResponse)
async def teams_list_page(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("teams_list.html", {"request": request})

# API to Fetch List of Teams from Firestore (Only for Logged-in Users)
@app.get("/api/teams")
async def get_teams(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        teams_ref = db.collection("teams").stream()
        teams = [{"id": doc.id, **doc.to_dict()} for doc in teams_ref]

        if not teams:
            return JSONResponse(content={"message": "No teams found!"}, status_code=404)

        return JSONResponse(content={"teams": teams}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# API to Get Team Details by ID
@app.get("/api/team/{team_id}")
async def get_team(team_id: str):
    try:
        team_ref = db.collection("teams").document(team_id).get()
        if not team_ref.exists:
            return JSONResponse(content={"error": "Team not found"}, status_code=404)
        return JSONResponse(content={"team": team_ref.to_dict()}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Route to Display Edit Team Page
@app.get("/edit-team", response_class=HTMLResponse)
async def edit_team_page(request: Request, team_id: str = Query(..., alias="id")):
    return templates.TemplateResponse("edit_team.html", {"request": request, "team_id": team_id})

# API to Update a Team's Information
@app.post("/api/update-team/{team_id}")
async def update_team(
    request: Request,
    team_id: str,
    name: str = Form(None),
    year_founded: int = Form(None),
    total_pole_positions: int = Form(None),
    total_race_wins: int = Form(None),
    total_constructor_titles: int = Form(None),
    finishing_position_last_season: int = Form(None),
    user_token: dict = Depends(get_current_user)
):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        team_ref = db.collection("teams").document(team_id)
        team_doc = team_ref.get()

        if not team_doc.exists:
            return JSONResponse(content={"error": "Team not found!"}, status_code=404)

        team_data = {}

        # Check for duplicate name (excluding the current team)
        if name:
            existing_teams = db.collection("teams").where("name", "==", name).stream()
            for existing_team in existing_teams:
                if existing_team.id != team_id:  # Ensure it's not the current team
                    return JSONResponse(content={"error": "A team with this name already exists!"}, status_code=400)
            team_data["name"] = name

        # Ensure each attribute is updated only if provided
        if year_founded is not None: team_data["year_founded"] = year_founded
        if total_pole_positions is not None: team_data["total_pole_positions"] = total_pole_positions
        if total_race_wins is not None: team_data["total_race_wins"] = total_race_wins
        if total_constructor_titles is not None: team_data["total_constructor_titles"] = total_constructor_titles
        if finishing_position_last_season is not None: team_data["finishing_position_last_season"] = finishing_position_last_season

        if not team_data:
            return JSONResponse(content={"message": "No changes made."}, status_code=400)

        team_ref.update(team_data)
        return JSONResponse(content={"message": f"Team {name if name else team_id} has been updated successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# API to Delete a Team
@app.post("/api/delete-team/{team_id}")
async def delete_team(request: Request, team_id: str, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        db.collection("teams").document(team_id).delete()
        return JSONResponse(content={"message": "Team has been deleted successfully!"}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Route to Display the Compare Drivers Page
@app.get("/compare-drivers", response_class=HTMLResponse)
async def compare_drivers_page(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("compare_drivers.html", {"request": request})

# API to Fetch and Compare Two Drivers' Data
@app.get("/api/compare-drivers")
async def compare_drivers(driver1_id: str = Query(...), driver2_id: str = Query(...), user_token: dict = Depends(get_current_user)):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        driver1_ref = db.collection("drivers").document(driver1_id).get()
        driver2_ref = db.collection("drivers").document(driver2_id).get()

        if not driver1_ref.exists or not driver2_ref.exists:
            return JSONResponse(content={"error": "One or both drivers not found"}, status_code=404)

        driver1 = driver1_ref.to_dict()
        driver2 = driver2_ref.to_dict()

        return JSONResponse(content={"driver1": driver1, "driver2": driver2}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
# Route to Display Compare Teams Page (Only for Logged-in Users)
@app.get("/compare-teams", response_class=HTMLResponse)
async def compare_teams_page(request: Request, user_token: dict = Depends(get_current_user)):
    if not user_token:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("compare_teams.html", {"request": request})

# API to Fetch Team Details for Comparison
@app.post("/api/compare-teams")
async def compare_teams(
    team1: str = Form(...),
    team2: str = Form(...),
    user_token: dict = Depends(get_current_user)
):
    if not user_token:
        return JSONResponse(content={"error": "Unauthorized access! Please log in."}, status_code=401)

    try:
        team1_doc = db.collection("teams").document(team1).get()
        team2_doc = db.collection("teams").document(team2).get()

        if not team1_doc.exists or not team2_doc.exists:
            return JSONResponse(content={"error": "One or both teams not found"}, status_code=404)

        team1_data = team1_doc.to_dict()
        team2_data = team2_doc.to_dict()

        return JSONResponse(content={"team1": team1_data, "team2": team2_data}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
