from fastapi import APIRouter, HTTPException
from app.models.request_models import CloudArchiveRequest, CloudArchiveDoneRequest
from app.services.google_drive import start_google_auth

router = APIRouter()


@router.post("/cloud_upload")
async def cloud_upload(request: CloudArchiveRequest):
    if request.cloud_type != "google_drive":
        raise HTTPException(status_code=400, detail="Unsupported cloud type")

    auth_url = start_google_auth(request)
    return {"redirect_to": auth_url}


@router.post("/cloud_upload/done")
async def cloud_upload_done(request: CloudArchiveDoneRequest):
    # Код, подтверждающий, что выгрузка выполнена
    return {"status": "success"}
