# CURRENT_RULES

## DIAGNOSTIC_REAUDIT · HIGH

Every repaired script revision requires a fresh independent audit.

Scope: SCRIPT  
Owner: AUDIT  
Reason: Mock diagnostic failure path  
Related error: ERR-30e5818b36

## WRITING_RULE_SET · v1

```json
{
  "set_id": "WRITING_V1",
  "version": "1",
  "rules": [
    {
      "rule_id": "NO_FABRICATION",
      "name": "Claim discipline",
      "scope": "SCRIPT",
      "priority": 50,
      "severity": "BLOCKER",
      "hard_or_soft": "HARD",
      "applies_to": [
        "SCRIPT_PRIMARY",
        "SCRIPT_EDITOR",
        "AUDIT"
      ],
      "text": "Never fabricate facts, sources or numbers. Preserve source-bound claims.",
      "examples": [],
      "exceptions": [],
      "version": "1",
      "source": "SYSTEM"
    },
    {
      "rule_id": "OWNER_ONLY",
      "name": "Single writer",
      "scope": "ALL",
      "priority": 50,
      "severity": "BLOCKER",
      "hard_or_soft": "HARD",
      "applies_to": [],
      "text": "Downstream submits a change request; never edits upstream.",
      "examples": [],
      "exceptions": [],
      "version": "1",
      "source": "SYSTEM"
    },
    {
      "rule_id": "CREATIVE_POLICY",
      "name": "Creative policy",
      "scope": "ALL",
      "priority": 50,
      "severity": "BLOCKER",
      "hard_or_soft": "HARD",
      "applies_to": [],
      "text": "Human creative policy outranks optimization metrics.",
      "examples": [],
      "exceptions": [],
      "version": "1",
      "source": "SYSTEM"
    },
    {
      "rule_id": "ORAL_CLARITY",
      "name": "Spoken clarity",
      "scope": "SCRIPT",
      "priority": 50,
      "severity": "WARNING",
      "hard_or_soft": "SOFT",
      "applies_to": [],
      "text": "Use concise spoken clauses; explain jargon; remove empty repetition.",
      "examples": [],
      "exceptions": [],
      "version": "1",
      "source": "SYSTEM"
    }
  ]
}
```

## HOOK_RULE_SET · v1

```json
{
  "hook_type": "DIRECT_VALUE",
  "max_duration": 8.0,
  "max_sentence_count": 2,
  "information_gap": "",
  "specificity": "Specific and source-bound",
  "promise": "Deliver in this script",
  "forbidden_patterns": [
    "FABRICATED_NUMBER",
    "UNSUPPORTED_PROMISE"
  ]
}
```

## RETENTION_RULE_SET · v1

```json
{
  "version": "1",
  "information_change": "Change when meaning changes",
  "open_loop": "Only when there is a payoff",
  "payoff": "Close the promise",
  "visual_refresh": "Follow semantic beats",
  "density_change": "Primary before supporting details",
  "question_answer": "Bind questions to answers",
  "pattern_interrupt": "Purposeful only",
  "section_transition": "Narrative function"
}
```

## EDITORIAL_VOICE · v1

```json
{
  "profile_id": "COMPANION_V1",
  "version": "1",
  "tone": "Clear, rational, approachable",
  "formality": "Conversational",
  "sentence_length": "Short spoken clauses",
  "humor": "Restrained",
  "technical_density": "Explain necessary jargon",
  "directness": "Direct",
  "slang": "Limited",
  "emoji_policy": "None in spoken script",
  "rhetorical_question_frequency": "Low",
  "first_person_style": "Companion",
  "forbidden_expressions": []
}
```
