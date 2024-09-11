from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
import requests
from jose import jwt
from config import settings, google_links
from services.google_drive_service import GoogleDriveService
from services.file_metadata_service import FileMetadataService

app = FastAPI()


@app.get("/")
def hello():
    return {'hello': 'lite-gallery'}


@app.get("/login/google")
async def login_google():
    return dict(
        url=f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope={settings.SCOPES[0]}&access_type=offline")


@app.get("/auth/google")
async def auth_google(code: str):
    """
    :param code: код авторизации от пользователя после get("/login/google")
    :return: хэш, для создания объекта класса Credentials
    """
    token_url = google_links.USER_TOKEN_URL
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": google_links.GRANT_TYPE,
    }
    response = requests.post(token_url, data=data)
    # TODO Обработка исключений

    return {
        "token": response.json()['access_token'],
        "refresh_token": response.json().get('refresh_token'),
        "token_uri": google_links.USER_TOKEN_URL,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET
    }


@app.post("/upload/google")
async def upload_to_google_drive(creds_hash: dict, file_path: str, folder_id: str = None):
    """
    Создаем экземпляр GoogleDriveService,
    :param creds_hash: хэш/словарь из get("/auth/google")
    :param file_path: путь к файлу формата 'folder/file.ext'
    :param folder_id: необязательный аргумент, ID директории в Google Drive, куда нужно поместить файл
    :return: ID файла на Google Drive
    """
    drive_service = GoogleDriveService(creds_hash)

    if any(c in "/" for c in file_path):
        file_name = file_path.split('/')[-1]
    else:
        file_name = file_path
    # TODO добавить сервис для обработки директорий / вложенных директорий
    file_metadata = FileMetadataService.get_file_metadata(file_name, folder_id)
    file_mimetype = FileMetadataService.get_mime_type(file_name)

    file_id = drive_service.upload_file(file_path, file_metadata, file_mimetype)

    return {"file_id": file_id}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, settings.GOOGLE_CLIENT_SECRET, algorithms=["HS256"])
