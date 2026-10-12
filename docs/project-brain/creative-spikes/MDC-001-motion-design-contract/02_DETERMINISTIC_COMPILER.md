# Deterministic Motion Compiler

`DeterministicMotionCompiler` converts semantic phases into EDT metadata after ordinary Visual Compiler geometry and primitive selection.

Compiler-owned output includes:

- primitive-progress frame keyframes;
- uniform container-scale keyframes;
- secondary opacity-response keyframes;
- numeric phase offsets;
- primary, secondary and background-context clip assignments.

The same semantic input compiled twice produced the same compiled motion SHA-256:

```text
c70ba6095fb676620574314cfb541ddf4b47fa0e506bd22249f66a0fe82e140e
```

The Renderer consumes numeric keyframes. It does not contain policies for FOCUS, WARN, CONNECT, Shot Type, Visual Job or character role.

## Geometry and aspect-ratio boundary

Motion Design does not change `x/y`, destination boxes, crop regions, font size or source transforms. Registered media continues to carry one uniform `media_transform`. Secondary opacity and uniform container scale may change over time; independent `scale_x / scale_y` is forbidden.

The primitive-only and motion-designed props are byte-equivalent after removing only:

- `metadata.motion_design`;
- `motion_design_qa`;
- `compiled_motion_artifact`.

This verifies that Motion Design was the only A/B variable.
