TAILWIND_CLI = bin/tailwindcss-linux-x64
TAILWIND_URL = https://github.com/tailwindlabs/tailwindcss/releases/download/v3.3.2/tailwindcss-linux-x64

WHEEL = dist/cbtk-0.1.0-py3-none-any.whl
SOURCES = $(wildcard cbtk/**/*.py cbtk/**/*.js cbtk/**/*.html) cbtk/www/output.css

all: $(WHEEL)

$(TAILWIND_CLI):
	mkdir -p bin
	curl -L $(TAILWIND_URL) -o $@
	chmod 755 $@

cbtk/www/output.css: input.css $(TAILWIND_CLI)
	$(TAILWIND_CLI) -i $< -o $@ --minify


$(WHEEL): $(SOURCES)
	poetry build
