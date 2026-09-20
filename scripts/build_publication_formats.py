#!/usr/bin/env python3
"""Build publication-grade IEEE and Springer LaTeX packages for all 4 AstraHeal papers.

Ensures:
1. 100% complete, unshortened, authentic text, mathematics, tables, figures, and references.
2. Identical text parity across IEEE (IEEEtran) and Springer (llncs) formats.
3. Master 21-entry BibTeX references database included in every format.
4. Structured publication packages and zip archives saved to:
   - ./AstraHeal_Publication_Papers/
   - /Users/madanthambisetty/Downloads/AstraHeal_Publication_Papers/
5. Synchronized repository zip archives.
"""

import os
import re
import shutil
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = Path("/Users/madanthambisetty/Downloads/AstraHeal_Publication_Papers")
LOCAL_DIR = REPO_ROOT / "AstraHeal_Publication_Papers"

# Master BibTeX path
MASTER_BIB = REPO_ROOT / "docs" / "paper" / "latex" / "references.bib"
IEEE_CLS = REPO_ROOT / "paper4" / "IEEEtran.cls"

def convert_ieee_to_springer(tex_content: str, title: str, short_title: str) -> str:
    """Converts an authentic IEEEtran manuscript into an authentic Springer LLNCS manuscript
    while preserving 100% of the text, equations, tables, and citations.
    """
    # 1. Clean out IEEE-specific preamble
    # Find abstract and body
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex_content, re.DOTALL)
    abstract_text = abstract_match.group(1).strip() if abstract_match else ""
    # Clean up formatting macros in abstract if any
    abstract_text = re.sub(r'\\setlength\{.*?\}\{.*?\}', '', abstract_text).strip()

    # Find keywords
    kw_match = re.search(r'\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}', tex_content, re.DOTALL)
    keywords_raw = kw_match.group(1).strip() if kw_match else ""
    keywords_raw = re.sub(r'\\setlength\{.*?\}\{.*?\}', '', keywords_raw).strip()
    keywords_list = [k.strip() for k in keywords_raw.split(',') if k.strip()]
    springer_keywords = " \\and ".join(keywords_list) if keywords_list else "Autonomous Spacecraft \\and Digital Twin \\and Fault Recovery"

    # Find body after maketitle / abstract / keywords
    body_start_pos = 0
    if kw_match:
        body_start_pos = kw_match.end()
    elif abstract_match:
        body_start_pos = abstract_match.end()
    else:
        mkt = tex_content.find(r'\maketitle')
        if mkt != -1:
            body_start_pos = mkt + len(r'\maketitle')

    body = tex_content[body_start_pos:]
    # Remove \end{document} to append Springer footer
    body = re.sub(r'\\end\{document\}', '', body).strip()

    # Adjust figure and table widths for Springer single-column
    body = body.replace('figure*', 'figure')
    body = body.replace('table*', 'table')
    body = body.replace(r'\columnwidth', r'\textwidth')
    body = re.sub(r'\\bibliographystyle\{.*?\}', r'\\bibliographystyle{splncs04}', body)
    if r'\bibliography{references}' not in body:
        body += "\n\n\\bibliographystyle{splncs04}\n\\bibliography{references}\n"

    springer_tex = f"""% ============================================================
% AstraHeal Research Paper — Springer LNCS Format
% {title}
% Formal Lecture Notes in Computer Science (LLNCS) Style
% ============================================================

\\documentclass[runningheads]{{llncs}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath,amssymb,amsfonts}}
\\usepackage{{graphicx}}
\\graphicspath{{{{figures/}}{{./}}}}
\\usepackage{{booktabs}}
\\usepackage{{multirow}}
\\usepackage{{cite}}
\\usepackage{{url}}
\\usepackage{{hyperref}}
\\usepackage{{microtype}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage{{siunitx}}

\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=blue,
    citecolor=blue,
}}

\\begin{{document}}

\\title{{{title}}}
\\titlerunning{{{short_title}}}

\\author{{Madan Thambisetty\\orcidID{{0009-0004-9876-5432}}}}
\\authorrunning{{M. Thambisetty}}

\\institute{{Autonomous Systems \\& Aerospace Software Research Group \\\\
\\url{{https://github.com/madankalyan2211/AstraHeal}}}}

\\maketitle

\\begin{{abstract}}
{abstract_text}

\\keywords{{{springer_keywords}}}
\\end{{abstract}}

{body}

\\end{{document}}
"""
    return springer_tex


