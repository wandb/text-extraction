import argparse
import typing
import os

import weave
from weave import op_def
from weave import op_args
from weave import uris
from weave import artifact_local

import wandb
from wandb.sdk.artifacts.artifact import Artifact as WandbArtifact

import settings
import util


def validate_object_ref(ref: str) -> uris.WeaveURI:
    parsed_uri = uris.WeaveURI.parse(ref)
    get_node = weave.ops.get(str(parsed_uri))
    if get_node.type == weave.types.NoneType():
        raise argparse.ArgumentTypeError(f"Object {ref} does not exist")
    return parsed_uri


def add_arg_to_parser(
    prefix: str, arg_type: weave.types.Type, parser: argparse.ArgumentParser
):
    if isinstance(arg_type, weave.types.Boolean):
        parser.add_argument(f"--{prefix}", action="store_true", default=False)
    elif isinstance(arg_type, weave.types.Int):
        parser.add_argument(f"--{prefix}", type=int, required=True)
    elif isinstance(arg_type, weave.types.Float):
        parser.add_argument(f"--{prefix}", type=float, required=True)
    elif isinstance(arg_type, weave.types.String):
        parser.add_argument(f"--{prefix}", type=str, required=True)
    elif isinstance(arg_type, weave.types.TypedDict):
        for k, v in arg_type.property_types.items():
            add_arg_to_parser(f"{prefix}.{k}" if prefix else k, v, parser)
    elif weave.types.ObjectType().assign_type(arg_type):
        parser.add_argument(
            f"--{prefix}",
            type=validate_object_ref,
            required=True,
            help=f"URI of {arg_type.name}",
        )
    elif isinstance(arg_type, weave.types.List):
        parser.add_argument(
            f"--{prefix}", nargs="*", type=int, required=True
        )  # Assuming int for demonstration (TODO)
    elif weave.types.is_optional(arg_type):
        non_none_type = weave.types.split_none(arg_type)[1]
        add_arg_to_parser(prefix, non_none_type, parser)
        parser._actions[-1].required = False  # Make the last added argument optional
        parser._actions[
            -1
        ].default = None  # Default value is None for optional arguments
    # elif isinstance(arg_type, Union):
    #     choices = [type(t).__name__ for t in arg_type.types]
    #     parser.add_argument(f"--{prefix}", type=str, choices=choices)
    else:
        raise NotImplementedError(f"Type {arg_type} not supported")


def convert_to_value(parsed_args, type_def: weave.types.Type, prefix=""):
    if isinstance(type_def, weave.types.Boolean):
        return getattr(parsed_args, prefix)
    elif isinstance(type_def, weave.types.Int):
        return int(getattr(parsed_args, prefix))
    elif isinstance(type_def, weave.types.Float):
        return float(getattr(parsed_args, prefix))
    elif isinstance(type_def, weave.types.String):
        return str(getattr(parsed_args, prefix))
    elif isinstance(type_def, weave.types.TypedDict):
        obj = {}
        for k, v in type_def.property_types.items():
            nested_prefix = f"{prefix}.{k}" if prefix else k
            obj[k] = convert_to_value(parsed_args, v, nested_prefix)
        return obj
    elif weave.types.ObjectType().assign_type(type_def):
        return getattr(parsed_args, prefix)
        # return weave.ops.get(str(getattr(parsed_args, prefix)))
    elif isinstance(type_def, weave.types.List):
        return list(getattr(parsed_args, prefix))
    elif weave.types.is_optional(type_def):
        non_none_type = weave.types.split_none(type_def)[1]
        return (
            convert_to_value(parsed_args, non_none_type, prefix)
            if getattr(parsed_args, prefix) is not None
            else None
        )
    # elif isinstance(type_def, Union):
    #     value = getattr(parsed_args, prefix)
    #     for t in type_def.types:
    #         if isinstance(value, t):
    #             return convert_to_type(parsed_args, t, prefix)
    #     return value
    else:
        raise NotImplementedError(f"Type {type_def} not supported")


