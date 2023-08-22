## Idea

API for blog or small social network, based on event system and automatic AI moderation flow, using `https://sightengine.com/` 
service and couple `celery` + `redis` for external tasks. You can visit https://sightengine.com/ for more information.

## Stack:

Project built on next technologiies:

![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)

Of course: `asyncio` `sqlalchemy` `httpx` `celery` 

Python version: `3.11.X`

## Moderation Flow:

[![mod-flow.jpg](https://i.postimg.cc/9fqdgzyj/mod-flow.jpg)](https://postimg.cc/QBhKH866)

