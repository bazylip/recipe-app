build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down --remove-orphans

run:
	docker-compose run app sh

flake:
	docker-compose run --rm app sh -c "flake8"

test: flake
	docker-compose run --rm app sh -c "python manage.py test"

pip-compile:
	pip-compile -v --no-emit-index-url requirements.in

dev-pip-compile:
	pip-compile -v --no-emit-index-url requirements-dev.in