def weave_object_main(weave_obj_class):
    weave_type = typing.cast(weave.types.ObjectType, weave_obj_class.WeaveType())

    equiv_typed_dict = weave.types.TypedDict(weave_type.attr_types())
    parser = argparse.ArgumentParser(
        usage=f"Publishes a {weave_obj_class.__name__} Weave Object"
    )
    add_arg_to_parser("", equiv_typed_dict, parser)

    args = parser.parse_args()

    equiv_dict_val = convert_to_value(args, equiv_typed_dict)
    weave_obj = weave_obj_class(**equiv_dict_val)

    # TODO: need to control the W&B Artifact type and name in a nicer way.
    #   e.g. we want this type to be TextExtractionModel and name to be
    #   PredictBasic
    object_name = weave_obj_class.__name__
    if settings.wandb:
        ref = weave.storage.publish(weave_obj, f"{settings.project}/{object_name}")
    else:
        ref = weave.storage.save(weave_obj, f"{object_name}")
    print("REF", ref)
    # TODO: print nice UI link so we can see this object!


def weave_config_to_wandb_config(c: dict):
    config = {}
    for k, v in c.items():
        if isinstance(v, dict):
            config[k] = weave_config_to_wandb_config(v)
        elif isinstance(v, uris.WeaveURI):
            config[k] = util.weave_uri_to_wandb_uri_string(v)
        else:
            config[k] = v
    return config


def wandb_config_to_weave_config(c: dict):
    config = {}
    for k, v in c.items():
        if isinstance(v, dict):
            config[k] = wandb_config_to_weave_config(v)
        elif isinstance(v, WandbArtifact):
            config[k] = util.wandb_artifact_to_weave_uri(v)
        elif isinstance(v, str) and v.startswith("local-artifact://"):
            config[k] = uris.WeaveURI.parse(v)
        else:
            config[k] = v
    return config


def uris_to_get_nodes(c: dict):
    config = {}
    for k, v in c.items():
        if isinstance(v, dict):
            config[k] = wandb_config_to_weave_config(v)
        elif isinstance(v, uris.WeaveURI):
            config[k] = weave.ops.get(str(v))
        else:
            config[k] = v
    return config


def publish_local_artifacts(c: dict):
    config = {}
    for k, v in c.items():
        if isinstance(v, dict):
            config[k] = wandb_config_to_weave_config(v)
        elif isinstance(v, artifact_local.WeaveLocalArtifactURI):
            print("Publishing local artifact", v)
            # Inefficient, we read the object and then write it back
            obj = weave.storage.get(str(v))
            # TODO: the version / commit hash changes for some reason?
            published_ref = weave.storage.publish(obj, f"{settings.project}/{v.name}")
            print("Published to", str(published_ref))
            config[k] = uris.WeaveURI.parse(published_ref.uri)
        else:
            config[k] = v
    return config


def is_wandb_launch_mode():
    return bool(os.environ.get("WANDB_LAUNCH"))


def weave_op_main(weave_op: op_def.OpDef):
    input_type = weave_op.input_type
    if not isinstance(input_type, op_args.OpNamedArgs):
        raise NotImplementedError(
            "Only weave_op.input_type.named_args is supported for now"
        )
    weave_input_type = input_type.weave_type()
    parser = argparse.ArgumentParser(usage=f"Executes the {weave_op.name} Weave Op")
    add_arg_to_parser("", weave_input_type, parser)

    config_val = {}
    if not is_wandb_launch_mode():
        args = parser.parse_args()
        config_val = convert_to_value(args, weave_input_type)

    if settings.wandb:
        config_val = publish_local_artifacts(config_val)

        run_config = None
        if not is_wandb_launch_mode():
            run_config = weave_config_to_wandb_config(config_val)

        run = wandb.init(
            entity=settings.entity, project=settings.project, config=run_config
        )
        # If the config is passed in by launch, we need to process it differently.
        config_val = wandb_config_to_weave_config(run.config)

    config_val = uris_to_get_nodes(config_val)

    called = weave_op(**config_val)
    result = weave.use(called)

    if settings.wandb:
        if isinstance(result, dict):
            # TODO
            run.log(result)
        else:
            run.summary["result"] = result
