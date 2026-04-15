diff:
	latexdiff ../2025-tvcg-initial-submission/main.tex main.tex > diff.tex
	pdflatex diff
	bibtex diff
	pdflatex diff
	bibtex diff
	pdflatex diff

clean: 
	rm -f *.aux *.log *.bbl *.blg *.brf *.cb *.ind *.idx *.ilg	\
	*.inx *.toc *.out $(DVIFILES) $(PSFILES) main.pdf *~
