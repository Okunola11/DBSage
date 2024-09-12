### DOCKER CLI COMMANDS

ENV_PATH=./.env

.PHONY: docker-run-all
docker-run-all:
	# stop and remove all running containers to avoid name conflicts

	docker network create sage-network

	docker run -d \
		--name db-sage-dev \
		--network sage-network \
		--env-file=${ENV_PATH} \
		-v ./:/usr/src/ \
		-p 7002:7002 \
		--restart unless-stopped \
		db-sage-dev:0

	# -v venv:/usr/src/.venv:delegated


.PHONY: docker-start
docker-start:
	-docker start db-sage-dev
	-docker start test-db

.PHONY: docker-stop
docker-stop:
	-docker stop db-sage-dev

.PHONY: docker-rm
docker-rm:
	-docker container rm db-sage-dev
	-docker network rm sage-network
	