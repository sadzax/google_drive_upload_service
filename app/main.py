from fastapi import FastAPI
from app.api import cloud_upload

app = FastAPI()

app.include_router(cloud_upload.router)


@app.get("/")
async def root():
    return {"message": "Cloud Upload Service"}
