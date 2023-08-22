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

## Startup project:

```bash
git clone git@github.com:Omarmeks89/blogapp_engine.git app_dir
```
Setup create venv:
```bash
cd app_dir
python -m venv venv
source venv/bin/activate
```
Should be installed (in your new venv):
``` bash
celery
```
and `redis` have to be installed on your mashine to
To check that celery installed correct use:
```bash
which celery
>>> your_root_dir/proj_dir/venv/bin/celery
```
if you have same output - all will be ok.

Below is the sample of .env file:
```bash
# app
APP_RUN_PATH=app:app
APP_API_V=0.1.0
RELOADING=True
ENCODING=utf8
SECRET=add_your_secret
CRYPT_ALG=add_your_alg

# db test
TEST_DIALECT=postgresql
TEST_DB_DRIVER=psycopg2
TEST_LOGIN=your_login
TEST_PASSWD=your_passwd
TEST_HOST=0.0.0.0
TEST_POST=5432
TEST_DB_NAME=postgres
TEST_ECHO_POOL=debug
TEST_POOL_PREPING=True
TEST_POOL_SZ=10
TEST_POOL_OWF=6
TEST_POOL_RECL=3600
TEST_AUTOCM=False
TEST_AUTOFL=False
TEST_DB_URL={}+{}://{}:{}@{}:{}/{}

# celery
BROKER_URL=redis://localhost:6379/0
RESULT_BACKEND=redis://localhost:6379/0

# test smtp server
SMTP_PASSWD=your_passwd
SMTP_HOST=smtp.gmail.com  # (or other smpt host you use)
SMTP_PORT=465
SMTP_LOGIN=your_post_login

# cache
CHOST=localhost
CPORT=6379
DEFDBNO=0
RESP_DEC=True

# moderation servise
API_USER=0000000000
API_SECRET=your_secret  # (you can get it for free)
BORDER_COEFF=0.84
```
So, if you`ve configured environment, you can try to warmup:
```bash
cd app_dir && source venv/bin/activate
```
then use commands below step by step (i didn`t setup docker yet, so startup is a little bit complex now...)
```bash
./app/run.sh > celerylog &
```
```bash
python app/app.py > applog.txt &
```
So, now you can discover API on http://127.0.0.1:8000/docs. You can login, create posts and publish them. After moderation you`ll
get email from service. Below you can find simplified moderation-flow schema:

## Moderation Flow:

[![mod-flow.jpg](https://i.postimg.cc/9fqdgzyj/mod-flow.jpg)](https://postimg.cc/QBhKH866)

## Shutdown

Now shutdown process looks like next cmds sequence:
```bash
fg
^C
fg
^C
ps -au
```
### work in progress...
