# Задача загрузки галереи в гугл диск

Необходимо реализовать функционал, при котором пользователь галереи сможет легко загрузить контент съемки напрямую Google Drive.

# ТЗ

Любой микросервис, которые делаем должен быть:
- контенеризован
- конфигурируем через переменные окружения.
- написан yml файлы для kubernetes для запуска
	- можно сначала docker-compose, на этапе старта, для удобства, но потом обязательно надо для куба сделать
- используем fastapi

Для реализации этого сервиса необходимо:
- создать свое приложение для гугла
- все протестировать на отдельном домене, возможно своем, либо через ngrok?

### Как устроен процесс скачки на клауд
#### 1. Этап запроса контента

Пользователь в галерее нажимает кнопку, на бек уходит запрос на загрузку архива в гугл диск.

Фронт задает куда отправить пользователя после успешной или не успешной авторизации, то есть начала процесса скачки.

Возвращается с бека ссылка - куда перекинуть пользователя.
##### Задача: реализовать получение запроса и авторизацию в гугле

В разделе [API для галереи](# API для гелери) описано api, которое нужно реализовать для старта авторизации загрузки. Позже этот endpoint будет вмонтирован в доступность по app.litegallery.io/cloud_archive - как-то так, решим.


#### 4. Этап авторизации в гугле

В гугле проходит авторизация клиента, разрешение распоряжаться гугл диском. Дальше возврат к нам на сервис с токеном авторизация, запуск самой скачки. 

В очередь отправляем json с со всей необходимой информацией для запуска скачки.

Брокер используем - rabbitmq. Можно тестовый поставить через докер и использовать.

Пользователь отправляется на success или fail url

#### 5. Этап скачки галереи и загрузки в гугл. 

Отдельный микросервис берет из очереди задачи и грузит съемку нужную по токену в нужный гугл драйв.

##### Как найти файлы галереи из archive_url

1. они доступны по основному домену сервиса, нужно просто заменить host
	-  например, ссылка https://arch-d.lite.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=web
	- для получения списка файлов тогда преобразуем до вида - https://app.litegallery.io/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?json=true
		- Тут у нас json=true и правильный host.
2. Берем JSON. Каждый файл описан структурой типа
```json
{
  "crc": "e7b057b2",
  "filesize": 268756,
  "created_at": "2024-08-17 12:54:32 +0300",
  "name": "Photos 1/Test_011.jpg",
  "url": "https://up-d.lite.gallery/litepr-m/uploads/image/image/49851973/Test_011.jpg",
  "id": 49851973
}
```
3. Разбираем файлы по папкам из имени, создаем папку галереи из параметра gallery_name, создаем подпапки/альбомы(если они есть), загружаем фотки
4. Важно, удостовериться, что фотка была загружена, пробовать 5 раз, с нарастающим интервалом задержки.
5. После загрузки всех файлов в храналище, дернуть url об успешной скачке галереи, ниже описан апи



Тестовая галерея

https://testerlite.lite.gallery/test_16

URL для скачки (его можно получить через запрос ссылки на архив) - https://arch-d.lite.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=web

# API для галереи

Здесь описано апи, которое будет использоваться фронтом для выгрузки архива в гугл.

endpoint:
https://app.litegallery.io - прод
https://t.litegallery.io - stage

### POST /cloud_archive

#### REQUEST

```json

{
	"redirect_success_link": "https://asdfasdfsdaf/asdfadf/", //куда отправить в случае успеха старта
	"redirect_fail_link": "https://asdfsdfdf.rur/asdfsdf/s", // в случае провала
	"archive_url": "https://arch.litegallery.io/asdfdafdf/", // ссылка на архив, которая может быть получена как "скачать галерею" в интерфейсе
	"gallery_name": "Название галереи",
	"archive_type": "webs", // or originals
	"cloud_type": "google_drive", // куда качаем, можно yadisk.
}
```

#### RESPONSE
```json
{
	"redirect_to": "https:/asdfasdfasdf"
}
```



Endpoint - app.litegallery.io or t.litegallery.io
#### POST /cloud_archive/done

```json
{
	"cloud_type":  "google_drive", // or yadisk
	"failed_photos": 0, // кол-во фоток, которые неудалось загрузить
	"archive_type": "originals" // or webs
}
```
