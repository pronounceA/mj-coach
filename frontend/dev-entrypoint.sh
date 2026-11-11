#!/bin/sh
set -e
node /app-host/dev-init.js
node /app-host/dev-watch.js &
exec npm run dev
