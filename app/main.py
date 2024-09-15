from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import requests
from urllib.parse import urlparse
from jose import jwt
from logging_config import logger
from config import settings, google_links
from services.google_drive_service import GoogleDriveService
from services.file_metadata_service import FileMetadataService
from services.lite_gallery_stream_service import LiteGalleryStreamService
from models.archive_request import SessionLocalArchiveRequest, ArchiveRequest


app = FastAPI()


@app.post("/cloud_archive")
async def cloud_archive(request: Request):
    """
    Эндпоинт для получения параметров от фронта, перенаправления пользователя на Google OAuth2
    :param request:
        {
            "redirect_success_link": "https://app-site/success", // куда отправить в случае успеха старта
            "redirect_fail_link": "https://app-site/fail", // в случае провала
            "archive_url": "https://app-site/gallery_num", // ссылка на архив, которая может быть получена как "скачать галерею" в интерфейсе
            "gallery_name": "Lorem Ipsum",
            "archive_type": "webs", // or originals
            "cloud_type": "google_drive", // or yadisk.
        }
    :return: 307 редирект на систему авторизации Google
    """
    session = SessionLocalArchiveRequest()
    body = await request.json()
    # body = {
    #     "redirect_success_link": "https://litegallery.io/oferta/",
    #     "redirect_fail_link": "https://litegallery.io/policy/",
    #     "archive_url": "https://arch-d.lite.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=web",
    #     "gallery_name": "Название галереи",
    #     "archive_type": "webs",
    #     "cloud_type": "google_drive"} # MOCK

    # Проверяем корректность типа диска
    cloud_type = body.get("cloud_type")
    if cloud_type != "google_drive": #TODO через ENV
        logger.error(f"Поступил запрос с некорректным параметром cloud_type")
        raise HTTPException(status_code=400, detail="Invalid cloud type")

    redirect_success_link = body.get("redirect_success_link")
    redirect_fail_link = body.get("redirect_fail_link")
    archive_url = body.get("archive_url")
    gallery_name = body.get("gallery_name")
    user_ip = request.client.host
    logger.info(f"Поступил запрос на выгрузку {gallery_name} по ссылке {archive_url} c ip: {user_ip}")

    # Создаем запись в базе данных
    new_request = ArchiveRequest(
        redirect_success_link = redirect_success_link,
        redirect_fail_link = redirect_fail_link,
        archive_url = archive_url,
        gallery_name = gallery_name,
        cloud_type = cloud_type,
        user_ip = user_ip
    )

    # Сохраняем запись в базу
    session.add(new_request)
    session.commit()
    # session.close() # ВОПРОC: надо ли закрыть?
    logger.info(f"Создана запись в базе с uuid {new_request.id}")

    # Перенаправляем пользователя на Google OAuth2 для получения кода
    redirect_link = (
        f"https://accounts.google.com/o/oauth2/auth"
        f"?response_type=code"
        f"&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&scope={settings.SCOPES[0]}"
        f"&access_type=offline"
        f"&state={new_request.id}" # OAuth2 Google не поддерживает передачу доп.параметров, поэтому используется state
    )
    return RedirectResponse(url = redirect_link)


