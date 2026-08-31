# AstraHeal LaTeX Submission Package

This directory contains compile-ready LaTeX source files formatted for formal conference and journal submissions (IEEE Aerospace Conference, AIAA SciTech Forum, etc.).

---

## 1. Directory Contents

- **`main.tex`**: Standard IEEEtran two-column conference paper template with full mathematical formulation, equations, benchmark tables, and citations.
- **`aiaa_paper.tex`**: AIAA / Standard single-column aerospace journal formatted template.
- **`references.bib`**: Complete BibTeX bibliography containing all NASA dataset, spacecraft FDIR, evidential deep learning, and aerospace citations.

---

## 2. Compiling with LaTeX

If you have a local TeX distribution (TeX Live / MacTeX / MikTeX):

```bash
cd docs/paper/latex

# Compile IEEEtran paper:
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Compile AIAA paper:
pdflatex aiaa_paper.tex
bibtex aiaa_paper
pdflatex aiaa_paper.tex
pdflatex aiaa_paper.tex
```

---

## 3. Uploading to Overleaf

1. Zip the `docs/paper/latex/` folder (or select `main.tex` and `references.bib`).
2. Go to [Overleaf](https://www.overleaf.com), click **New Project** -> **Upload Project**.
3. Set the compiler to **pdfLaTeX** and set main document to `main.tex` (or `aiaa_paper.tex`).
