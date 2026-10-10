CC ?= cc
CUPS_CONFIG ?= cups-config
CPPFLAGS += $(shell $(CUPS_CONFIG) --cflags)
CFLAGS ?= -O2 -g
CFLAGS += -std=c11 -Wall -Wextra -Wpedantic -Wno-deprecated-declarations
LDFLAGS += $(shell $(CUPS_CONFIG) --ldflags)
LDLIBS += $(shell $(CUPS_CONFIG) --libs) -lm
PREFIX ?= /usr
FILTERDIR ?= $(PREFIX)/lib/cups/filter
PPDDIR ?= $(PREFIX)/share/ppd/nln41
all: build/raster-nln41
build:
	mkdir -p build
build/raster-nln41: src/raster-nln41.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)
build/generate: tests/generate.c | build
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)
test: all build/generate
	python3 tests/test_filter.py
	PYTHONDONTWRITEBYTECODE=1 python3 tests/test_installer.py
	cupstestppd -I filters -W translations ppd/NL-N41.ppd
	cupstestppd -I filters -W translations ppd/NL-N41-Network.ppd
install: all
	install -d $(DESTDIR)$(FILTERDIR) $(DESTDIR)$(PPDDIR)
	install -m 755 build/raster-nln41 $(DESTDIR)$(FILTERDIR)/raster-nln41
	install -m 644 ppd/NL-N41.ppd $(DESTDIR)$(PPDDIR)/NL-N41.ppd
clean:
	rm -rf build
.PHONY: all test install clean
