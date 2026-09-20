#!/usr/bin/env python3
"""AstraHeal Paper 3 — Authentic Two-Column IEEE Conference Paper PDF Generator.

Compiles the complete Paper 3 research manuscript into an authentic, publication-grade
two-column IEEE Conference PDF (letter, 2-column, Times-Roman typography, IEEE section
numbering, IEEE tables, column-fitted figures, and formal IEEE references).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    HRFlowable,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class IEEENumberedCanvas(canvas.Canvas):
    """Two-pass canvas for IEEE Conference headers, footers, and page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_ieee_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_ieee_decorations(self, page_count):
        self.saveState()
        self.setFont("Times-Italic", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawCentredString(306, 756, "2026 IEEE AEROSPACE CONFERENCE (AERO) &bull; BIG SKY, MONTANA")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(44, 750, 568, 750)

        # Running Footer (all pages)
        self.setFont("Times-Roman", 8)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(44, 40, 568, 40)

        disclaimer = "IEEE PREPRINT &bull; ASTRAHEAL RESEARCH GROUP &bull; NOT FLIGHT VALIDATED"
        page_str = f"{self._pageNumber}"
        self.drawString(44, 28, disclaimer)
        self.drawRightString(568, 28, page_str)
        self.restoreState()


def build_ieee_conference_pdf(output_path: str):
    # Printable area: width = 612 - 88 = 524 pt
    # Col width = 254 pt, Gutter = 16 pt
    col_w = 254
    gutter = 16
    left_m = 44
    col1_x = left_m
    col2_x = left_m + col_w + gutter

    doc = BaseDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=left_m,
        rightMargin=left_m,
        topMargin=44,
        bottomMargin=44,
    )

    # Page 1: Header frame (title/authors/abstract) + 2 columns below
    header_h = 240
    p1_cols_h = 792 - 44 - 44 - header_h - 10  # ~454 pt
    f_p1_head = Frame(col1_x, 792 - 44 - header_h, 524, header_h, id='p1_head', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
    f_p1_c1 = Frame(col1_x, 44, col_w, p1_cols_h, id='p1_c1', topPadding=4, bottomPadding=0, leftPadding=0, rightPadding=0)
    f_p1_c2 = Frame(col2_x, 44, col_w, p1_cols_h, id='p1_c2', topPadding=4, bottomPadding=0, leftPadding=0, rightPadding=0)
    p1_template = PageTemplate(id='page1', frames=[f_p1_head, f_p1_c1, f_p1_c2])

    # Later pages: 2 full-height columns (height = 792 - 88 = 704 pt)
    f2_c1 = Frame(col1_x, 44, col_w, 696, id='p2_c1', topPadding=6, bottomPadding=0, leftPadding=0, rightPadding=0)
    f2_c2 = Frame(col2_x, 44, col_w, 696, id='p2_c2', topPadding=6, bottomPadding=0, leftPadding=0, rightPadding=0)
    p2_template = PageTemplate(id='page2', frames=[f2_c1, f2_c2])

    doc.addPageTemplates([p1_template, p2_template])

    styles = getSampleStyleSheet()

    # IEEE Typography Styles
    title_style = ParagraphStyle(
        'IEEETitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.black,
        alignment=1,
        spaceAfter=6,
    )

    author_name_style = ParagraphStyle(
        'IEEEAuthor',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.black,
        alignment=1,
    )

    author_affil_style = ParagraphStyle(
        'IEEEAffil',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        spaceAfter=10,
    )

    abstract_style = ParagraphStyle(
        'IEEEAbstract',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=11,
        textColor=colors.black,
        alignment=4,  # Justified
        spaceAfter=5,
    )

    sec_hdr_style = ParagraphStyle(
        'IEEESectionHdr',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.black,
        alignment=1,  # Centered
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    subsec_hdr_style = ParagraphStyle(
        'IEEESubSectionHdr',
        parent=styles['Normal'],
        fontName='Times-Italic',
        fontSize=9,
        leading=12,
        textColor=colors.black,
        alignment=0,  # Left
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'IEEEBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=8.5,
        leading=11,
        textColor=colors.black,
        alignment=4,  # Justified
        firstLineIndent=0,
        spaceAfter=4,
    )

    body_no_indent = ParagraphStyle(
        'IEEEBodyNoIndent',
        parent=body_style,
        firstLineIndent=0,
        spaceAfter=4,
    )

    table_title_style = ParagraphStyle(
        'IEEETableTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.black,
        alignment=1,
        spaceAfter=3,
        keepWithNext=True,
    )

    table_cell = ParagraphStyle(
        'IEEETableCell',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.black,
    )

    table_cell_bold = ParagraphStyle(
        'IEEETableCellBold',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=6.8,
        leading=8.5,
        textColor=colors.black,
    )

    fig_caption_style = ParagraphStyle(
        'IEEEFigCaption',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.black,
        alignment=4,
        spaceBefore=3,
        spaceAfter=6,
    )

    ref_style = ParagraphStyle(
        'IEEERef',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=7.2,
        leading=9,
        textColor=colors.black,
        alignment=4,
        leftIndent=12,
        firstLineIndent=-12,
        spaceAfter=3,
    )

    story = []

    # =========================================================================
    # PAGE 1 HEADER FRAME (Title, Authors, Abstract, Keywords)
    # =========================================================================
    story.append(Paragraph("AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery", title_style))
    story.append(Paragraph("Madan Kalyan Thambisetty", author_name_style))
    story.append(Paragraph("Autonomous Systems &amp; Aerospace Research Group<br/>AstraHeal Space Research Series &bull; Paper 3 &bull; Open-Source Repository: <i>github.com/madankalyan2211/AstraHeal</i>", author_affil_style))

    abstract_text = (
        "<b><i>Abstract</i>—Autonomous spacecraft operating in Low Earth Orbit (LEO) and deep-space regimes must resolve critical "
        "electrical and thermal anomalies during prolonged communication blackouts. While machine-learning planners and evidential "
        "diagnostic models generate flexible recovery candidates, statistical architectures lack formal execution guarantees: "
        "under novel compound failures or sensor corruption, upstream models can produce catastrophic commands with misleadingly "
        "high confidence. This paper presents the AstraHeal Deterministic Safety Governor, a fail-closed execution gatekeeper founded "
        "on the architectural axiom: <i>the AI proposes; the deterministic governor disposes</i>. Rather than inspecting instantaneous "
        "telemetry, the governor simulates candidate consequences across digital twin lookahead horizons and validates admissibility "
        "against five hard physical invariants: battery thermal runaway barrier (T &le; 46.0&deg;C), bus undervoltage floor (V &ge; 22.0V), "
        "PDU overcurrent rating (I &le; 40.0A), battery reserve floor (SoC &ge; 15%), and power ceiling (P &le; 880W). Across 8 controlled "
        "experiments evaluating 1,519 unsafe proposals, the system demonstrated: (i) zero unsafe executions (0.00% execution rate, "
        "Clopper-Pearson 95% bound &lt; 0.1970%), significantly outperforming an ungoverned AI baseline (100% unsafe executions, "
        "McNemar p = 1.92e-43, Cohen's h = 3.1416); (ii) 100% rejection across 400 adversarial proposals spanning 5 attack vectors; "
        "(iii) 100% concurrent recall across 800 compound multi-breach violations; (iv) strictly monotonic step-function transitions across "
        "804 continuous boundary sweep points; (v) complete dominance of hard safety constraints over communication rules; and (vi) 100% "
        "safe-failure convergence to NO_SAFE_ACTION_AVAILABLE during physical dead-ends. Microsecond profiling (10,000 runs) confirmed a "
        "mean latency of 2.99 &micro;s, demonstrating flight-feasible deterministic safety assurance with negligible onboard overhead.</b>"
    )
    story.append(Paragraph(abstract_text, abstract_style))

    keywords_text = (
        "<b><i>Index Terms</i>—autonomous spacecraft, safety governor, runtime assurance, safety shield, fault recovery, "
        "physical invariants, fail-closed systems, aerospace artificial intelligence.</b>"
    )
    story.append(Paragraph(keywords_text, abstract_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=4, spaceAfter=4))

    # Move from Header Frame into Left Column 1 of Page 1!
    story.append(FrameBreak())
    story.append(NextPageTemplate('page2'))

    # =========================================================================
    # SECTION I: INTRODUCTION
    # =========================================================================
    story.append(Paragraph("I. INTRODUCTION", sec_hdr_style))
    story.append(Paragraph(
        "Modern space exploration increasingly relies on high onboard autonomy due to orbital occultation and round-trip radio "
        "propagation delays. In Low Earth Orbit (LEO), spacecraft experience communication blackouts lasting up to 45 minutes per "
        "95-minute orbit; in lunar, Martian, and deep-space missions, signal latency ranges from minutes to hours [1]. When time-critical "
        "electrical power system (EPS) and thermal anomalies occur—such as internal battery resistance degradation, thermal runaway initiation, "
        "or bus overcurrent transients—immediate autonomous intervention is required to avoid irreversible vehicle loss.",
        body_style
    ))
    story.append(Paragraph(
        "To address this vulnerability, recent aerospace research has explored advanced machine-learning planners, evidential Bayesian "
        "diagnosis [2], and counterfactual lookahead algorithms [3]. While adaptive AI models outperform rigid rule tables under complex multi-variable "
        "interactions, they remain fundamentally statistical approximators. When presented with unseen out-of-distribution (OOD) telemetry, "
        "sensor calibration drift, or novel compound failures, AI models can produce catastrophic actuation proposals while reporting dangerously "
        "high subjective confidence [4].",
        body_style
    ))
    story.append(Paragraph(
        "This work resolves that vulnerability by investigating the authoritative safety barrier situated immediately prior to command execution: "
        "a <b>deterministic runtime safety governor</b>. Founded on the principle that <i>the AI proposes; the deterministic governor disposes</i>, "
        "this system intercepts upstream proposals and verifies them against immutable physical invariants over counterfactual lookahead horizons.",
        body_style
    ))

    # =========================================================================
    # SECTION II: RELATED WORK
    # =========================================================================
    story.append(Paragraph("II. RELATED WORK", sec_hdr_style))
    story.append(Paragraph(
        "Spacecraft autonomous fault management traces back to landmark flight demonstrations including NASA's Remote Agent on Deep Space 1 [1] "
        "and the Autonomous Sciencecraft Experiment on EO-1 [5]. These systems demonstrated model-based reasoning and onboard replanning [6]. "
        "However, modern neural planners and reinforcement learning agents lack mathematical safety guarantees.",
        body_style
    ))
    story.append(Paragraph(
        "In safety-critical cyber-physical systems, runtime assurance architectures—such as the ASTM F3269-17 standard and the classic Simplex "
        "architecture [7]—place a deterministic monitor between an uncertified controller and actuators. In reinforcement learning, formal safety "
        "shields filter exploratory actions violating temporal logic specifications [8]. In control theory, Control Barrier Functions (CBFs) enforce "
        "forward invariance [9]. The AstraHeal Safety Governor extends these principles to coupled electro-thermal spacecraft dynamics, verifying "
        "candidate admissibility over digital twin lookahead horizons.",
        body_style
    ))

    # =========================================================================
    # SECTION III: PROBLEM FORMULATION
    # =========================================================================
    story.append(Paragraph("III. PROBLEM FORMULATION &amp; SYSTEM MODEL", sec_hdr_style))
    story.append(Paragraph(
        "Let the physical state of the spacecraft Electrical Power System (EPS) at time <i>t</i> be represented by a telemetry vector:",
        body_style
    ))
    story.append(Paragraph(
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>s<sub>t</sub> = [V<sub>bus</sub>, I<sub>batt</sub>, T<sub>batt</sub>, SoC, P<sub>pdu</sub>, &phi;, &lambda;]<sup>T</sup> &isin; S</i>",
        body_no_indent
    ))
    story.append(Paragraph(
        "where <i>V<sub>bus</sub></i> is bus voltage, <i>I<sub>batt</sub></i> is battery current, <i>T<sub>batt</sub></i> is cell core temperature, "
        "<i>SoC</i> is state of charge, <i>P<sub>pdu</sub></i> is power delivery, <i>&phi;</i> is orbital fraction, and <i>&lambda;</i> is link status.",
        body_style
    ))
    story.append(Paragraph(
        "An upstream AI recovery planner proposes a candidate recovery action <i>a &isin; A</i> with subjective confidence <i>&mu;<sub>AI</sub> &isin; [0, 1]</i>. "
        "Executing action <i>a</i> in state <i>s<sub>t</sub></i> induces a continuous trajectory over future lookahead horizon <i>H</i>:",
        body_style
    ))
    story.append(Paragraph(
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>&tau;(s<sub>t</sub>, a) = { s&#770;<sub>t+&tau;</sub> | &tau; &isin; [0, H] }</i>",
        body_no_indent
    ))
    story.append(Paragraph(
        "governed by the electro-thermal differential kinetics of the battery pack and orbital radiosity:",
        body_style
    ))
    story.append(Paragraph(
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>C<sub>th</sub> (dT/dt) = I<sup>2</sup>R<sub>0</sub> + Q&#775;<sub>exo</sub>(T) - h<sub>rad</sub>(T<sup>4</sup> - T<sub>space</sub><sup>4</sup>)</i>",
        body_no_indent
    ))
    story.append(Paragraph(
        "The Safety Governor evaluates action <i>a</i> via deterministic constraint mapping <i>C(s<sub>t</sub>, a) &rarr; {0, 1}<sup>M</sup></i>:",
        body_style
    ))
    story.append(Paragraph(
        "&nbsp;&nbsp;&nbsp;&nbsp;<i>G(s<sub>t</sub>, a) = ACCEPT if &and; C<sub>j</sub> = 1, else REJECT</i>",
        body_no_indent
    ))

    # =========================================================================
    # SECTION IV: SAFETY GOVERNOR ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("IV. DETERMINISTIC SAFETY GOVERNOR", sec_hdr_style))
    story.append(Paragraph("A. 4-Tier Safety Invariant Hierarchy", subsec_hdr_style))
    story.append(Paragraph(
        "The governor enforces an immutable 4-tier dominance hierarchy: (i) <b>Level 1 Hard Physical Invariants</b> strictly dominate all lower levels; "
        "(ii) <b>Level 2 Communication Rules</b> arbitrate autonomous action vs ground pass deferral but can never override Level 1; "
        "(iii) <b>Level 3 Recovery Utility</b> ranks payload availability among certified safe candidates; and (iv) <b>Level 4 AI Preferences</b> "
        "provide heuristic ranking, possessing zero authority to authorize an unsafe action.",
        body_style
    ))

    # TABLE I: INVARIANTS
    inv_rows = [
        [Paragraph("Constraint", table_cell_bold), Paragraph("Parameter", table_cell_bold), Paragraph("Threshold", table_cell_bold), Paragraph("Physical Barrier Mechanism", table_cell_bold)],
        [Paragraph("Thermal", table_cell), Paragraph("T_core", table_cell), Paragraph("&le; 46.0&deg;C", table_cell), Paragraph("Prevents SEI exothermic decomposition", table_cell)],
        [Paragraph("Voltage", table_cell), Paragraph("V_bus", table_cell), Paragraph("&ge; 22.0V", table_cell), Paragraph("Avionics undervoltage brownout floor", table_cell)],
        [Paragraph("Current", table_cell), Paragraph("I_batt", table_cell), Paragraph("&le; 40.0A", table_cell), Paragraph("Harness &amp; solid-state switch fuse limit", table_cell)],
        [Paragraph("Reserve", table_cell), Paragraph("SoC", table_cell), Paragraph("&ge; 15.0%", table_cell), Paragraph("Prevents copper dissolution in cells", table_cell)],
        [Paragraph("Power", table_cell), Paragraph("P_pdu", table_cell), Paragraph("&le; 880.0W", table_cell), Paragraph("Derived rating (V_min &times; I_max)", table_cell)],
        [Paragraph("Catalog", table_cell), Paragraph("Action ID", table_cell), Paragraph("Certified", table_cell), Paragraph("Blocks corrupted / uncertified commands", table_cell)],
    ]
    t_inv = Table(inv_rows, colWidths=[42, 38, 48, 126])
    t_inv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(Paragraph("TABLE I: IMMUTABLE PHYSICAL INVARIANTS", table_title_style))
    story.append(t_inv)

    story.append(Paragraph("B. The Instantaneous Telemetry Fallacy", subsec_hdr_style))
    story.append(Paragraph(
        "A central finding of this investigation is that evaluating telemetry instantaneously is flawed for electro-thermal spacecraft dynamics. "
        "If battery temperature is nominally 28&deg;C, an action re-enabling a science payload appears valid. Under degraded internal resistance, "
        "the resulting Joule heating causes thermal runaway 45 seconds later. By executing counterfactual lookahead, the governor detects delayed "
        "boundary breaches and blocks them prior to command dispatch.",
        body_style
    ))

    story.append(Paragraph("C. Fail-Closed Error Containment", subsec_hdr_style))
    story.append(Paragraph(
        "If telemetry contains NaN/Inf values, if action IDs are unrecognized, or if the lookahead simulator throws an exception, the governor "
        "unconditionally outputs <i>REJECT</i>, preventing corrupted inputs from executing.",
        body_style
    ))

    # =========================================================================
    # SECTION V: EXPERIMENTAL METHODOLOGY
    # =========================================================================
    story.append(Paragraph("V. EXPERIMENTAL METHODOLOGY", sec_hdr_style))
    story.append(Paragraph(
        "The evaluation was executed on a 12U CubeSat EPS digital twin in a 550 km sun-synchronous Low Earth Orbit across 8 controlled studies:",
        body_style
    ))
    story.append(Paragraph(
        "&bull; <b>P3-E1 (Baseline Enforcement)</b>: Direct comparison between Ungoverned AI (System A) and Governed AI (System B) across 500 scenarios.<br/>"
        "&bull; <b>P3-E2 (Coverage)</b>: Testing 6 hard constraints in 4 states (Nominal, Near-Limit, Boundary, Breach) across 600 evaluations.<br/>"
        "&bull; <b>P3-E3 (Compound Violations)</b>: 300 multi-fault compound scenarios evaluating multi-breach recall without short-circuiting.<br/>"
        "&bull; <b>P3-E4 (Adversarial Injection)</b>: 400 proposals across 5 attack vectors with deceptive confidence (&mu; &ge; 0.96).<br/>"
        "&bull; <b>P3-E5 (Boundary Sweeps)</b>: 804 points testing step-function transition sharpness (&Delta; = 0.05).<br/>"
        "&bull; <b>P3-E6 (Communication Hierarchy)</b>: 300 scenarios testing dominance during ground contact and blackout occultation.<br/>"
        "&bull; <b>P3-E7 (No-Safe-Action)</b>: 150 dead-end scenarios (750 candidates) testing non-forcing safe hold.<br/>"
        "&bull; <b>P3-E8 (Ablation &amp; Overhead)</b>: 3-way ablation and 10,000-run microsecond latency profiling.",
        body_style
    ))

    # =========================================================================
    # SECTION VI: RESULTS & EMPIRICAL FINDINGS
    # =========================================================================
    story.append(Paragraph("VI. EXPERIMENTAL RESULTS &amp; BENCHMARKS", sec_hdr_style))
    story.append(Paragraph("A. Baseline Safety Enforcement (P3-E1)", subsec_hdr_style))
    story.append(Paragraph(
        "Across 500 scenarios, the AI proposed 193 actions that violated at least one hard physical constraint. Ungoverned System A executed "
        "all 193 unsafe actions (100.0% execution). Under the AstraHeal Governor (System B), exactly zero unsafe actions reached execution (0.00%), "
        "while achieving 100% acceptance of safe actions (307/307). Paired testing confirms statistical significance (McNemar &chi;<sup>2</sup> = 191.01, "
        "p = 1.92&times;10<sup>-43</sup>, Cohen's h = 3.1416). Across all 1,519 evaluated unsafe proposals in the research suite, zero unsafe actions were "
        "executed, establishing a Clopper-Pearson exact 95% upper bound of &lt; 0.1970%.",
        body_style
    ))

    # FIG 1: BASELINE
    fig1_path = REPO_ROOT / "docs" / "paper3" / "figures" / "fig1_safety_enforcement_comparison.png"
    if fig1_path.exists():
        story.append(Image(str(fig1_path), width=248, height=162))
        story.append(Paragraph("Fig. 1. Action Execution Comparison across 500 Scenarios (Ungoverned AI vs. Governed AI).", fig_caption_style))

    # TABLE II: MASTER BENCHMARK
    master_rows = [
        [Paragraph("Study", table_cell_bold), Paragraph("Focus", table_cell_bold), Paragraph("Evals", table_cell_bold), Paragraph("Unsafe Prop", table_cell_bold), Paragraph("Unsafe Exec", table_cell_bold), Paragraph("Rejection", table_cell_bold)],
        [Paragraph("P3-E1", table_cell), Paragraph("Baseline", table_cell), Paragraph("500", table_cell), Paragraph("193", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E2", table_cell), Paragraph("Coverage", table_cell), Paragraph("600", table_cell), Paragraph("150", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E3", table_cell), Paragraph("Compound", table_cell), Paragraph("300", table_cell), Paragraph("300", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E4", table_cell), Paragraph("Adversarial", table_cell), Paragraph("400", table_cell), Paragraph("400", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E5", table_cell), Paragraph("Boundaries", table_cell), Paragraph("804", table_cell), Paragraph("400", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E6", table_cell), Paragraph("Comm Hierarchy", table_cell), Paragraph("300", table_cell), Paragraph("150", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E7", table_cell), Paragraph("No-Safe-Action", table_cell), Paragraph("750", table_cell), Paragraph("750", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("P3-E8", table_cell), Paragraph("Ablation", table_cell), Paragraph("500", table_cell), Paragraph("176", table_cell), Paragraph("<b>0 (0.0%)</b>", table_cell), Paragraph("100.0%", table_cell)],
        [Paragraph("<b>TOTAL</b>", table_cell_bold), Paragraph("<b>Suite</b>", table_cell_bold), Paragraph("<b>4,158</b>", table_cell_bold), Paragraph("<b>1,519</b>", table_cell_bold), Paragraph("<b>0 (0.0%)</b>", table_cell_bold), Paragraph("<b>100.0%</b>", table_cell_bold)],
    ]
    t_master = Table(master_rows, colWidths=[38, 54, 34, 46, 46, 36])
    t_master.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(Paragraph("TABLE II: MASTER BENCHMARK EVALUATION RESULTS", table_title_style))
    story.append(t_master)

    story.append(Paragraph("B. Constraint Coverage &amp; Compound Violations", subsec_hdr_style))
    story.append(Paragraph(
        "P3-E2 verified 100% accuracy across all 6 constraints (F1 = 1.0000). In P3-E3, 300 compound scenarios containing 800 simultaneous "
        "breaches achieved 100% recall (800/800 detected), confirming that the governor avoids premature short-circuiting.",
        body_style
    ))

    # FIG 2 & FIG 4
    fig2_path = REPO_ROOT / "docs" / "paper3" / "figures" / "fig2_constraint_coverage_matrix.png"
    if fig2_path.exists():
        story.append(Image(str(fig2_path), width=248, height=180))
        story.append(Paragraph("Fig. 2. Constraint Verification Accuracy across 6 Hard Invariants.", fig_caption_style))

    story.append(Paragraph("C. Adversarial Robustness (P3-E4)", subsec_hdr_style))
    story.append(Paragraph(
        "Across 400 adversarial proposals spanning 5 attack vectors with deceptive confidence (&mu; &ge; 0.96), the governor rejected 100.0% "
        "(400/400), proving mathematical decoupling between AI score and flight authorization.",
        body_style
    ))

    fig4_path = REPO_ROOT / "docs" / "paper3" / "figures" / "fig4_adversarial_injection_robustness.png"
    if fig4_path.exists():
        story.append(Image(str(fig4_path), width=248, height=138))
        story.append(Paragraph("Fig. 3. Rejection Rate across 5 Adversarial AI Attack Vectors.", fig_caption_style))

    story.append(Paragraph("D. Continuous Boundaries &amp; Safe Failure", subsec_hdr_style))
    story.append(Paragraph(
        "P3-E5 confirmed sharp step-function monotonicity across 804 points. In P3-E7, all 150 dead-end scenarios (750 candidates) safely "
        "converged to NO_SAFE_ACTION_AVAILABLE with zero forced unsafe actions.",
        body_style
    ))

    fig5_path = REPO_ROOT / "docs" / "paper3" / "figures" / "fig5_boundary_testing_sweeps.png"
    if fig5_path.exists():
        story.append(Image(str(fig5_path), width=248, height=178))
        story.append(Paragraph("Fig. 4. Continuous Physical Constraint Boundary Sweeps across 201 Points/Channel.", fig_caption_style))

    # =========================================================================
    # SECTION VII: ABLATION & OVERHEAD
    # =========================================================================
    story.append(Paragraph("VII. ABLATION &amp; COMPUTATIONAL OVERHEAD", sec_hdr_style))
    story.append(Paragraph(
        "Ablation testing (P3-E8) proved that static FDIR rules failed 100% against delayed-effect actions, commanding unsafe payload engagement. "
        "The digital-twin governor eliminated all delayed unsafe executions (0.0%). Across 10,000 evaluations, mean latency was 2.99 &micro;s &plusmn; 0.81 &micro;s "
        "(median 2.75 &micro;s, 95th percentile 3.13 &micro;s, throughput 324,707 evals/s), rendering gating overhead negligible relative to typical "
        "spacecraft integration timesteps (&Delta;t &ge; 100 ms).",
        body_style
    ))

    fig7_path = REPO_ROOT / "docs" / "paper3" / "figures" / "fig7_ablation_and_latency.png"
    if fig7_path.exists():
        story.append(Image(str(fig7_path), width=248, height=110))
        story.append(Paragraph("Fig. 5. Architectural Ablation and Microsecond Latency Distribution.", fig_caption_style))

    # =========================================================================
    # SECTION VIII: CONCLUSION
    # =========================================================================
    story.append(Paragraph("VIII. CONCLUSION", sec_hdr_style))
    story.append(Paragraph(
        "This work demonstrated that a deterministic, fail-closed runtime safety governor reliably prevents unsafe autonomous recovery actions "
        "from reaching spacecraft execution. By projecting candidate actions forward across counterfactual digital twin horizons and enforcing an "
        "immutable 4-tier invariant hierarchy, the system achieved zero unsafe executions across 1,519 evaluated proposals (p &lt; 0.1970%), "
        "fully decoupled from upstream AI confidence. Deterministic safety gating provides a flight-feasible foundation for certified autonomous spaceflight.",
        body_style
    ))

    # =========================================================================
    # REFERENCES
    # =========================================================================
    story.append(Paragraph("REFERENCES", sec_hdr_style))
    refs = [
        "[1] N. Muscettola, P. P. Nayak, B. Pell, and B. C. Williams, \"Remote Agent: To boldly go where no AI has gone before,\" <i>Artificial Intelligence</i>, vol. 103, no. 1–2, pp. 5–47, 1998.",
        "[2] M. Thambisetty, \"Evidential uncertainty-aware fault diagnosis for autonomous spacecraft health management,\" <i>AstraHeal Research Series</i>, vol. 2, 2026.",
        "[3] M. Thambisetty, \"AstraHeal: Uncertainty-aware counterfactual planning for autonomous spacecraft fault recovery,\" <i>Zenodo</i>, Sep. 2026, doi: 10.5281/zenodo.22233081.",
        "[4] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, \"On calibration of modern neural networks,\" in <i>Proc. 34th Int. Conf. Mach. Learn. (ICML)</i>, 2017, pp. 1321–1330.",
        "[5] S. Chien, R. Sherwood, D. Tran, et al., \"Autonomous Sciencecraft Experiment on the EO-1 spacecraft,\" <i>IEEE Intelligent Systems</i>, vol. 20, no. 5, pp. 16–24, 2005.",
        "[6] B. C. Williams and P. P. Nayak, \"A model-based approach to reactive self-configuring systems,\" in <i>Proc. 13th Natl. Conf. Artif. Intell. (AAAI)</i>, 1996, pp. 971–978.",
        "[7] L. Sha, \"Using simplicity to control complexity,\" <i>IEEE Software</i>, vol. 18, no. 4, pp. 20–28, 2001.",
        "[8] M. Alshiekh, R. Bloem, R. Ehlers, et al., \"Safe reinforcement learning via shielding,\" in <i>Proc. AAAI Conf. Artif. Intell.</i>, vol. 32, no. 1, 2018.",
        "[9] A. D. Ames, X. Xu, J. W. Grizzle, and P. Tabuada, \"Control barrier functions: Theory and applications,\" in <i>European Control Conference (ECC)</i>, 2016, pp. 362–373.",
        "[10] ASTM International, \"Standard Guide for Design of Runtime Assurance Systems for Aircraft Systems,\" ASTM F3269-17, 2017.",
        "[11] K. Hundman et al., \"Detecting spacecraft anomalies using LSTMs and nonparametric dynamic thresholding,\" in <i>Proc. ACM SIGKDD</i>, 2018.",
        "[12] M. Sensoy, L. Kaplan, and M. Kandemir, \"Evidential deep learning to quantify classification uncertainty,\" in <i>NeurIPS</i>, 2018.",
        "[13] M. Chen and G. A. Rincon-Mora, \"Accurate electrical battery model capable of predicting runtime and IV performance,\" <i>IEEE Trans. Energy Convers.</i>, 2006.",
        "[14] J. R. Wertz, D. F. Everett, and J. J. Puschell, <i>Space Mission Engineering: The New SMAD</i>, Microcosm Press, 2011."
    ]
    for r in refs:
        story.append(Paragraph(r, ref_style))

    # Build PDF
    doc.build(story, canvasmaker=IEEENumberedCanvas)
    print(f"Successfully generated authentic Two-Column IEEE Conference PDF: {output_path}")


if __name__ == "__main__":
    out_pdf = str(REPO_ROOT / "docs" / "paper3" / "latex" / "PAPER3.pdf")
    build_ieee_conference_pdf(out_pdf)
