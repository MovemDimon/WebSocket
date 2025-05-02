#!/bin/bash

gunicorn server:app --worker-class eventlet -w 1 -b 0.0.0.0:10000 &

python3 bot.py
