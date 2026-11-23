# Part failure model v2.0

The training command produces a model card with dataset hash, chronological
split dates, sample counts, and held-out metrics in `ml_model/outputs/v2.0/`.
This model is an experimental demonstration trained on synthetic service
records, not a basis for maintenance or safety decisions.

The input features are machine ID, part ID, and time in service. Service type
is excluded: in the supplied dataset it perfectly identifies the outcome and
is not available as a meaningful pre-failure feature. Unseen IDs are accepted.
Chronological evaluation reduces future-data leakage but does not establish
real-world accuracy, calibration, or fairness. In the supplied data,
non-failures occur at 100–359 days and failures at 450–742 days; this
synthetic separation can make test scores appear unrealistically strong.
