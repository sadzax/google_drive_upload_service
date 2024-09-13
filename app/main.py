from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
import requests
from urllib.parse import urlparse
from jose import jwt
from logging_config import logger
from config import settings, google_links
from services.google_drive_service import GoogleDriveService
from services.file_metadata_service import FileMetadataService
from services.lite_gallery_stream_service import LiteGalleryStreamService


app = FastAPI()


@app.get("/check") # Тестовый эндпоинт для проверки1
def check():
    url = 'https://some_random.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=nonweb'
    res = LiteGalleryStreamService(url)
    return res.data


@app.get("/mock") # Тестовый эндпоинт для проверки2
def mock():
    code = '4/0AQlEd8xyomvQNR_si4EbOIquccGEzpmyh8O6nBDcdt1vQLAP2B_-9-qPbqJHmNU5bDXWiw'
    logger.info(f"Попытка аутентификации пользователя с кодом {code}")
    token_url = google_links.USER_TOKEN_URL
    data = {"code": code, "client_id": settings.GOOGLE_CLIENT_ID, "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI, "grant_type": google_links.GRANT_TYPE, }
    try:
        response = requests.post(token_url, data=data)
        if response.ok:
            logger.info(f"Аутентификация с кодом {code} прошла успешно")
            creds_hash = {"token": response.json()['access_token'], "refresh_token": response.json().get('refresh_token'),
                          "token_uri": google_links.USER_TOKEN_URL, "client_id": settings.GOOGLE_CLIENT_ID,
                          "client_secret": settings.GOOGLE_CLIENT_SECRET}

        else: # response.status_code != 200
            logger.error(f"Ошибка при получении токена, ответ http-клиента: {response}, {response.content}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        return None

    drive_service = GoogleDriveService(creds_hash)
    folder_id = drive_service.initial_folder_id

    target_url = 'https://some_random.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=nonweb'

    data = LiteGalleryStreamService(target_url).data

    for folder_name in data:
        new_folder_id = drive_service.create_folder(folder_name=folder_name, parent_id=folder_id)
        for record in data[folder_name]:
            file_name = record['file_name']
            file_path = record['url']
            file_metadata = FileMetadataService.get_file_metadata(file_name=file_name, folder_id=new_folder_id)
            file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)
            drive_service.upload_file(file_path=file_path, file_metadata=file_metadata, file_mimetype=file_mimetype)


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
    logger.info(f"Попытка аутентификации пользователя с кодом {code}")
    token_url = google_links.USER_TOKEN_URL
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": google_links.GRANT_TYPE,
    }
    try:
        response = requests.post(token_url, data=data)
        # TODO Обработка исключений
        if response.ok:
            logger.info(f"Аутентификация с кодом {code} прошла успешно")
            return {
                "token": response.json()['access_token'],
                "refresh_token": response.json().get('refresh_token'),
                "token_uri": google_links.USER_TOKEN_URL,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET
        }
        else: # response.status_code != 200
            logger.error(f"Ошибка при получении токена, ответ http-клиента: {response}, {response.content}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        return None


@app.post("/upload/google")
async def upload_to_google_drive(creds_hash: dict, target_url: str, folder_id: str = None):
    """
    Создаем экземпляр GoogleDriveService,
    :param creds_hash: хэш/словарь из get("/auth/google")
    :param file_path: путь к файлу формата 'folder/file.ext'
    :param folder_id: необязательный аргумент, ID директории в Google Drive, куда нужно поместить файл
    :return: ID файла на Google Drive
    """
    drive_service = GoogleDriveService(creds_hash=creds_hash)

    if folder_id is None:
        folder_id = drive_service.initial_folder_id

    data = LiteGalleryStreamService(target_url).data

    for folder_name in data:
        new_folder_id = drive_service.create_folder(folder_name=folder_name, parent_id=folder_id)
        for record in data[folder_name]:
            file_name = record['file_name']
            file_path = record['url']
            file_metadata = FileMetadataService.get_file_metadata(file_name=file_name, folder_id=new_folder_id)
            file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)
            drive_service.upload_file(file_path=file_path, file_metadata=file_metadata, file_mimetype=file_mimetype)


@app.post("/upload/google/single")
async def upload_to_google_drive(creds_hash: dict, file_path: str, folder_id: str = None):
    """
    Создаем экземпляр GoogleDriveService,
    :param creds_hash: хэш/словарь из get("/auth/google")
    :param file_path: путь к файлу формата 'folder/file.ext'
    :param folder_id: необязательный аргумент, ID директории в Google Drive, куда нужно поместить файл
    :return: ID файла на Google Drive
    """
    drive_service = GoogleDriveService(creds_hash=creds_hash)
    if any(c in "/" for c in file_path):
        file_name = file_path.split('/')[-1]
    else:
        file_name = file_path
    file_metadata = FileMetadataService.get_file_metadata(file_name=file_name, folder_id=folder_id)
    file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)
    file_id = drive_service.upload_file(file_path=file_path, file_metadata=file_metadata, file_mimetype=file_mimetype)
    return {"file_id": file_id}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@app.get("/token")
async def get_token(token: str = Depends(oauth2_scheme)):
    return jwt.decode(token, settings.GOOGLE_CLIENT_SECRET, algorithms=["HS256"])
