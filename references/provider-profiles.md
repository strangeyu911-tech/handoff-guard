# Provider profiles

The selector reads [provider-profiles.json](provider-profiles.json). This file is intentionally separate from code so a provider can update its catalog, aliases, tier mapping, or coarse cost class without rewriting the routing algorithm.

Each provider has:

```json
{
  "aliases": ["provider-name"],
  "models": [
    {"name": "model-visible-name", "aliases": ["legacy-name"], "tier": "budget", "cost_class": "low", "capabilities": ["coding"]}
  ]
}
```

Tier labels are routing roles, not benchmark rankings. The default WorkBuddy mappings are conservative, editable heuristics based on model naming/positioning. They deliberately do not contain the user's unresolved multiplier values. Add or remove a model by editing the JSON catalog; keep the schema stable.

The default Codex profile exposes `Luna` as the general tier and `Sol` as the strong tier. Legacy names remain accepted as model aliases. Model tier and reasoning effort are separate recommendations; both Luna and Sol use Medium effort by default in the regression policy.

Provider availability in a selector request can use canonical names or aliases. If a provider has no model for the requested tier, the selector uses the nearest configured tier and reports the fallback.
