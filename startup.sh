#!/bin/bash

# 安全のためロギング
echo "==== Installing requirements ===="
pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt

echo "==== Starting Streamlit App ===="
streamlit run /home/site/wwwroot/app.py --server.port=8000 --server.enableCORS=false
