# Makefile for FinancialAgent project

.PHONY: help install install-dev test lint format clean run webapp cli docs

# 默认目标
help:
	@echo "Available targets:"
	@echo "  install       - Install production dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  test-cov      - Run tests with coverage"
	@echo "  lint          - Run linting (flake8, mypy)"
	@echo "  format        - Format code (black, isort)"
	@echo "  clean         - Clean build artifacts"
	@echo "  run           - Run CLI application"
	@echo "  webapp        - Start web application"
	@echo "  docs          - Generate documentation"
	@echo "  pre-commit    - Install pre-commit hooks"

# 安装依赖
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

# 测试
test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing

# 代码质量
lint:
	flake8 .
	mypy .

format:
	black .
	isort .

# 清理
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# 运行应用
run:
	python cli.py

webapp:
	python webapp/app.py

# 开发工具
pre-commit:
	pre-commit install

docs:
	@echo "Documentation generation not yet implemented"

# 数据库相关
init-db:
	python -c "from core.cache_manager import CacheManager; CacheManager().init_database()"

# 配置相关
init-config:
	cp config/config.example.yaml config/config.yaml
	cp .env.example .env
	@echo "Please edit config/config.yaml and .env files with your settings"

# 开发环境初始化
dev-setup: install-dev pre-commit init-config
	@echo "Development environment setup complete!"
	@echo "Next steps:"
	@echo "1. Edit config/config.yaml with your API keys"
	@echo "2. Edit .env with your environment variables"
	@echo "3. Run 'make test' to verify installation"

# Docker 相关（预留）
docker-build:
	@echo "Docker build not yet implemented"

docker-run:
	@echo "Docker run not yet implemented"

# 部署相关（预留）
deploy:
	@echo "Deployment not yet implemented"
