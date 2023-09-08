from __future__ import annotations
import argparse
import re
import typing
from typing_extensions import (
    NotRequired,
    TypedDict,
)

from arg_config import parser

parser.add_argument("--model_basic_name_up_to_period", action="store_true")
parser.add_argument("--model_basic_shares_skip_chars", type=int)



def split_paragraphs(doc):
    lines = [l.strip() for l in doc.split("\n")]
    stripped_doc = "\n".join(lines)
    return [p.strip() for p in stripped_doc.split("\n\n")]


def find_first_numeric(s: str) -> typing.Optional[int]:
    match = re.search(r"\d+", s)
    if match is None:
        return None
    return int(match.group().replace(",", ""))


class PredictBasicConfig(TypedDict):
    name_up_to_period: NotRequired[bool]
    shares_skip_chars: NotRequired[int]

# Model
class PredictBasic:
    @classmethod
    def from_args(cls, args) -> PredictBasic:
        # TODO: can get rid of this boilerplate
        predict_config = {}
        if args['model_basic_name_up_to_period']:
            predict_config["name_up_to_period"] = True
        if args['model_basic_shares_skip_chars']:
            predict_config["shares_skip_chars"] = args['model_basic_shares_skip_chars']
        return cls(predict_config)

    def __init__(self, config: PredictBasicConfig):
        self.config = config

    def predict(self, example: str) -> dict:
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

if __name__ == '__main__':
    import job_batch_predict

    job_batch_predict.main(PredictBasic)