@app.get("/google_auth_callback")
async def google_auth_callback(code: str, state: str):
    """
    Получаем код авторизации и передаем его в auth_google.
    Затем вызываем загрузку файлов и делаем редирект на success или fail ссылку.
    :param code: код авторизации от пользователя формата "4/0AQlEd8x___[FILTERED]___f6I3FbDWeYSbjKgxGh2fqG6Bv5lSjDSzVI-x2hAEh50Bs4Q"
    :param state: Id в формате uuid модели ArchiveRequest, передаётся в стейт из-за особенностей Google OAuth
    :return: 307 редирект, установленный первоначальным запросом с фронта (success либо failed)
    """
    # Получаем креденшалы с помощью кода авторизации
    creds_hash = await auth_google(code=code)

    if creds_hash:
        try:
            # Ищем запрос в базе данных по archive_id
            session = SessionLocalArchiveRequest()
            archive_request = session.query(ArchiveRequest).filter(ArchiveRequest.id == state).first()
            if not archive_request:
                logger.error(f"Запись запроса с ID {state} не найдена")
                raise HTTPException(status_code = 404, detail = "Запись не найдена")

            # Вызываем загрузку файлов на Google Drive
            target_url = archive_request.archive_url

            await upload_to_google_drive(creds_hash = creds_hash, target_url = target_url)

            # Если всё прошло успешно, перенаправляем на success_link
            return RedirectResponse(url = archive_request.redirect_success_link)
        except Exception as e:
            logger.error(f"Ошибка при обработке OAuth Google: {e}")
            #return RedirectResponse(url = archive_request.redirect_fail_link) # TODO добавить в ENV адрес фейл-редиректа
            return # MOCK
    else:
        logger.error(f"Ошибка при получении креденшалов для кода авторизации {code}")
        #return RedirectResponse(url = archive_request.redirect_fail_link)  # TODO добавить в ENV адрес фейл-редиректа
        return # MOCK


@app.get("/auth_google")
async def auth_google(code: str):
    """
    :param code: код авторизации от пользователя формата "4/0AQlEd8x___[FILTERED]___f6I3FbDWeYSbjKgxGh2fqG6Bv5lSjDSzVI-x2hAEh50Bs4Q"
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
            #return RedirectResponse(url = archive_request.redirect_fail_link) # TODO добавить в ENV адрес фейл-редиректа
            return # MOCK
    except Exception as e:
        logger.error(f"Ошибка при получении токена: {e}")
        # return RedirectResponse(url = archive_request.redirect_fail_link) # TODO добавить в ENV адрес фейл-редиректа
        return # MOCK


@app.post("/upload_to_google_drive")
async def upload_to_google_drive(creds_hash: dict, target_url: str, folder_id: str = None):
    """
    Создаем экземпляр GoogleDriveService,
    :param creds_hash: хэш/словарь из get("/auth/google")
    :param target_url: ссылка на альбом 'https://some_random.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=nonweb'
    :param folder_id: необязательный аргумент, ID директории в Google Drive, куда нужно поместить файл
    :return: ID файла на Google Drive
    """
    drive_service = GoogleDriveService(creds_hash=creds_hash)

    if folder_id is None:
        folder_id = drive_service.initial_folder_id

    data = LiteGalleryStreamService(target_url).data
#TODO переписать на фоновое выполнение в очереди RabbitMQ
    for folder_name in data:
        new_folder_id = drive_service.create_folder(folder_name=folder_name, parent_id=folder_id)
        for record in data[folder_name]:
            file_name = record['file_name']
            file_path = record['url']
            file_metadata = FileMetadataService.get_file_metadata(file_name=file_name, folder_id=new_folder_id)
            file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)
            drive_service.upload_file(file_path=file_path, file_metadata=file_metadata, file_mimetype=file_mimetype)


# @app.post("/upload/google/single")
# async def upload_to_google_drive(creds_hash: dict, file_path: str, folder_id: str = None):
#     """
#     (Нет потребности)
#     Создаем экземпляр GoogleDriveService, и загружаем локальный файл
#     :param creds_hash: хэш/словарь из get("/auth/google")
#     :param file_path: путь к файлу формата 'folder/file.ext'
#     :param folder_id: необязательный аргумент, ID директории в Google Drive, куда нужно поместить файл
#     :return: ID файла на Google Drive
#     """
#     drive_service = GoogleDriveService(creds_hash=creds_hash)
#     if any(c in "/" for c in file_path):
#         file_name = file_path.split('/')[-1]
#     else:
#         file_name = file_path
#     file_metadata = FileMetadataService.get_file_metadata(file_name=file_name, folder_id=folder_id)
#     file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)
#     file_id = drive_service.upload_file(file_path=file_path, file_metadata=file_metadata, file_mimetype=file_mimetype)
#     return {"file_id": file_id}
#
#
# @app.get("/check") # Тестовый эндпоинт для проверки
# def check(request: Request):
#     session = SessionLocalArchiveRequest()
#     return len(session.query(ArchiveRequest).all())
