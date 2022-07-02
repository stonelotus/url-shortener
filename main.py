from http.client import HTTPException
import validators
from sqlalchemy.orm import Session
from . import schemas, models
from .database import SessionLocal, engine
import secrets
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse


app = FastAPI()      # defined fastApi
models.Base.metadata.create_all(bind=engine) # bind db engine -> if db in engine doesn't exist,
                                             # will be created with all modeled tabled at first time run
def get_db():
    db = SessionLocal() # generate local db session 
    try:
        yield db        # return db session as Generator (one-time use object)
    except:
        print("Exception dude")
        pass
    finally:
        db.close()


def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


### ENDPOINT
@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"

@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    db_url = (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )
    if db_url:
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)

@app.post("/url", response_model=schemas.URLInfo)
def create_url(url:schemas.URLBase, db: Session = Depends(get_db)):     #establish a database session for the request and close the session when the request is finished 
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    key = "".join(secrets.choice(chars) for _ in range(5))
    secret_key = "".join(secrets.choice(chars) for _ in range(8))

    db_url = models.URL(
        target_url=url.target_url, key=key, secret_key=secret_key
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    db_url.url = key
    db_url.admin_url = secret_key

    return db_url


