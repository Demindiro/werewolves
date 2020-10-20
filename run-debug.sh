#!/bin/bash -e

if [[ "$VIRTUAL_ENV" == "" ]]
then
	source venv/bin/activate
fi

FLASK_ENV=development FLASK_APP=web.py ./web.py $@
