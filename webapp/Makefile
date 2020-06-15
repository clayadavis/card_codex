PYTHON=python
JSON=AllCards.json.gz

.PHONY: clean

all: models

$(JSON):
	wget -N https://mtgjson.com/json/$(JSON)

library: $(JSON)
	$(PYTHON) build_library.py && touch $@

models: library
	$(PYTHON) build_models.py && touch $@

clean:
	rm $(JSON)
