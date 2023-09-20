import weave
from weave.panels import panel_board
from weave import ops_domain
from weave import weave_internal

import settings


def make_board(
    initial_entity_name: str, initial_project_name: str, predictions_stream_name: str
):
    varbar = panel_board.varbar()

    entity_name_val = varbar.add("entity_name_val", initial_entity_name, hidden=True)
    entity = ops_domain.entity(entity_name_val)
    entity_name = varbar.add(
        "entity_name",
        weave.panels.Dropdown(
            entity_name_val, choices=ops_domain.viewer().entities().name()
        ),
    )

    project_name_val = varbar.add("project_name_val", initial_project_name, hidden=True)
    project = ops_domain.project(entity_name_val, project_name_val)
    project_name = varbar.add(
        "project_name",
        weave.panels.Dropdown(project_name_val, choices=entity.projects().name()),
    )

    model_name_val = varbar.add("model_name_val", "PredictBasic", hidden=True)

    model_name = varbar.add(
        "model_name",
        weave.panels.Dropdown(
            model_name_val,
            choices=project.artifactType("PredictBasic").artifacts().name(),
        ),
    )

    model_version_val = varbar.add("model_version_val", "v0")

    model_artifact_version = varbar.add(
        "model_artifact_version",
        project.artifactVersion("PredictBasic", model_version_val),
    )

    # Unused for now.
    # dataset_ref = varbar.add('dataset_ref', weave.ops.ref(
    #     weave_internal.const('wandb-artifact:///')
    #     + entity_name_val + '/' + project_name_val + '/' + dataset_name_val + ':latest/obj'),
    #                     hidden=True)

    model_uri = varbar.add(
        "model_uri",
        weave_internal.const("wandb-artifact:///")
        + entity_name_val
        + "/"
        + project_name_val
        + "/"
        + model_name_val
        + ":"
        + model_version_val
        + "/obj",
        hidden=True,
    )

    model = varbar.add(
        "model",
        weave.ops.get(
            weave_internal.const("wandb-artifact:///")
            + entity_name_val
            + "/"
            + project_name_val
            + "/"
            + model_name_val
            + ":"
            + model_version_val
            + "/obj"
        ),
    )

    prediction_stream = varbar.add(
        "prediction_stream",
        weave.ops.get(
            weave_internal.const("wandb-artifact:///")
            + entity_name_val
            + "/"
            + project_name_val
            + "/"
            + predictions_stream_name
            + ":latest/obj"
        )
        .rows()
        .filter(lambda row: row["inputs.self"] == model_uri),
    )

    main = weave.panels.Group(
        layoutMode="grid",
        showExpressions=True,
        enableAddPanel=True,
    )

    main.add(
        "model",
        model,
        layout=weave.panels.GroupPanelLayout(x=0, y=0, w=12, h=12),
    )
    # main.add(
    #     "model code",
    #     model_artifact_version.file("obj.py"),
    #     layout=weave.panels.GroupPanelLayout(x=0, y=0, w=12, h=6),
    # )

    # TODO: make a function to get the evaluation run we want
    #     we should filter down to our eval op with particular arguments
    #     pinned. (write this API, will help on deciding about partials)
    main.add(
        "f1",
        model_artifact_version.usedBy()
        .filter(lambda run: run.state() == "finished")[-1]
        .summary()["summary.avg_f1"],
        layout=weave.panels.GroupPanelLayout(x=12, y=0, w=4, h=4),
    )

    main.add(
        "precision",
        model_artifact_version.usedBy()
        .filter(lambda run: run.state() == "finished")[-1]
        .summary()["summary.avg_precision"],
        layout=weave.panels.GroupPanelLayout(x=16, y=0, w=4, h=4),
    )

    main.add(
        "recall",
        model_artifact_version.usedBy()
        .filter(lambda run: run.state() == "finished")[-1]
        .summary()["summary.avg_recall"],
        layout=weave.panels.GroupPanelLayout(x=20, y=0, w=4, h=4),
    )

    main.add(
        "used_by_runs",
        weave.panels.Table(
            model_artifact_version.usedBy(),
            columns=[
                lambda run: run.id(),
                lambda run: run.state(),
                lambda run: run.loggedArtifactVersions().count(),
            ],
        ),
        layout=weave.panels.GroupPanelLayout(x=12, y=4, w=12, h=8),
    )

    main.add(
        "predictions",
        prediction_stream,
        layout=weave.panels.GroupPanelLayout(x=0, y=12, w=24, h=12),
    )

    # TODO: code to load a particular evaluation result
    #   yeah we really want to define this model as an object with a bunch of functions that
    #   produce its "slot" information.

    return weave.panels.Board(vars=varbar, panels=main)


if __name__ == "__main__":
    entity, project = settings.wandb_project.split("/")
    # board_ref = weave.storage.save(make_board(entity, project), f"{project}/models")
    board_ref = weave.storage.save(
        make_board(entity, project, settings.predictions_stream_name), "models_board"
    )
    print(board_ref)

    fetch_op = weave.ops.get(str(board_ref))
    fetch_op_s = str(fetch_op)

    # uri encode fetch_op_s, first import any modules we need
    import urllib.parse

    # then encode
    fetch_op_s = urllib.parse.quote(fetch_op_s)
    print(f"http://localhost:3000/?exp={fetch_op_s}")
