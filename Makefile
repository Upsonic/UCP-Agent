#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

.PHONY: help install server client clean run

# Configuration
DB_DIR := /tmp/ucp_test
PRODUCTS_DB := $(DB_DIR)/products.db
TRANSACTIONS_DB := $(DB_DIR)/transactions.db
SERVER_PORT := 8182
SERVER_URL := http://localhost:$(SERVER_PORT)
TEST_DATA_DIR := $(shell pwd)/ucp-server/test_data

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

help: ## Show help
	@echo "$(GREEN)UCP Commerce Agent$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-10s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	uv sync

server: install ## Start server (init DB + run)
	@echo "$(GREEN)Initializing database...$(NC)"
	@mkdir -p $(DB_DIR)
	uv run --directory ucp-server import_csv.py \
		--products_db_path=$(PRODUCTS_DB) \
		--transactions_db_path=$(TRANSACTIONS_DB) \
		--data_dir=$(TEST_DATA_DIR)
	@echo "$(GREEN)Starting server on port $(SERVER_PORT)...$(NC)"
	@echo "$(YELLOW)Server: $(SERVER_URL)$(NC)"
	uv run --directory ucp-server server.py \
		--products_db_path=$(PRODUCTS_DB) \
		--transactions_db_path=$(TRANSACTIONS_DB) \
		--port=$(SERVER_PORT)

client: install ## Run client example
	@echo "$(GREEN)Running client...$(NC)"
	@echo "$(YELLOW)Server must be running at $(SERVER_URL)$(NC)"
	uv run --directory ucp-client-python simple_happy_path_client.py \
		--server_url=$(SERVER_URL)

clean: ## Clean databases
	@echo "$(GREEN)Cleaning databases...$(NC)"
	@rm -rf $(DB_DIR)
	@echo "$(GREEN)Done!$(NC)"

run: install ## Run the Upsonic shopping agent
	@echo "$(GREEN)Installing upsonic...$(NC)"
	uv pip install upsonic==0.69.3
	@echo "$(GREEN)Running Upsonic Shopping Agent...$(NC)"
	@echo "$(YELLOW)Server must be running at $(SERVER_URL)$(NC)"
	uv run upsonic_shopping_agent.py --server_url=$(SERVER_URL)
