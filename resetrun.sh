export FLASK_APP=timeline && export FLASK_ENV=development

flask init-db
flask run --host=0.0.0.0 --port=80 >> log.txt 2>&1 &
