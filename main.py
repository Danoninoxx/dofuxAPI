from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import supabase, hash_password, verify_password, create_jwt, verify_jwt

app = FastAPI()

security = HTTPBearer()

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
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"message": "User created", "username": response.data}

# User signup
@app.post("/signup")
async def signup(username: str, password: str):
    hashed_password = hash_password(password)  # Hash before storing
    response = supabase.table("users").insert({"username": username, "password": hashed_password}).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"message": "User created successfully"}


# User login
@app.post("/login")
async def login(username: str, password: str):
    response = supabase.table("users").select("*").eq("username", username).execute()

    if response.error or not response.data:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    user = response.data[0]  
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_jwt(username)  # Generate JWT token
    return {"message": "Login successful", "token": token}

# Protected route (JWT authentication required)

@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = verify_jwt(token)  # Validate token
    return {"message": f"Access granted to {username}"}