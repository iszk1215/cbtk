TAILWIND_CLI = bin/tailwindcss-linux-x64
TAILWIND_URL = https://github.com/tailwindlabs/tailwindcss/releases/download/v3.3.2/tailwindcss-linux-x64

WHEEL = dist/cbtk-0.1.0-py3-none-any.whl
SOURCES = $(shell find cbtk -not -path '*/__pycache__/*' -a -type f)
TEMPLATES = $(shell find cbtk/www/templates -name '*.html')

all: test $(WHEEL)

$(TAILWIND_CLI):
	mkdir -p bin
	curl -L $(TAILWIND_URL) -o $@
	chmod 755 $@

cbtk/www/output.css: misc/input.css $(TAILWIND_CLI) $(TEMPLATES)
	$(TAILWIND_CLI) -i $< -c misc/tailwind.config.js -o $@ --minify

$(WHEEL): $(SOURCES) cbtk/www/output.css
	poetry build

test:
	poetry run pytest
