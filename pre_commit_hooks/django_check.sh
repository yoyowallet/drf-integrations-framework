#!/bin/bash
set -a
[ -f .env ] && source .env
set +a

# Ensure poetry is in PATH (adjust the path if necessary)
export PATH="$HOME/.local/bin:$PATH"

# Run the command
DJANGO_SETTINGS_MODULE=example.settings poetry run django-admin check
