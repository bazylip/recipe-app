build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down --remove-orphans

run:
	docker-compose run app sh

flake:
	docker-compose run --rm app sh -c "flake8 --ignore=E,W"

test: flake
	docker-compose run --rm app sh -c "python manage.py test"

pip-compile:
	pip-compile -v --no-emit-index-url requirements.in

dev-pip-compile:
	pip-compile -v --no-emit-index-url requirements-dev.in

make-migrations:
	docker-compose run --rm app sh -c "python manage.py makemigrations"

migrate:
	docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"
