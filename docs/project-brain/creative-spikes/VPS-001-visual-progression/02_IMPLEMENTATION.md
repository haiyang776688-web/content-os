# VPS-001 · Experimental implementation

The hand-authored `ground_truth.json` is a Spike artifact, not a DirectorIR extension. `vnext/phase2/experimental/visual_progression.py` validates that each existing beat has 2–4 contiguous visual states, then compiles the selected 5.56–24.68-second interval into ordinary `EDTClip` records and Remotion props. The formal production store and CS-001 artifacts are read-only throughout this experiment.

The A props are a time slice of CS-001's final Remotion props. The compiler adjusts the master voice's `source_in/source_out` to 5.56/24.68 seconds and offsets clip positions to the 19.12-second local timeline. A representative A frame at local 4.00 seconds differs from CS-001's master frame at 9.56 seconds by only about 0.22/255 mean value per RGB channel, consistent with re-encoding rather than a changed composition.

B replaces only the selected interval's visual tracks. It retains the same underlying research and script screenshot asset IDs, creates deterministic pixel crops in the ignored Remotion preview directory, and emits MEDIA, ELEMENT and TEXT clips. The yellow highlight is a transparent, frame-sized SVG ELEMENT whose rectangle is mapped to a region inside the cropped screenshot. It is not an LLM-generated replacement image. Existing voice clips remain byte-identical in props. The two clipped `SEG-04` subtitle fragments are regrouped into two complete cues; the compiler rejects any repair that changes their concatenated text.

Supported operations in this experimental contract: `FULL_FRAME_MEDIA`, `ZOOM_TO_REGION`, `HIGHLIGHT_RECT`, `SHOW_TEXT`, `CALLOUT_TEXT`. These are the only operations needed for this Ground Truth. State changes use hard cuts; two crop states optionally retain 1.8% continuous zoom for the motion-dependency control. `B-motion-off` removes that zoom while preserving all states and timings. `DIM_OUTSIDE_REGION`, character presence and an AI-generated plan were deliberately not implemented because this sample does not need them.

The compiler produces `A-props.json`, `B-props.json`, `B-motion-off-props.json`, `VPS-001-experimental-edt-clips.json` and `diagnostics.json` in the isolated local output directory. Existing Remotion renders all three videos. No renderer swap or formal EDT/Director schema migration occurred.

The diagnostic `VISUAL_STATE_HOLD` here means the longest designed interval without a new visual state: A uses the existing beat boundaries; B uses the explicit state boundaries. It is a report metric, not a new Mechanical QA rule or a universal threshold.

The focused tests verify contract rejection, screenshot crop dimensions, ordinary EDT validation, A/B voice and duration preservation, subtitle text preservation, character removal from evidence visuals and a pure motion-off transform. The full suite passed **216 tests** with one pre-existing Starlette/httpx deprecation warning.
