LATEXMK ?= latexmk
LATEXDIFF ?= latexdiff
OLD_MAIN ?= main-old.tex
DIFF_TEX ?= diff.tex

.PHONY: paper resp supplement supp diff clean

paper:
	$(LATEXMK) -pdf main.tex

resp:
	$(LATEXMK) -pdf response-to-reviewers.tex

supplement:
	$(LATEXMK) -pdf supplementary-material.tex

supp: supplement

diff:
	$(LATEXDIFF) $(OLD_MAIN) main.tex > $(DIFF_TEX)
	pdflatex diff
	bibtex diff
	pdflatex diff
	bibtex diff
	pdflatex diff

clean:
	$(LATEXMK) -c main.tex response-to-reviewers.tex supplementary-material.tex
