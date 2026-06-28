# L4 calendar and observation-computation notes

Goal: improve date and calendar handling, and distinguish historical astronomical observation from modern computation.

This stage records uncertainty and comparison metadata. It does not need to implement a complete Chinese calendar conversion engine.

Scope:
- Continue after L1, L2, and L3 are complete.
- Do not change upstream ingest.
- Do not write Qdrant.
- Do not add a database.
- Do not build Web UI in this stage.
- Do not force complete calendar conversion.

Tasks:

1. Add DateNormalization model with:
- source_date_text
- calendar_system
- normalized_date_start
- normalized_date_end
- date_precision
- timezone
- location
- conversion_method
- conversion_status
- conversion_notes
- uncertainty_days
- alternative_dates
- source_refs

calendar_system enum:
- gregorian
- julian
- chinese_lunisolar
- unknown

conversion_method enum:
- manual
- library
- external_table
- unknown

conversion_status enum:
- exact
- approximate
- conflict
- unconverted
- unknown

2. alternative_dates entries should include:
- date_start
- date_end
- calendar_system
- source
- notes

3. Extend HistoricalEvent with date_normalization.

4. Support celestial research date fields:
- date_normalization
- observation_date_normalization
- computation_date_normalization

Keep backward compatibility with date_start, date_end, and date_precision.

5. Add CelestialObservation model:
- id
- celestial_event_id
- source_date_text
- date_normalization
- observer_location
- body
- event_type
- target_asterism
- original_text
- source_refs
- reliability
- notes

6. Add CelestialComputation model:
- id
- celestial_event_id
- computation_method
- ephemeris
- date_start
- date_end
- body
- event_type
- target_asterism
- angular_distance_deg
- duration_days
- visibility
- location
- thresholds_used
- computed_at
- notes

7. Add ObservationComputationComparison model:
- celestial_event_id
- observation_id
- computation_id
- delta_days
- angular_consistency
- date_consistency
- notes

angular_consistency enum:
- matched
- near_match
- conflict
- not_computed

date_consistency enum:
- matched
- near_match
- conflict
- unknown

8. Add CLI validate-calendar-data:
- validate date_normalization fields;
- check conflicts between legacy dates and normalized dates;
- date_precision=day without normalized_date_start is error;
- conversion_status=conflict requires conversion_notes;
- validate alternative_dates;
- output JSON summary.

9. Add CLI compare-observation-computation:
- input --celestial-event-id and --research-root;
- read observation records;
- read computation records;
- compare date difference;
- compare body, event_type, target_asterism;
- output JSON;
- save comparison to data/research/comparisons when possible.

First version can compare stored data only; it does not need to run Skyfield.

10. Update single and group reports with:
- date and calendar notes;
- observation and computation notes;
- limitations for uncertain date, pending conversion, or conflict.

11. Update case_index.json and group_index.json with:
- date_precision
- calendar_system
- conversion_status
- uncertainty_days
- astronomical_consistency
- observation_computation_delta_days

Tests:
- invalid calendar_system detected;
- date_precision=day without normalized date errors;
- conversion_status=conflict without notes warns or errors;
- compare-observation-computation generates comparison JSON;
- report contains date and calendar notes.

Acceptance commands:

```bash
cd apps/star-omen
pytest -q
python -m src.cli validate-calendar-data --research-root data/research
python -m src.cli compare-observation-computation --celestial-event-id mars_guarding_xin_001 --research-root data/research
python -m src.cli generate-case-report --correlation-id corr_mars_xin_leadership_change_001 --research-root data/research --rules-path data/processed/corpus/sample_rules.json --out-dir data/research/case_reports
```

Final report should include modified files, new models, new CLI commands, report sections, tests, acceptance results, and risks.
