.PHONY: test test-v test-one test-st test-ut test-fast coverage help clean

# 默认目标：运行所有测试
test:
	python -m pytest tests/ -q

# 运行所有测试（详细输出）
test-v:
	python -m pytest tests/ -v

# 运行特定测试文件
test-one:
	@echo "用法: make test-one FILE=tests/test_xxx.py"
	python -m pytest $(FILE) -v

# 运行快速测试（排除慢速测试）
test-fast:
	python -m pytest tests/ -v -m "not slow"

# 运行系统测试 (ST)
test-st:
	python -m pytest tests/st/ -v

# 运行单元测试 (UT)
test-ut:
	python -m pytest tests/ut/ -v

# 运行测试并生成覆盖率报告
coverage:
	python -m pytest tests/ --cov=log_analyzer --cov-report=html --cov-report=term

# 清理测试生成的文件
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

# 帮助信息
help:
	@echo "可用的测试命令:"
	@echo "  make test          - 运行所有测试（简洁输出）"
	@echo "  make test-v         - 运行所有测试（详细输出）"
	@echo "  make test-st        - 运行系统测试 (ST)"
	@echo "  make test-ut        - 运行单元测试 (UT)"
	@echo "  make test-one       - 运行特定测试文件 (FILE=tests/st/test_xxx.py)"
	@echo "  make test-fast      - 运行快速测试（排除慢速测试）"
	@echo "  make coverage       - 运行测试并生成覆盖率报告"
	@echo "  make clean          - 清理测试生成的文件"
	@echo ""
	@echo "示例:"
	@echo "  make test-st"
	@echo "  make test-ut"
	@echo "  make test-one FILE=tests/st/test_invalid_range_fault.py"
