PYTHON=python
JSON=AllCards.json.gz

.PHONY: clean

all: models

$(JSON):
	# wget -N https://mtgjson.com/json/$(JSON)
	# curl --remote-time -o ${JSON} https://mtgjson.com/json/$(JSON)
	## What we really want here is to use remote timestamp if file exists, else
	## use the current timestamp.
	curl -o ${JSON} https://mtgjson.com/json/$(JSON)

library: $(JSON)
	$(PYTHON) build_library.py && touch $@

models: library
	$(PYTHON) build_models.py && touch $@

clean:
	rm $(JSON)
