#!/bin/bash

source blogenv/bin/activate
redis-server redis.conf
cd app
celery -A tasks.tasks:celery_app worker -Q notification --loglevel=DEBUG
deactivate
