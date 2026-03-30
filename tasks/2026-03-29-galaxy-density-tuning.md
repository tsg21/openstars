# Galaxy density tuning

## Goal
Reduce average inter-planet gaps in generated galaxies so small maps feel meaningfully denser and less empty.

## Steps
- [x] Review the current generator and identify which parameter actually controls average spacing.
- [x] Tune galaxy generation so the average nearest-neighbour gap is about one third of the previous value while preserving deterministic placement and minimum separation.
- [x] Update PRD/task records and run backend tests plus lint/format verification.

## Status
✅ Complete

## Notes
- Lowering the minimum-separation floor had almost no effect on average spacing; the broad placement region was the main cause of sparse maps.
- The generator now places planets inside a central square covering roughly one sixth of the axis range, which brings the average nearest-neighbour gap down to about 35% of the previous value in small-galaxy samples.
