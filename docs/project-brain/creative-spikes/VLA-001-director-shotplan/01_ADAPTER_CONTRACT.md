# VLA-001 · Adapter Contract

## Inputs

The adapter accepts:

- formal `DirectorIR` scenes and beats;
- a locked script ID and immutable script segments;
- fact-to-evidence bindings;
- registered evidence assets and named regions;
- frozen timings/captions.

It validates script identity, segment references, fact references, evidence registration and asset hashes before compilation.

## Decisions owned by the adapter

For every ordinary Director beat, deterministic editorial policy selects:

- Visual Job;
- per-beat Visual Mode;
- Shot Type;
- PRIMARY and supporting/background protagonists;
- evidence asset and registered semantic region;
- Evidence Treatment;
- Character Role;
- Motion Semantic.

The adapter does not receive or emit `x`, `y`, width, height, pixel crop, font size, CSS, absolute asset path or raw animation parameters.

## Decisions owned by Visual Compiler

`VisualCompiler` remains the sole owner of:

- canvas geometry and safe areas;
- evidence/character/text boxes;
- normalized crop geometry sourced from the Asset Registry;
- typography size and treatment tokens;
- motion primitive parameters;
- explicit Remotion layer envelopes.

The compiler records the originating ShotPlan ID, schema version, script ID, beat/segment identity and every semantic decision in its output. The renderer receives explicit layers and primitives. It contains no branches for Visual Job, Visual Mode, Shot Type or Evidence Treatment.

## Production boundary

The new code lives under `vnext/phase2/experimental/` and a separate `vla001-index.tsx` composition. No production route imports or activates it.
