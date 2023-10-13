import typing

import weave
import cli
import base_types


# TODO: optional
class PredictBasicConfig(typing.TypedDict):
    name_up_to_period: bool
    shares_skip_chars: int


class PredictBasicOutput(typing.TypedDict):
    name: str
    shares: int


# Model
@weave.type()
class PredictBasic(base_types.Model):
    config: PredictBasicConfig

    @weave.op()
    def predict(self, example: str) -> PredictBasicOutput:
        import re

        def split_paragraphs(doc):
            lines = [l.strip() for l in doc.split("\n")]
            stripped_doc = "\n".join(lines)
            return [p.strip() for p in stripped_doc.split("\n\n")]

        def find_first_numeric(s: str) -> typing.Optional[int]:
            match = re.search(r"\d+", s)
            if match is None:
                return None
            return int(match.group().replace(",", ""))

        config = self.config
        paragraphs = split_paragraphs(example)
        capital_paragraph = None
        name_paragraph = None
        for p in paragraphs:
            if "name" in p.lower():
                name_paragraph = p
            if "share" in p.lower():
                capital_paragraph = p
        result = {
            "name": None,
            "shares": None,
        }
        if capital_paragraph:
            paragraph_start = config.get("shares_skip_chars", 0)
            result["shares"] = find_first_numeric(capital_paragraph[paragraph_start:])
        if name_paragraph:
            match = re.search(r"is ", name_paragraph)
            if match is not None:
                result["name"] = name_paragraph[match.end() :]
            if result["name"] and config.get("name_up_to_period"):
                match = re.search(r"\.", result["name"])
                if match is not None:
                    result["name"] = result["name"][: match.start()]

        return result


if __name__ == "__main__":
    cli.weave_object_main(PredictBasic)
