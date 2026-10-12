# VPS-001 · Human-defined visual ground truth

## Source binding

- Source: CS-001 final EDT `ART-c537f9ba61ee4817`, render `RUN-dda8992671.mp4`.
- Master interval: **5.56–24.68 s** (19.12 s). Voice source range is exactly 5.56–24.68 s from `VOICE` `ART-7ef0a1a38f894364`; no resynthesis or stretching.
- Script `ART-278087e926034f3b`, segments `SEG-02`, `SEG-03`, `SEG-04`.
- Beats: `BEAT-02` (5.56–11.80), `BEAT-03` (11.80–17.44), `BEAT-04` (17.44–21.06), `BEAT-5a133712b419` (21.06–24.68). The last two beats share `SEG-04`.
- Evidence assets: research screenshot `MED-23b344b5d0c0` and script screenshot `MED-a380de2ef563`; both are exact CS-001 Workbench screenshots. The B version may reassign either already registered screenshot to an evidence beat; no new source imagery is introduced.
- All region coordinates below are normalized to the source screenshot (1600×1000); they are cropped deterministically, not regenerated. The introductory full-frame context state shows the whole screenshot. The evidence crop is enlarged until the relevant UI text becomes legible at 1080p.

State boundaries are manual semantic/phrase anchors because the source voice has measured segment boundaries but no word timestamps. The fixed boundaries do **not** claim word-accurate forced alignment.

## `BEAT-02` · Research intake, `SEG-02`

Narration: “研究页允许从本地文件导入资料，模型提取的原文候选需要操作者确认。” Evidence protagonist: the research Workbench UI. XIAO-Y absent.

| State | Master time | Operation and evidence region | Before viewer knows → After viewer sees | Why |
| --- | --- | --- | --- | --- |
| R1 | 5.56–6.56 | `FULL_FRAME_MEDIA`, research screenshot | No page context → sees the research Workbench | Establish where the action happens; intentionally short |
| R2 | 6.56–8.56 | `ZOOM_TO_REGION`, research crop `(0.14, 0.47, 0.45, 0.30)` | Knows the page → can read the local source import area | Make the actual UI legible |
| R3 | 8.56–11.80 | `HIGHLIGHT_RECT` over the same crop, import button/drop area; short label “候选需确认” | Sees intake control → understands import and model candidate are not automatic confirmation | Direct attention without claiming the screenshot depicts an already confirmed Fact |

## `BEAT-03` · Human verification, `SEG-03`

Narration: “候选引文不会自动成为已核实 Fact，这一步必须由人来把关。” Visual protagonist: a two-stage source status demonstration, not XIAO-Y.

| State | Master time | Operation | Before → After | Why |
| --- | --- | --- | --- | --- |
| H1 | 11.80–14.60 | `SHOW_TEXT`: “模型候选引文” over the enlarged research UI | Has seen import → sees candidate status | Name the unverified state |
| H2 | 14.60–17.44 | `SHOW_TEXT`: “人工确认后才是 Fact” over the same UI | Might conflate candidate and fact → sees the human gate | Explicitly change the information state rather than repeat the whole narration |

## `BEAT-04` · Fact/source binding, first half of `SEG-04`

Narration portion: “Fact Pack 把选中的事实与来源绑定……”. Visual protagonist: script Workbench UI, because this captured screen visibly states the script's Fact-ID requirement; it is **not** presented as a screenshot of a Fact Pack page. XIAO-Y absent.

| State | Master time | Operation and evidence region | Before → After | Why |
| --- | --- | --- | --- | --- |
| F1 | 17.44–18.54 | `FULL_FRAME_MEDIA`, script screenshot | Human verification is clear → sees the downstream script Workbench | Establish new page context |
| F2 | 18.54–21.06 | `ZOOM_TO_REGION`, script direction crop `(0.15, 0.35, 0.5625, 0.35)` | Sees page → can read the Fact-ID instruction area | Evidence-led narrowing, with no new visual claim about hidden Fact Pack internals |

## `BEAT-5a133712b419` · Script citation, second half of `SEG-04`

Narration portion: “……脚本里的事实性主张要引用已有 Fact ID。” Visual protagonist: the same enlarged script direction UI. XIAO-Y absent.

| State | Master time | Operation | Before → After | Why |
| --- | --- | --- | --- | --- |
| C1 | 21.06–22.66 | `HIGHLIGHT_RECT` around the Fact-ID requirement inside the enlarged script UI | Can read requirements → knows the exact line to notice | Point to the rule in the real UI |
| C2 | 22.66–24.68 | `CALLOUT_TEXT`: “事实主张 → 已有 Fact ID”, retaining the crop | Sees source rule → understands the required link | State the short conclusion, without reprinting the sentence |

Nine states across four existing beats; no extra beat or voice change. Target average hold is about 2.12 s and maximum hold is 3.24 s. The rectangles and crops are ground-truth design values to be inspected in rendered pixels and corrected in the experimental plan if they do not land on the visible controls. This plan is deliberately human-authored; Director automation is excluded until B demonstrates a clear creative gain.
