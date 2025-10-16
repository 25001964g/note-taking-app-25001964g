from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

# This is a temporary in-memory storage
users = {}
current_id = 1

@router.get("/users/")
async def get_users():
    return list(users.values())

@router.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    global current_id
    new_user = User(
        id=current_id,
        username=user.username,
        email=user.email
    )
    users[current_id] = new_user
    current_id += 1
    return new_user

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]