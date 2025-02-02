from sonyflake import SonyFlake

_id_generator = SonyFlake()


def generate_id() -> int:
    """
    This function generates a unique Snowflake ID.
    """
    if not _id_generator:
        raise RuntimeError("_id_generator is None")

    return _id_generator.next_id()
