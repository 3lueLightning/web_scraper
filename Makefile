install:
	@echo "Run install scraper"
	pip install .

dev_install:
	@echo "Run install scraper with dev dependencies"
	pip install .[dev]

test_with_logs:
	@echo "Run tests with logs"
	pytest --log-cli-level=INFO