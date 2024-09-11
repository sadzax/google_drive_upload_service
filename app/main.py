from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
import requests
from jose import jwt
from config import settings, google_links
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

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
    token_url = google_links.USER_TOKEN_URL
    data = {
        "code": code, # MOCK
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": google_links.GRANT_TYPE,
    }
    response = requests.post(token_url, data=data)
    # TODO Обработка исключений

    creds = Credentials(
        token=response.json()['access_token'],
        refresh_token=response.json().get('refresh_token'),
        token_uri='https://accounts.google.com/o/oauth2/token',
        client_id='YOUR_CLIENT_ID',
        client_secret='YOUR_CLIENT_SECRET',
    )

    # return creds # TODO метод заканчивать выдачей токена, логику загрузки вынести в сервисы
    # TODO разделить метод на 2 сервиса - request и получение кредов
    # TODO автотесты?

    # TODO Вытащить сервис в класс
    # Здесь используется уже access_token пользователя (а не сервиса)
    drive_service = build('drive', 'v3', credentials=creds) # TODO Вынести в отдельный сервис

    # services.folder_id_create_service # TODO допилить сервис запуска 2 операций: 1. создавалась директория - 2. перехватывать её ID
    folder_id = '1lVeI-2cVeMaYMVeQnhiR6l53xCT8E168' # MOCK

    # services.file_path_create_service # TODO допилить сервис прохода по файлам для загрузки + MIME
    file_metadata = {'name': 'testfile_DRIVE.txt', 'parents': [folder_id]} # MOCK
    file_path = 'testfile.txt' # MOCK
    file_mimetype = 'text/plain' # MOCK

    file_metadata = {'name': 'testfile_DRIVE_JPG.jpg', 'parents': [folder_id]} # MOCK
    file_path = 'testfile.jpg' # MOCK
    file_mimetype = 'image/jpeg' # MOCK

    file_metadata = {'name': 'testfile_DRIVE_HEIC.HEIC', 'parents': [folder_id]} # MOCK
    file_path = 'testfile.HEIC' # MOCK
    file_mimetype = 'image/heic' # MOCK

    file_metadata = {'name': 'testfile_DRIVE_MP4.mp4', 'parents': [folder_id]} # MOCK
    file_path = 'testfile.mp4' # MOCK
    file_mimetype = 'video/mp4' # MOCK

    media = MediaFileUpload(file_path, mimetype=file_mimetype) # TODO допилить сервис обработки медиа

    # TODO обработка interruptions
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return {"file_id": file.get("id")}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, settings.GOOGLE_CLIENT_SECRET, algorithms=["HS256"])
