#!/bin/sh
set -e

if [ -f /etc/onetwoboard/cron-env.sh ]; then
    set -a
    # shellcheck source=/dev/null
    . /etc/onetwoboard/cron-env.sh
    set +a
fi

cd /app || exit 1
exec python manage.py expire_listings
