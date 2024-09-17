import time
import pika
import json
from pika.exceptions import AMQPConnectionError
from app.services.google_drive_service import GoogleDriveService
from app.services.lite_gallery_stream_service import LiteGalleryStreamService
from app.services.file_metadata_service import FileMetadataService
from app.logging_config import logger


def fibonacci_retries(max_retries):
    """
    Генератор создания интервалов по последовательности Фибоначчи
    """
    a, b = 1, 1
    for _ in range(max_retries):
        yield a
        a, b = b, a + b


def upload_to_google_drive_task(ch, method, properties, body):
    """
    Основной процесс, запускается брокером очередей, требует получения в теле креденшалов и ссылки, откуда брать файлы
    """
    task = json.loads(body)
    creds_hash = task['creds_hash']
    target_url = task['target_url']

    failed_files = []  # Список неудачных файлов для логирования

    try:
        # Получаем данные с прямыми ссылками на файлы и прочей информацией
        data = LiteGalleryStreamService(target_url).data

        # Открываем соединение с сервисом
        drive_service = GoogleDriveService(
            creds_hash=creds_hash
        )

        # Создаём директорию на диске для загрузки файлов туда
        folder_id = drive_service.initial_folder_id

        # Загружаем файлы
        for folder_name in data:
            # Создание дочерней директории для альбомов
            new_folder_id = drive_service.create_folder(
                folder_name=folder_name,
                parent_id=folder_id
            )

            # Очередь файлов для загрузки
            for record in data[folder_name]:
                file_name = record['file_name']
                file_path = record['url']
                file_metadata = FileMetadataService.get_file_metadata(
                    file_name=file_name,
                    folder_id=new_folder_id
                )
                file_mimetype = FileMetadataService.get_mime_type(file_name=file_name)

                # Пробуем загрузить файл с повторными попытками
                success = upload_file_with_retries(
                    drive_service = drive_service,
                    file_path = file_path,
                    file_metadata = file_metadata,
                    file_mimetype = file_mimetype
                )

                # Обработка кейса неудачной загрузки файла
                if not success:
                    failed_files.append(
                        {
                            "name": file_metadata['name'],
                            "type": file_mimetype,
                            "url": file_path,
                        }
                    )

        if len(failed_files) > 0:
            logger.warning(f"Не удалось загрузить следующие файлы: {[er for er in failed_files]}")

        logger.info("Задача по загрузке файлов в Google Drive завершена")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи загрузке файлов в Google Drive: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)


def upload_file_with_retries(drive_service, file_path, file_metadata, file_mimetype, max_retries=8):
    """
    Загружает файл с повторными попытками по схеме Фибоначчи.
    """
    for wait_time in fibonacci_retries(max_retries):
        try:
            id_file = drive_service.upload_file(
                file_path,
                file_metadata,
                file_mimetype
            )
            logger.info(f"Файл {file_metadata['name']} успешно загружен с id {id_file}")
            return True  # Успешная загрузка выводит из функции
        except Exception as e:
            logger.info(f"Из-за ошибки при загрузке файла повторная попытка будет произведена через {wait_time} сек.")
            time.sleep(wait_time)

    # Если после всех попыток всё же не удалось загрузить файл
    logger.error(f"Файл {file_metadata['name']} не удалось загрузить после {max_retries} попыток.")
    return False


def start_worker():
    """
    Запуск консьюмера
    :return: None
    """
    connection = connect_to_rabbitmq()
    channel = connection.channel()

    # Подписываемся на очередь
    channel.queue_declare(queue='google_drive_upload', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='google_drive_upload', on_message_callback=upload_to_google_drive_task)

    logger.info("Worker успешно запущен")
    print("Worker успешно запущен")
    channel.start_consuming()


def connect_to_rabbitmq(max_retries=5):
    """
    Пробует установить соединение с RabbitMQ c повторными попытками по схеме Фибоначчи
    """
    for wait_time in fibonacci_retries(max_retries):
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))  # Подключение RabbitMQ через сеть Docker
        except AMQPConnectionError as e:
            logger.error(f"Не удалось подключиться к RabbitMQ, будет повторная попытка через {wait_time} сек.")
            time.sleep(wait_time)


if __name__ == "__main__":
    start_worker()
