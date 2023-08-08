#!/bin/bash

source blogenv/bin/activate
cd app
celery -A tasks.tasks:celery_app worker -Q notification --loglevel=DEBUG
deactivate
