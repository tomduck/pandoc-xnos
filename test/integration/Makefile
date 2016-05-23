
PANDOC = pandoc-1.17.0.2
#PANDOC = pandoc-1.15.2

FLAGS = --filter pandoc-fignos --filter pandoc-eqnos --filter pandoc-tablenos

all: out/demo.pdf out/demo.tex out/demo.html out/demo.epub out/demo.md out/demo.json

out/demo.pdf: demo.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	$(PANDOC) $< $(FLAGS) -o $@ # --include-in-header=cleveref.tex

out/demo.tex: demo.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	$(PANDOC) $< $(FLAGS) -o $@ --standalone

out/demo.html: demo.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	$(PANDOC) $< --standalone $(FLAGS) -o $@
	cp -R plot.png out

out/demo.epub: demo.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	$(PANDOC) $< -t epub3 $(FLAGS) -o $@

out/demo.md: demo.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	$(PANDOC) $< $(FLAGS)  -o $@

out/demo.json: demo.md
	@if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi
	$(PANDOC) $< -o $@


.PHONY: clean

clean:
	rm -rf out