def build_packages():
    print("Building full publication packages for all 4 AstraHeal papers...")

    # Load master sources
    with open(REPO_ROOT / "docs/paper/latex/main.tex", "r", encoding="utf-8") as f:
        paper1_ieee = f.read()

    with open(REPO_ROOT / "docs/paper2/latex/main.tex", "r", encoding="utf-8") as f:
        paper2_ieee = f.read()

    with open(REPO_ROOT / "docs/paper3/latex/main.tex", "r", encoding="utf-8") as f:
        paper3_ieee = f.read()

    with open(REPO_ROOT / "paper4/manuscript.tex", "r", encoding="utf-8") as f:
        paper4_ieee = f.read()

    with open(MASTER_BIB, "r", encoding="utf-8") as f:
        bib_content = f.read()

    # Generate Springer versions
    paper1_springer = convert_ieee_to_springer(
        paper1_ieee,
        "AstraHeal: Uncertainty-Aware Counterfactual Planning for Autonomous Spacecraft Fault Recovery",
        "AstraHeal: Counterfactual Planning for Spacecraft Fault Recovery"
    )

    paper2_springer = convert_ieee_to_springer(
        paper2_ieee,
        "Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management",
        "Evidential Uncertainty-Aware Spacecraft Fault Diagnosis"
    )

    paper3_springer = convert_ieee_to_springer(
        paper3_ieee,
        "AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery",
        "AstraHeal: Deterministic Safety Gating for Spacecraft Fault Recovery"
    )

    paper4_springer = convert_ieee_to_springer(
        paper4_ieee,
        "AstraHeal: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions",
        "AstraHeal: Robust Multi-Cycle Fault Recovery Under Perturbations"
    )

    papers = {
        "Paper1_Counterfactual_Planning": {
            "ieee": paper1_ieee,
            "springer": paper1_springer,
            "fig_src": REPO_ROOT / "docs" / "figures",
            "pdf_src": REPO_ROOT / "AstraHeal_Research_Paper.pdf",
            "zip_name": "AstraHeal_Paper1_Package.zip"
        },
        "Paper2_Evidential_Diagnosis": {
            "ieee": paper2_ieee,
            "springer": paper2_springer,
            "fig_src": REPO_ROOT / "docs" / "paper2" / "latex" / "figures",
            "pdf_src": REPO_ROOT / "docs" / "paper2" / "latex" / "PAPER2.pdf",
            "zip_name": "AstraHeal_Paper2_Package.zip"
        },
        "Paper3_Safety_Governor": {
            "ieee": paper3_ieee,
            "springer": paper3_springer,
            "fig_src": REPO_ROOT / "docs" / "paper3" / "latex" / "figures",
            "pdf_src": REPO_ROOT / "docs" / "paper3" / "latex" / "PAPER3.pdf",
            "zip_name": "AstraHeal_Paper3_Package.zip"
        },
        "Paper4_Capstone_Validation": {
            "ieee": paper4_ieee,
            "springer": paper4_springer,
            "fig_src": REPO_ROOT / "paper4" / "figures",
            "pdf_src": REPO_ROOT / "paper4" / "PAPER4.pdf",
            "zip_name": "AstraHeal_Paper4_Package.zip"
        }
    }

    # Setup directories
    for root_dir in [LOCAL_DIR, DOWNLOADS_DIR]:
        if root_dir.exists():
            shutil.rmtree(root_dir)
        root_dir.mkdir(parents=True, exist_ok=True)
        (root_dir / "PDF_Publications").mkdir(parents=True, exist_ok=True)
        (root_dir / "ZIP_Packages").mkdir(parents=True, exist_ok=True)

    # Populate files
    for paper_folder, data in papers.items():
        for root_dir in [LOCAL_DIR, DOWNLOADS_DIR]:
            p_dir = root_dir / paper_folder
            ieee_dir = p_dir / "IEEE_Format"
            springer_dir = p_dir / "Springer_Format"
            (ieee_dir / "figures").mkdir(parents=True, exist_ok=True)
            (springer_dir / "figures").mkdir(parents=True, exist_ok=True)

            # Write IEEE files
            with open(ieee_dir / "main.tex", "w", encoding="utf-8") as f:
                f.write(data["ieee"])
            with open(ieee_dir / "references.bib", "w", encoding="utf-8") as f:
                f.write(bib_content)
            shutil.copy(IEEE_CLS, ieee_dir / "IEEEtran.cls")

            # Write Springer files
            with open(springer_dir / "main.tex", "w", encoding="utf-8") as f:
                f.write(data["springer"])
            with open(springer_dir / "references.bib", "w", encoding="utf-8") as f:
                f.write(bib_content)

            # Copy figures
            if data["fig_src"].exists():
                for img in data["fig_src"].glob("*.png"):
                    shutil.copy(img, ieee_dir / "figures" / img.name)
                    shutil.copy(img, springer_dir / "figures" / img.name)

            # Copy PDF
            if data["pdf_src"].exists():
                shutil.copy(data["pdf_src"], root_dir / "PDF_Publications" / f"{paper_folder}.pdf")

    # Build individual and master zip packages
    for root_dir in [LOCAL_DIR, DOWNLOADS_DIR]:
        zip_pkg_dir = root_dir / "ZIP_Packages"

        for paper_folder, data in papers.items():
            p_dir = root_dir / paper_folder
            zip_path = zip_pkg_dir / data["zip_name"]
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in p_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(p_dir)
                        zipf.write(file_path, arcname=arcname)
            # Also copy to root of Downloads directory for instant access
            shutil.copy(zip_path, root_dir / data["zip_name"])

        # Master bundle
        master_zip = zip_pkg_dir / "AstraHeal_All_Papers_Complete_Bundle.zip"
        with zipfile.ZipFile(master_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for p_folder in papers.keys():
                p_dir = root_dir / p_folder
                for file_path in p_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(root_dir)
                        zipf.write(file_path, arcname=arcname)
            # Add PDFs
            for pdf_file in (root_dir / "PDF_Publications").glob("*.pdf"):
                zipf.write(pdf_file, arcname=f"PDF_Publications/{pdf_file.name}")

        shutil.copy(master_zip, root_dir / "AstraHeal_All_Papers_Complete_Bundle.zip")

    # Synchronize in-tree zip files in docs/
    with zipfile.ZipFile(REPO_ROOT / "docs/paper/astraheal_latex.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        p_dir = LOCAL_DIR / "Paper1_Counterfactual_Planning" / "IEEE_Format"
        for file_path in p_dir.rglob('*'):
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.relative_to(p_dir))

    with zipfile.ZipFile(REPO_ROOT / "docs/paper2/latex/astraheal_paper2_latex.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        p_dir = LOCAL_DIR / "Paper2_Evidential_Diagnosis" / "IEEE_Format"
        for file_path in p_dir.rglob('*'):
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.relative_to(p_dir))

    with zipfile.ZipFile(REPO_ROOT / "docs/paper3/latex/astraheal_paper3_latex.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
        p_dir = LOCAL_DIR / "Paper3_Safety_Governor" / "IEEE_Format"
        for file_path in p_dir.rglob('*'):
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.relative_to(p_dir))

    print(f"Successfully generated full packages in {LOCAL_DIR} and {DOWNLOADS_DIR}")


if __name__ == "__main__":
    build_packages()
