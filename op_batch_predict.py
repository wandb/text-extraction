import weave
import typing
import cli
import base_types


@weave.op(input_type={"model": weave.types.ObjectType()})
def batch_predict(dataset: base_types.Dataset, model) -> typing.Any:
    predict_result = []
    print("DATASET", dataset)
    print("MODEL", model)

    for dataset_row in dataset.rows:
        result = weave.use(model.predict(dataset_row["example"]))
        predict_result.append(
            {
                "dataset_id": dataset_row["id"],
                "prediction": result,
            }
        )
    return {"prediction_table": predict_result}


def main():
    cli.weave_op_main(batch_predict)


if __name__ == "__main__":
    main()
