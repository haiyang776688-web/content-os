# Primitive Contract

The authoritative v1 capability contract is:

```text
vnext/renderers/remotion/project/src/vre001/motion-primitive-contract-v1.json
```

Each entry declares its producer, semantic source, allowed layer kinds, behavior class, Renderer consumer, actual behavior, implementation status and fallback policy. Both Python pre-render QA and the TypeScript Renderer read this same JSON contract.

## Enforcement

- Unknown name: `MOTION_PRIMITIVE_UNKNOWN`
- Declared without a real consumer: `MOTION_PRIMITIVE_DECLARED_NOT_RENDERED`
- Known primitive on an unsupported layer: `MOTION_PRIMITIVE_UNSUPPORTED_FOR_LAYER`

All three are BLOCKER conditions. The Visual Compiler runs motion QA before returning final props. Storyboard Review combines motion QA with Asset Aspect-Ratio QA and disables approval when either fails. The Renderer repeats the assertion as a defense at the pixel boundary; it does not silently treat an invalid value as `NONE`.

## Geometry and media boundary

The primitive contract changes opacity, uniform scale, translation, clip/mask visibility or procedural geometry. It never owns `x/y`, destination width/height, crop pixels, font size or source-media aspect ratio. Visual Compiler remains the geometry owner.

Registered source media still uses its compiled `media_transform`, whose `scale_x` and `scale_y` are equal within 0.5%. Motion scale is a uniform container transform. Only procedural UNDERLINE and RELATION geometry may change width or SVG path visibility.
