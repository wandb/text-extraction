import typing
import weave


@weave.type()
class Dataset:
    rows: list[typing.Any]
