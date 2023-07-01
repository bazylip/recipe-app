build:
	docker-compose build

up:
	docker-compose up

flake:
	docker-compose run --rm app sh -c "flake8"
