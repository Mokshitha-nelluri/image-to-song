#!/bin/bash
uvicorn main_oauth_test:app --host 0.0.0.0 --port $PORT
