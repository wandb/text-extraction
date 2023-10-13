import subprocess

import weave
from weave import monitoring

import publish_dataset

import board_model_compare2

import op_evaluate

import model_basic

import settings


def main():
    dataset_ref = weave.storage.publish(
        publish_dataset.read_dataset(), f"{settings.project}/dataset"
    )
    dataset = weave.storage.get(dataset_ref)
    print("published dataset")

    model_a_ref = weave.storage.publish(
        model_basic.PredictBasic({"shares_skip_chars": 0, "name_up_to_period": False}),
        f"{settings.project}/PredictBasic",
    )

    # Make some predictions to ensure we have some in the prediction
    # StreamTable
    monitoring.init_monitor(
        f"{settings.entity}/{settings.project}/{settings.predictions_stream_name}"
    )
    model_a = weave.storage.get(model_a_ref)
    weave.use(model_a.predict("hello"))
    weave.use(model_a.predict("my name is jim"))

    print("published model a")
    weave.use(op_evaluate.evaluate_multi_task_f1(dataset, model_a))
    print("evaluated model a")

    model_b_ref = weave.storage.publish(
        model_basic.PredictBasic({"shares_skip_chars": 5, "name_up_to_period": False}),
        f"{settings.project}/PredictBasic",
    )

    # Make predictions
    model_b = weave.storage.get(model_b_ref)
    weave.use(model_b.predict("my name is bob"))

    print("published model b")
    weave.use(op_evaluate.evaluate_multi_task_f1(dataset, model_b))
    print("evaluated model b")

    # model_c = weave.publish(
    #     model_basic({"shares_skip_chars": 5, "name_up_to_period": True}), "ModelBasic"
    # )
    # cli.run_op(op_evaluate.evaluate_multi_task_f1(dataset, model_c))

    # Annoying, need to deinit_monitor so we don't trace ops called during board creation
    # TODO: fix
    monitoring.deinit_monitor()

    # Need to publish the op_def so we can pass it to make_board for now.
    # TODO: fix
    op_def = op_evaluate.evaluate_multi_task_f1
    op_def_ref = weave.storage.publish(
        op_def,
        f"{settings.project}/{op_def.name}",
    )

    weave.publish(
        board_model_compare2.make_board(
            str(op_def_ref), settings.entity, settings.project
        ),
        f"{settings.project}/model_compare",
    )
    print("published model compare board")


if __name__ == "__main__":
    main()
