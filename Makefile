.PHONY: all generate quality analyze sql test clean

all: generate quality analyze sql test

generate:
	python -m src.generate_dataset
	python -m src.generate_events

quality:
	python -m src.data_quality

analyze:
	python -m src.experiment

sql:
	python -m src.run_sql

test:
	python -m unittest discover -s tests -v

clean:
	rm -rf artifacts __pycache__ src/__pycache__ tests/__pycache__
