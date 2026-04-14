COMPOSE = docker compose --env-file .env -f deploy/docker-compose.yml

.PHONY: init-config build up up-cache down restart logs ps health smoke config release-bundle verify-release github-repo verify-github

init-config:
	./scripts/init-config.sh

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

up-cache:
	$(COMPOSE) --profile cache up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) --profile cache up -d

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

health:
	curl -s http://127.0.0.1:$${APP_PORT:-18080}/api/health
	printf "\n"
	curl -s http://127.0.0.1:$${NGINX_PORT:-18090}/api/health
	printf "\n"

smoke:
	set -a; [ -f .env ] && . ./.env; set +a; ./scripts/smoke_test.sh

config:
	$(COMPOSE) config

release-bundle:
	./scripts/build_release_bundle.sh

verify-release:
	./scripts/verify_release_bundle.sh

github-repo:
	./scripts/build_github_repo.sh

verify-github:
	./scripts/verify_github_repo.sh
