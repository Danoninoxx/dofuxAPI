from fastapi import FastAPI, HTTPException
from database import supabase  # Import Supabase client

app = FastAPI()

@app.get("/")
def readRoot():
    return {"message": "FastAPI + Supabase"}

# Fetch data from a Supabase table
@app.get("/users")
async def getUsers():
    response = supabase.table("users").select("username").execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return response.data

# Insert data into a Supabase table
@app.post("/users")
async def createUser(name: str, password: str):
    response = supabase.table("users").insert({"username": name, "password": password}).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"message": "User created", "user": response.data}
