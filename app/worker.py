import pika
import json
from app.services.google_drive_service import GoogleDriveService
from app.services.lite_gallery_stream_service import LiteGalleryStreamService
from app.services.file_metadata_service import FileMetadataService
from app.logging_config import logger


def upload_to_google_drive_task(ch, method, properties, body):
    task = json.loads(body)
    creds_hash = task['creds_hash']
    target_url = task['target_url']

    try:
        # Открываем соединение с сервисом
        drive_service = GoogleDriveService(creds_hash=creds_hash)

        # Создаём директорию на диске для загрузки файлов туда
        folder_id = drive_service.initial_folder_id

        # Получаем данные с прямыми ссылками на файлы и прочей информацией
        data = LiteGalleryStreamService(target_url).data

        # Загружаем файлы
        for folder_name in data:
            new_folder_id = drive_service.create_folder(folder_name=folder_name, parent_id=folder_id)
            for record in data[folder_name]:
                file_name = record['file_name']
                file_path = record['url']
                file_metadata = FileMetadataService.get_file_metadata(file_name=file_name, folder_id=new_folder_id)
                file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)
                drive_service.upload_file(file_path=file_path, file_metadata=file_metadata, file_mimetype=file_mimetype)

        logger.info("Файлы успешно загружены в Google Drive")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Ошибка при загрузке файлов в Google Drive: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)


def start_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))  # Подключение RabbitMQ через сеть Docker
    channel = connection.channel()

    # Подписываемся на очередь
    channel.queue_declare(queue='google_drive_upload', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='google_drive_upload', on_message_callback=upload_to_google_drive_task)

    logger.info("Worker успешно запущен")
    print("Worker успешно запущен")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()
