# Particle Lab 0.2 - Accelerator Workshop

Run with `python -m pip install -r requirements.txt` then `python main.py`.

## Controls
- Select a component on the right, then click a grid square to install it.
- **R** rotates the next component (visual direction indicator); **right click** removes a component and refunds half its cost.
- **N** opens the physics notebook; **Space** starts/stops an experiment.
- Switch between **LINEAR** and **CYCLOTRON** using the top buttons.
- Tune accelerating voltage and magnetic field at the bottom.

## First experiment
The electron gun starts installed. Add an HV gap and a detector to its right, on the same row. Click RUN. Detect 10 electrons to earn a grant. Try adding magnets and changing the beam path.

## Cyclotron
The cyclotron is a preassembled demonstrator (not yet freely constructed). Protons gain energy on every half-turn and spiral outward. Adjust voltage and B to achieve extraction at 0.5 m. The RF timing is assumed to track the relativistic cyclotron frequency; real fixed-frequency cyclotrons cannot do this indefinitely.

## Model limitations
This is a **game prototype**, not a predictive accelerator design code. The linear beam uses a slowed visual motion speed and a local uniform B in magnet tiles. Accelerating gaps give a fixed energy increment once per tile traversal; real acceleration depends on electric-field geometry, polarity and phase. The cyclotron uses an idealized orbit radius and synchronously phased energy increments, with no space charge, losses, or injection/extraction hardware. Rotating components currently changes their direction marker and gun emission direction, not physical pipe connectivity. The vacuum tile is decorative for now. The linear beam has no wall collision model. Detector hits are tile-based. No saving yet.
