#!/data/data/com.termux/files/usr/bin/bash

cd ~/open-aoe2-jp/ || exit 1

pkill -f "uvicorn main:app"
sleep 3
nohup uvicorn main:app \
    --host 0.0.0.0 \
    --port 8443 \
    --ssl-keyfile ~/open-aoe2-jp/certs/open-aoe2-jp.key \
    --ssl-certfile ~/open-aoe2-jp/certs/open-aoe2-jp.fullchain.pem \
    --reload > ~/uvicorn.log 2>&1 &
