# AstraHeal Scientific Reproducibility Guide

## 1. Environment Setup

```bash
# Recommended Python: Python 3.10+ / Conda Python
/opt/anaconda3/bin/python3 -m pip install -r requirements.txt
```

## 2. Running Full Automated Test Suite

```bash
/opt/anaconda3/bin/python3 -m pytest tests/ -v
```

## 3. Running Master Reproducibility Pipeline

To execute all 9 research experiments, generate publication figures, and produce JSON benchmark evaluations in a single deterministic pass:

```bash
/opt/anaconda3/bin/python3 run_all_experiments.py
```
