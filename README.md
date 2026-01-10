# DetectionService

Сервис обнаружения оставленных предметов на видеопотоке с использованием компьютерного зрения.

Проект состоит из нескольких сервисов и полностью запускается через **Docker Compose** одной командой.

---

## Общая архитектура

```
RTSP (эмулятор камеры)
        ↓
     MediaMTX
        ↓
     ML сервис (YOLO + трекинг)
        ↓
     Backend API (FastAPI)
        ↓
     PostgreSQL

Snapshot’ы событий сохраняются в MinIO (S3)
Frontend получает:
- события из Backend API
- HLS-поток напрямую из MediaMTX
- изображения snapshot’ов напрямую из MinIO
```

---

## Требования

* Docker Engine / Docker Desktop
* Docker Compose
* Git

Устанавливать Python, Node.js или другие зависимости **не требуется**.

---

## Быстрый запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/3garfield5/DetectionService.git
cd DetectionService
```

---

### 2. Создать файл `.env`

Скопируйте пример и при необходимости измените значения:

```bash
cp .env.example .env
```

### 3. Запуск всех сервисов

```bash
docker compose up --build
```

Для запуска в фоне:

```bash
docker compose up -d --build
```

---

## Доступные сервисы

После успешного запуска:

| Сервис                | Адрес                                                                                        |
| --------------------- | -------------------------------------------------------------------------------------------- |
| Frontend              | [http://localhost:5173](http://localhost:5173)                                               |
| Backend API (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs)                                     |
| MinIO (Web UI)        | [http://localhost:9001](http://localhost:9001)                                               |
| HLS-поток             | [http://localhost:8888/live_stream/index.m3u8](http://localhost:8888/live_stream/index.m3u8) |

---

## Проверка сохранения snapshot’ов

Проверить содержимое бакета MinIO:

```bash
docker compose exec minio-init mc ls local/snapshots | head
```

Открыть любой snapshot в браузере:

```
http://localhost:9000/snapshots/<имя_файла>.jpg
```

---

## Остановка сервисов

```bash
docker compose down
```

Полный сброс данных (PostgreSQL и MinIO):

```bash
docker compose down -v
```

---

## Примечания

* Snapshot’ы хранятся в **MinIO**
* В базе данных сохраняется **только ключ объекта**, а не путь к файлу
* Вся конфигурация осуществляется через `.env`
* Проект предназначен для локальной разработки и демонстрации
* Если у вас появляется ошибка 
```
Attaching to backend-1, emulator-1, frontend-1, minio-1, minio-init-1, ml-1, postgres-1, mediamtx
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:1936 -> 0.0.0.0:0: listen tcp 0.0.0.0:1936: bind: An attempt was made to access a socket in a way forbidden by its access permissions.
```
То нужно открыть командную строку от имени администратора и ввести следующие команды:
```
net stop winnat
net start winnat
```
Затем запустить контейнер
