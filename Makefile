.PHONY: build up down clean logs test-add test-rm test-rep

# Build the server image and bring up the load balancer stack
build:
	docker build -t lb-server:latest ./server
	docker compose build

# Start the whole system (load balancer auto-spawns N=3 servers)
up:
	docker build -t lb-server:latest ./server
	docker compose up

# Start in detached (background) mode
up-detached:
	docker build -t lb-server:latest ./server
	docker compose up -d

# Stop everything
down:
	docker compose down

# Remove all containers, including dynamically-spawned servers
clean:
	docker rm -f $$(docker ps -aq) 2>/dev/null || true

# View live logs from the load balancer
logs:
	docker compose logs -f loadbalancer

# Quick manual tests against a running stack
test-rep:
	curl http://localhost:5000/rep

test-add:
	curl -X POST http://localhost:5000/add -H "Content-Type: application/json" -d '{"n": 2}'

test-rm:
	curl -X DELETE http://localhost:5000/rm -H "Content-Type: application/json" -d '{"n": 1}'