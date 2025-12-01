"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}

# adicional: novas atividades (2 esportes, 2 artísticas, 2 intelectuais)
activities.update({
    "basketball": {
        "description": "Partida de basquete 5x5 para estudantes de todos os níveis.",
        "participants": [],
        "max_participants": 10
    },
    "tennis": {
        "description": "Aulas e treinos de tênis — raquetes fornecidas quando necessário.",
        "participants": [],
        "max_participants": 8
    },
    "painting": {
        "description": "Oficina de pintura com aquarela e acrílico, materiais inclusos.",
        "participants": [],
        "max_participants": 12
    },
    "sculpture": {
        "description": "Atelier de escultura em argila para iniciantes e intermediários.",
        "participants": [],
        "max_participants": 10
    },
    "chess_club": {
        "description": "Clube de xadrez: aulas, partidas e pequenos torneios semanais.",
        "participants": [],
        "max_participants": 20
    },
    "robotics_workshop": {
        "description": "Workshop de robótica e lógica para desenvolvimento de projetos práticos.",
        "participants": [],
        "max_participants": 15
    }
})


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/signup")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    # Validate participant exists
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Participant not found for this activity")

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Removed {email} from {activity_name}"}
