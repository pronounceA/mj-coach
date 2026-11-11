#!/bin/sh
set -e
node /app/dev-watch.js &
exec npm run dev
