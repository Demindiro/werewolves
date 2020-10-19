#!/bin/bash -e

if [[ "$VIRTUAL_ENV" == "" ]]
then
	source venv/bin/activate
fi

FLASK_APP=main.py flask run $@
