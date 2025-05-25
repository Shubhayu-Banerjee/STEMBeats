# 🎵 STEMBeats

*Music meets Physics in Python.*

**STEMBeats** is a mini-demo widget from the larger **STEMverse** project — built to help middle schoolers learn STEM concepts in a fun, creative way. This tool turns iconic physics formulas into music by generating beat patterns based on their variables and relationships. All done in Python. All powered by code.

## 🚀 What It Does

Each formula is turned into a rhythmic beat or audio pattern. You tweak the variables, hit run, and hear the math in motion. It's a playful way to explore how equations behave — using your ears instead of just your brain.

## 🎓 Included Physics Formulas

These are the formulas baked into the current version of STEMBeats:

| Formula           | Description                       |
|-------------------|-----------------------------------|
| `F = ma`          | Newton's Second Law (Force)       |
| `T = 2π√(L/g)`    | Period of a Pendulum              |
| `F = mv²/r`       | Centripetal Force                 |
| `V = IR`          | Ohm’s Law                         |
| `y = A sin(ωt + φ)`| Simple Harmonic Motion (Waves)   |

Each of these formulas generates a different pattern of beats, tempo, or pitch based on the values you feed into them.

## 📁 Files in This Repo

- `stembeats.py` – Main Python file for generating audio.
- `mp3 files ` – `.mp3` clips used to build each beat.
- `README.md` – This file you're reading.

## 🛠 Requirements

- Python 3.8+
- `pygame` or `pydub` (depending on your playback method)
- `numpy` for math operations

Install dependencies:

```bash
pip install customtkinter pygame pillow numpy sounddevice sympy tkinter
