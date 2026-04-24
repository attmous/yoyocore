#!/usr/bin/env bash
# deploy/scripts/prod_ota_guard.sh
#
# ExecCondition-style guard for the future prod OTA service. It exits 0 only
# when the prod lane owns the app runtime and the dev lane is inactive.

set -euo pipefail

DEV_SERVICE="${YOYOPOD_DEV_SERVICE:-yoyopod-dev.service}"
PROD_SERVICE="${YOYOPOD_SERVICE_NAME:-yoyopod-prod.service}"

if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "${DEV_SERVICE}"; then
        echo "prod ota guard: dev lane is active; skipping prod OTA"
        exit 75
    fi

    if ! systemctl is-active --quiet "${PROD_SERVICE}"; then
        echo "prod ota guard: prod lane is not active; skipping prod OTA"
        exit 75
    fi
fi

exit 0
