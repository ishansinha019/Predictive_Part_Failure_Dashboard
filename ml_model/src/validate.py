import pandera.pandas as pa


SERVICE_SCHEMA = pa.DataFrameSchema(
    {
        "service_id": pa.Column(int, unique=True),
        "machine_id": pa.Column(str, checks=pa.Check.str_matches(r"^\S+$")),
        "part_id": pa.Column(str, checks=pa.Check.str_matches(r"^\S+$")),
        "service_date": pa.Column(pa.DateTime),
        "time_in_service_days": pa.Column(int, checks=pa.Check.ge(0)),
        "service_type": pa.Column(
            str, checks=pa.Check.isin(["Routine Check", "Repair", "Replacement"])
        ),
        "part_failed": pa.Column(int, checks=pa.Check.isin([0, 1])),
    },
    strict=True,
    coerce=False,
)


def validate_dataset(data):
    return SERVICE_SCHEMA.validate(data, lazy=True)
