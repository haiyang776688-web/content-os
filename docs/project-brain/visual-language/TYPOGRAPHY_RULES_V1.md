# Typography Rules v1

Typography carries different information classes; it is not a second script.

| Class | Content | Default length | Source |
| --- | --- | ---: | --- |
| Subtitle | spoken words | timed phrase/cue | locked script + measured audio timing |
| Callout | local attention label | 1–4 Chinese words | Shot Plan semantic focus |
| Keyword | one conceptual emphasis | short phrase | approved script segment |
| Number | source-bound numeric emphasis | one number + minimal context | approved Fact/segment |
| Relation label | named connection | 1–3 terms | registered objects |
| UI text | evidence itself | unchanged pixels | evidence asset |

Default prohibited combination:

```text
full narration sentence
+ same sentence as headline
+ same sentence as subtitle
```

The compiler rejects a callout that duplicates the normalized subtitle text or exceeds the configured short-label boundary. Mechanical QA checks safe area, clipping and subtitle continuity. Semantic QA checks unsupported wording, narration duplication and whether decorative text competes with the primary evidence.

Renderer typography may apply a registered font, weight, marker, underline or contrast panel. It may not synthesize new copy or silently change capitalization, numbers, Fact IDs or UI text.
