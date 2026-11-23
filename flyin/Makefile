# Variables
PYTHON = python3
PIP = pip
MAP = maps/easy1.txt

.PHONY: all install run debug clean lint lint-strict help

all: install lint

install:
	@echo "Instalando dependencias con pip..."
	$(PIP) install --upgrade pip
	$(PIP) install flake8 mypy pygame pytest

run:
	$(PYTHON) main.py $(MAP)

gui:
	$(PYTHON) main.py $(MAP) --gui

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	@echo "Limpiando archivos temporales y cachés de Python..."
	rm -rf __pycache__ .mypy_cache .pytest_cache *.pyc
	find . -type d -name "__pycache__" -exec rm -rf {} +

lint:
	@echo "Ejecutando chequeos de linter y tipado estricto..."
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

help:
	@echo "Comandos disponibles:"
	@echo "  make install     - Instala librerías requeridas"
	@echo "  make run MAP=... - Ejecuta la simulación por consola"
	@echo "  make gui MAP=... - Ejecuta la simulación con interfaz Pygame"
	@echo "  make lint        - Ejecuta análisis estático mypy y flake8"
	@echo "  make clean       - Elimina archivos .pyc y directorios de caché"