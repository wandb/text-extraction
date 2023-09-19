import weave
from weave.panels import panel_board
from weave import ops_domain
from weave import weave_internal

import settings


def make_board(initial_entity_name: str, initial_project_name: str):
    varbar = panel_board.varbar()

    dataset = weave.ops.get(
        f"wandb-artifact:///{settings.entity}/{settings.project}/dataset:latest/obj"
    )
    dataset_var = varbar.add("dataset", dataset)

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

    baseline_model_name_val = varbar.add(
        "baseline_model_name_val", "PredictBasic", hidden=True
    )
    baseline_model_name = varbar.add(
        "baseline_model_name",
        weave.panels.Dropdown(
            baseline_model_name_val,
            choices=project.artifactType("PredictBasic").artifacts().name(),
        ),
    )
    baseline_model_version_val = varbar.add("baseline_model_version_val", "v0")
    baseline_model_artifact_version = varbar.add(
        "baseline_model_artifact_version",
        project.artifactVersion("PredictBasic", baseline_model_version_val),
    )

    baseline_eval_run = varbar.add(
        "baseline_eval_run",
        baseline_model_artifact_version.usedBy()
        .filter(lambda run: run.state() == "finished")
        .sort(lambda run: weave.ops.make_list(a=run.createdAt()), ["desc"])[0],
    )

    candidate_model_name_val = varbar.add(
        "candidate_model_name_val", "PredictBasic", hidden=True
    )
    candidate_model_name = varbar.add(
        "candidate_model_name",
        weave.panels.Dropdown(
            candidate_model_name_val,
            choices=project.artifactType("PredictBasic").artifacts().name(),
        ),
    )
    candidate_model_version_val = varbar.add("candidate_model_version_val", "v1")
    candidate_model_artifact_version = varbar.add(
        "candidate_model_artifact_version",
        project.artifactVersion("PredictBasic", candidate_model_version_val),
    )
    candidate_eval_run = varbar.add(
        "candidate_eval_run",
        candidate_model_artifact_version.usedBy()
        .filter(lambda run: run.state() == "finished")
        .sort(lambda run: weave.ops.make_list(a=run.createdAt()), ["desc"])[0],
    )

    summary = varbar.add(
        "summary",
        weave.ops.make_list(
            a=weave.ops.TypedDict.merge(
                weave.ops.dict_(name="baseline"), baseline_eval_run.summary()["summary"]
            ),
            b=weave.ops.TypedDict.merge(
                weave.ops.dict_(name="candidate"),
                candidate_eval_run.summary()["summary"],
            ),
        ),
    )
    concatted_evals = varbar.add(
        "concatted_evals",
        weave.ops.List.concat(
            weave.ops.make_list(
                a=baseline_eval_run.summary()["eval_table"].map(
                    lambda row: weave.ops.TypedDict.merge(
                        weave.ops.dict_(name="baseline"), row
                    )
                ),
                b=candidate_eval_run.summary()["eval_table"].map(
                    lambda row: weave.ops.TypedDict.merge(
                        weave.ops.dict_(name="candidate"), row
                    )
                ),
            )
        ),
    )

    # join evals together first
    joined_evals = varbar.add(
        "joined_evals",
        weave.ops.join_all(
            weave.ops.make_list(
                a=baseline_eval_run.summary()["eval_table"],
                b=candidate_eval_run.summary()["eval_table"],
            ),
            lambda row: row["dataset_id"],
            False,
        ),
    )

    # then join dataset to evals
    dataset_evals = varbar.add(
        "dataset_evals",
        weave.ops.join_2(
            dataset_var.rows,
            joined_evals,
            lambda row: row["id"],
            lambda row: row["dataset_id"][0],
            "dataset",
            "evals",
            False,
            False,
        ),
    )

    main = weave.panels.Group(
        layoutMode="grid",
        showExpressions=True,
        enableAddPanel=True,
    )
    main.add(
        "avg_f1",
        weave.panels.Plot(
            summary,
            x=lambda row: row["avg_f1"],
            y=lambda row: row["name"],
            color=lambda row: row["name"],
        ),
        layout=weave.panels.GroupPanelLayout(x=0, y=0, w=12, h=4),
    )
    main.add(
        "latency",
        weave.panels.Plot(
            concatted_evals,
            x=lambda row: row["latency"],
            y=lambda row: row["name"],
            color=lambda row: row["name"],
            mark="boxplot",
        ),
        layout=weave.panels.GroupPanelLayout(x=12, y=0, w=12, h=4),
    )

    main.add(
        "task_name_f1",
        weave.panels.Plot(
            summary,
            x=lambda row: row["task_name.f1"],
            y=lambda row: row["name"],
            color=lambda row: row["name"],
        ),
        layout=weave.panels.GroupPanelLayout(x=0, y=4, w=8, h=4),
    )
    main.add(
        "task_shares_f1",
        weave.panels.Plot(
            summary,
            x=lambda row: row["task_shares.f1"],
            y=lambda row: row["name"],
            color=lambda row: row["name"],
        ),
        layout=weave.panels.GroupPanelLayout(x=8, y=4, w=8, h=4),
    )
    main.add(
        "task_directors_f1",
        weave.panels.Plot(
            summary,
            x=lambda row: row["task_directors.f1"],
            y=lambda row: row["name"],
            color=lambda row: row["name"],
        ),
        layout=weave.panels.GroupPanelLayout(x=16, y=4, w=8, h=4),
    )

    facet_correct = weave.panels.Facet(
        dataset_evals,
        x=lambda row: row["evals.summary"][0]["correct"],
        x_title="baseline correct",
        y=lambda row: row["evals.summary"][1]["correct"],
        y_title="candidate correct",
        select=lambda row: row.count(),
    )

    correct_comparison = main.add(
        "correct_comparison",
        facet_correct,
        layout=weave.panels.GroupPanelLayout(x=0, y=8, w=12, h=6),
    )
    main.add(
        "help",
        weave.panels.PanelString(
            "Click a cell in in the panel to the left to load examples for that cell.\n\nClick a row number in the table below to see details for that row.",
            mode="markdown",
        ),
        layout=weave.panels.GroupPanelLayout(x=12, y=8, w=12, h=6),
    )
    sel_ex_table = weave.panels.Table(correct_comparison.selected())
    sel_ex_table.config.rowSize = 2
    sel_ex_table.add_column(lambda row: row["dataset.id"], "id")
    sel_ex_table.add_column(lambda row: row["dataset.example"], "example")
    sel_ex_table.add_column(lambda row: row["dataset.label.name"], "label.name")
    sel_ex_table.add_column(
        lambda row: weave.ops.dict_(
            baseline=row["evals.output"][0]["name"],
            candidate=row["evals.output"][1]["name"],
        ),
        "output",
    )
    sel_ex_table.add_column(lambda row: row["dataset.label.shares"], "label.shares")
    sel_ex_table.add_column(
        lambda row: weave.ops.dict_(
            baseline=row["evals.output"][0]["shares"].toString(),
            candidate=row["evals.output"][1]["shares"].toString(),
        ),
        "output",
    )
    sel_ex_table.add_column(
        lambda row: row["dataset.label.directors"], "label.directors"
    )
    sel_ex_table.add_column(
        lambda row: weave.ops.dict_(
            baseline=row["evals.output"][0]["directors"].toString(),
            candidate=row["evals.output"][1]["directors"].toString(),
        ),
        "output.directors",
    )
    sel_ex_table.add_column(
        lambda row: weave.ops.dict_(
            baseline=row["evals.latency"][0],
            candidate=row["evals.latency"][1],
        ),
        "latency",
    )

    selected_examples = main.add(
        "selected_examples",
        sel_ex_table,
        layout=weave.panels.GroupPanelLayout(x=0, y=14, w=24, h=12),
    )

    # TODO: code to load a particular evaluation result
    #   yeah we really want to define this model as an object with a bunch of functions that
    #   produce its "slot" information.

    return weave.panels.Board(vars=varbar, panels=main)


if __name__ == "__main__":
    entity, project = settings.wandb_project.split("/")
    # board_ref = weave.storage.save(make_board(entity, project), f"{project}/models")
    board_ref = weave.storage.save(make_board(entity, project), "model_compare_board")
    print(board_ref)

    fetch_op = weave.ops.get(str(board_ref))
    fetch_op_s = str(fetch_op)

    # uri encode fetch_op_s, first import any modules we need
    import urllib.parse

    # then encode
    fetch_op_s = urllib.parse.quote(fetch_op_s)
    print(f"http://localhost:3000/?exp={fetch_op_s}")
