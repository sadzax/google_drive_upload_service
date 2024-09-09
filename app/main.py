from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
import requests
from jose import jwt
from config import settings, google_links
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = FastAPI()


SERVICE_ACCOUNT_FILE = settings.SERVICE_ACCOUNT_FILE
SCOPES = settings.SCOPES
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
USER_TOKEN_URL = google_links.USER_TOKEN_URL
GRANT_TYPE = google_links.GRANT_TYPE
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/login/google")
async def login_google():
    return dict(
        url=f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope={settings.SCOPES[0]}&access_type=offline")


@app.get("/auth/google")
async def auth_google(code: str):
    token_url = google_links.USER_TOKEN_URL
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": google_links.GRANT_TYPE,
    }
    response = requests.post(token_url, data=data)
    tokens = response.json()
    access_token = tokens.get("access_token")
    # return access_token # TODO метод заканчивать выдачей токена, логику загрузки вынести в сервисы

    # Здесь используется уже access_token пользователя (а не сервиса)
    drive_service = build('drive', 'v3', credentials=access_token)

    # services.folder_id_create_service # TODO допилить сервис запуска 2 операций: 1. создавалась директория - 2. перехватывать её ID
    folder_id = '1lVeI-2cVeMaYMVeQnhiR6l53xCT8E168' # MOCK

    # services.file_path_create_service # TODO допилить сервис прохода по файлам для загрузки (нужен пример)
    file_metadata = {'name': 'testfile_OLEG.txt', 'parents': [folder_id]} # MOCK
    file_path = 'testfile_OLEG.txt' # MOCK
    file_mimetype = 'text/plain' # MOCK

    media = MediaFileUpload(file_path, mimetype=file_mimetype) # TODO допилить сервис обработки медиа

    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return {"file_id": file.get("id")}


@app.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, settings.GOOGLE_CLIENT_SECRET, algorithms=["HS256"])
