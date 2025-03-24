from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from database import supabase, hash_password, verify_password, create_jwt, verify_jwt
from typing import Optional

app = FastAPI()

# Define allowed origins
origins = [
    "http://localhost:4200",
    "https://dofuxapi.onrender.com",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specifies which origins are allowed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class ClaseCreate(BaseModel):
    title: str
    class_logo: Optional[str] = None
    image: Optional[str] = None
    short_desc: Optional[str] = None
    description: Optional[str] = None

class ClaseUpdate(BaseModel):
    title: Optional[str] = None
    class_logo: Optional[str] = None
    image: Optional[str] = None
    short_desc: Optional[str] = None
    description: Optional[str] = None

class Clase(BaseModel):
    id: int
    title: str

class PersonajeBase(BaseModel):
    name: str
    level: int
    clase: str # Title de la tabla clase

class PersonajeCreate(PersonajeBase):
    user_id: int

class Personaje(PersonajeBase):
    id: int
    user_id: int

@app.get("/")
def read_root():
    return {"message": "FastAPI + Supabase"}

# Fetch all users from Supabase
@app.get("/users")
async def get_users():
    response = supabase.table("users").select("*").execute()

    # Ensure response follows correct structure
    if isinstance(response, dict) and "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])

    return response.data  # This correctly returns the user data


# Insert a new user into Supabase
@app.post("/users")
async def create_user(name: str, password: str):
    response = supabase.table("users").insert({"username": name, "password": password}).execute()

    # Fix: Check if response contains an error
    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    return {"message": "User created", "username": response.data}

# User signup
@app.post("/signup")
async def signup(username: str = Body(...), password: str = Body(...)):
    hashed_password = hash_password(password)  # Hash before storing
    response = supabase.table("users").insert({"username": username, "password": hashed_password, "admin": False}).execute()

    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    token = create_jwt(username)
    return {"message": "User created successfully", "token": token}

@app.post("/login")
async def login(login_data: LoginRequest):
    username = login_data.username
    password = login_data.password

    # Fetch user from Supabase
    response = supabase.table("users").select("*").eq("username", username).execute()

    # Check if user exists or there was an error
    if not response.data or "error" in response:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    user = response.data[0]  # Assuming the user is found

    # Verify the password against the hashed password
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Generate JWT token
    token = create_jwt(username)
    return {"message": "Login successful", "token": token, "admin": user["admin"], "id": user["id"]}

@app.get("/clases")
async def get_clases():
    # Makes the query for table "clases"
    response = supabase.table("clases").select("*").execute()

    # Verify if there was an error
    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(
            status_code=500, 
            detail=response["error"]["message"]
        )

    # Return the data
    return response.data

@app.get("/clases/{id}")
async def get_clase(id: int):
    response = supabase.table("clases").select("*").eq("id", id).execute()

    if not response.data or "error" in response:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    # Devuelve el primer registro (suponiendo que id sea único)
    return response.data[0]

@app.post("/clases")
async def create_clase(clase_data: ClaseCreate):
    # Convertir los datos a dict
    data_dict = clase_data.model_dump(exclude_unset=True)

    response = supabase.table("clases").insert(data_dict).execute()

    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    return {"message": "Clase creada con éxito", "data": response.data}

@app.put("/clases/{id}")
async def update_clase(id: int, clase_data: ClaseUpdate):
    data_dict = clase_data.model_dump(exclude_unset=True)
    
    # Si data_dict está vacío, significa que no hay campos para actualizar
    if not data_dict:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    # Verifica que la clase exista (opcional)
    existing = supabase.table("clases").select("*").eq("id", id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    response = supabase.table("clases").update(data_dict).eq("id", id).execute()
    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    return {"message": "Clase actualizada con éxito", "data": response.data}

@app.delete("/clases/{id}")
async def delete_clase(id: int):
    # Verifica si existe
    existing = supabase.table("clases").select("*").eq("id", id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    response = supabase.table("clases").delete().eq("id", id).execute()
    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    return {"message": "Clase eliminada con éxito"}

@app.get("/personajes/{user_id}")
async def get_personaje(user_id: int):
    # Busca en la tabla "personajes" donde user_id == user_id
    response = supabase.table("personajes").select("*").eq("user_id", user_id).execute()

    # Si no hay registros, 404
    if not response.data:
        raise HTTPException(status_code=404, detail="No existe personaje para este usuario")

    return response.data[0]  # Devuelve el primer (y único) personaje

@app.post("/personajes")
async def create_personaje(personaje_data: PersonajeCreate):
    # Convierte el modelo Pydantic a diccionario
    data_dict = personaje_data.model_dump()
    
    # Inserta en la tabla "personajes"
    response = supabase.table("personajes").insert(data_dict).execute()

    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    # Retornamos el registro creado
    return response.data[0]


# Protected route (JWT authentication required)
@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_jwt(token)  # Validate token
    return {"message": f"Access granted to {username}"}
