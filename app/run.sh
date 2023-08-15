#!/bin/bash

source blogenv/bin/activate
redis-server redis.conf
cd app
celery -A tasks.tasks:celery_app worker -l DEBUG -Q notification,moderation
