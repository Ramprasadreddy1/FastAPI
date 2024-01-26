import sys

import models

sys.path.append("..")

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, APIRouter, Request, Form
from models import Todos, Users
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .auth import get_current_user, get_password_hash, verify_password
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from starlette import status

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={401: {"user": "Not authorized"}}
)
templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/edit-password", response_class=HTMLResponse)
async def edit_user_view(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("edit-user-password.html", {'request': request, "user": user})


@router.post("/edit_password", response_class=HTMLResponse)
async def user_password_change(request: Request, db: db_dependency,
                               username: str = Form(...), password: str = Form(...), password2: str = Form(...)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    user_data = db.query(Users).filter(Users.username == username).first()

    msg = "Invalid username or password"

    if user_data is not None:
        if user_data.username == username and verify_password(password, user_data.hashed_password):
            user_data.hashed_password = get_password_hash(password2)
            db.add(user_data)
            db.commit()
            msg = 'Password updated'

    return templates.TemplateResponse("edit-user-password.html", {'request': request, "user": user, "msg": msg})

