build:
	docker-compose build

up:
	docker-compose up

flake:
	docker-compose run --rm app sh -c "flake8"

test:
	docker-compose run --rm app sh -c "python manage.py test"

pip-compile:
	pip-compile -v --no-emit-index-url requirements.in

dev-pip-compile:
	pip-compile -v --no-emit-index-url requirements-dev.in