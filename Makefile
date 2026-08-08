.PHONY: all generate quality advanced analyze sql test clean

all: generate quality advanced analyze sql test

generate:
	python -m src.generate_dataset
	python -m src.generate_events

quality:
	python -m src.data_quality

advanced:
	python -m src.power --baseline 0.5116201859 --n-control 6024 --n-treatment 5976 --effect 0.0213450082
	python -m src.cuped

analyze:
	python -m src.experiment

sql:
	python -m src.run_sql

test:
	python -m unittest discover -s tests -v

clean:
	rm -rf artifacts __pycache__ src/__pycache__ tests/__pycache__
