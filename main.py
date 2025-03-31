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

class OficioLevelUpdate(BaseModel):
    id_personaje: int
    id_oficio: int
    nivel: int

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

@app.get("/oficios")
async def get_oficios():
    # Makes the query for table "oficios"
    response = supabase.table("oficios").select("*").execute()

    # Verify if there was an error
    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(
            status_code=500, 
            detail=response["error"]["message"]
        )

    # Return the data
    return response.data

@app.get("/oficios/{id}")
async def get_oficio(id: int):
    response = supabase.table("oficios").select("*").eq("id", id).execute()

    if not response.data or "error" in response:
        raise HTTPException(status_code=404, detail="Oficio no encontrado")

    # Devuelve el primer registro (suponiendo id sea único)
    return response.data[0]

@app.get("/personajes/{user_id}")
async def get_personaje(user_id: int):
    # 1) Buscar el personaje
    personaje_resp = supabase.table("personajes").select("*").eq("user_id", user_id).execute()
    if not personaje_resp.data:
        raise HTTPException(status_code=404, detail="No existe personaje para este usuario")
    personaje = personaje_resp.data[0]

    # 2) Buscar en 'oficioslevel' los oficios de ese personaje
    #    y unirlos con la tabla 'oficios'
    #    (ya sea con select("*, oficios(*)") si configuras la relación
    #     o con dos consultas separadas).
    oficios_resp = supabase.table("oficios_level") \
                           .select("nivel, oficios!inner(id, oficio_name)") \
                           .eq("id_personaje", personaje["id"]) \
                           .execute()
    # Nota: 'oficios!inner(...)' es la sintaxis de Supabase
    # para incluir la tabla oficios. Ajusta según tu config.

    if "error" in oficios_resp and oficios_resp["error"]:
        raise HTTPException(status_code=500, detail=oficios_resp["error"]["message"])

    # 3) Construir un array de oficios con nivel
    oficios_list = []
    for row in oficios_resp.data:
        # row tiene { "nivel": X, "oficios": { "id":..., "oficio_name":... } }
        oficio_data = row["oficios"]
        oficios_list.append({
            "oficio_name": oficio_data["oficio_name"],
            "id_oficio": oficio_data["id"],
            "nivel": row["nivel"]
        })

    # 4) Agregar al personaje
    personaje["oficios"] = oficios_list

    return personaje

@app.post("/personajes")
async def create_personaje(personaje_data: PersonajeCreate):
    # Insertar el nuevo personaje en la tabla "personajes"
    data_dict = personaje_data.model_dump()
    response = supabase.table("personajes").insert(data_dict).execute()

    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    new_personaje = response.data[0]

    # Obtener la lista de todos los oficios existentes
    oficios_resp = supabase.table("oficios").select("id").execute()
    if isinstance(oficios_resp, dict) and "error" in oficios_resp and oficios_resp["error"]:
        raise HTTPException(status_code=500, detail=oficios_resp["error"]["message"])

    oficios_list = oficios_resp.data

    # Para cada oficio, insertar un registro en la tabla "oficioslevel" con nivel 1
    inserts = []
    for oficio in oficios_list:
        inserts.append({
            "id_personaje": new_personaje["id"],
            "id_oficio": oficio["id_oficio"],
            "nivel": 1
        })

    if inserts:
        oficioslevel_resp = supabase.table("oficios_level").insert(inserts).execute()
        if isinstance(oficioslevel_resp, dict) and "error" in oficioslevel_resp and oficioslevel_resp["error"]:
            raise HTTPException(status_code=500, detail=oficioslevel_resp["error"]["message"])

    return new_personaje

@app.patch("/oficioslevel")
async def update_oficio_level(data: OficioLevelUpdate = Body(...)):
    # Actualiza la tabla "oficios_level" donde coincidan id_personaje e id_oficio
    response = supabase.table("oficios_level").update({"nivel": data.nivel}) \
        .eq("id_personaje", data.id_personaje) \
        .eq("id_oficio", data.id_oficio).execute()

    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(status_code=500, detail=response["error"]["message"])

    return {"message": "Nivel actualizado", "data": response.data}

@app.get("/mazmorras")
async def get_mazmorras():
    # Makes the query for table "mazmorras"
    response = supabase.table("mazmorras").select("*").execute()

    # Verify if there was an error
    if isinstance(response, dict) and "error" in response and response["error"]:
        raise HTTPException(
            status_code=500, 
            detail=response["error"]["message"]
        )

    # Return the data
    return response.data

@app.get("/mazmorras/{id}")
async def get_mazmorra(id: int):
    response = supabase.table("mazmorras").select("*").eq("id", id).execute()

    if not response.data or "error" in response:
        raise HTTPException(status_code=404, detail="Mazmorra no encontrada")

    # Devuelve el primer registro (suponiendo que id sea único)
    return response.data[0]

# Protected route (JWT authentication required)
@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_jwt(token)  # Validate token
    return {"message": f"Access granted to {username}"}
