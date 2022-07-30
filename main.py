from http.client import HTTPException
import validators
from sqlalchemy.orm import Session

import crud
import schemas, models
from database import SessionLocal, engine
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from starlette.datastructures import URL


app = FastAPI()      # defined fastApi
origins = [ 
    "http://domainname.com",
    "https://domainname.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
models.Base.metadata.create_all(bind=engine) # bind db engine -> if db in engine doesn't exist,
                                             # will be created with all modeled tabled at first time run
def get_db():
    db = SessionLocal() # generate local db session 
    try:
        print(str(db))
        return db        # return db session as Generator (one-time use object)
    except Exception as e:
        print("Exception dude")
        print(str(e))
        pass
    finally:
        db.close()

def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    # base_url = URL(get_settings().base_url)
    base_url = URL("http://159.89.214.197:8000")
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))

    print(db_url)
    return db_url

def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


### ENDPOINTs
@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"


@app.get("/{url_key}")
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
  
    if db_url:= crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db = db, db_url = db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.post("/url", response_model=schemas.URLInfo)
def create_url(url:schemas.URLBase, db: Session = Depends(get_db)):     #establish a database session for the request and close the session when the request is finished 
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url)
    return get_admin_info(db_url)



@app.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
)
def get_url_info(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key=secret_key):
        return get_admin_info(db_url)

    else:
        raise_not_found(request)
    
     
@app.delete("/admin/{secret_key}")
def delete_url(
    secret_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)