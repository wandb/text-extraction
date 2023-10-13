import weave
from weave.panels import panel_board
from weave import ops_domain

import settings
import cli

import op_evaluate


def make_board(eval_op_uri: str, initial_entity_name: str, initial_project_name: str):
    varbar = panel_board.varbar()

    dataset = weave.ops.get(
        f"wandb-artifact:///{settings.entity}/{settings.project}/dataset:latest/obj"
    )
    dataset_var = varbar.add("dataset", dataset)

    calls = weave.ops.get(
        f"wandb-artifact:///{settings.entity}/{settings.project}/stream:latest/obj"
    ).rows()

    op_calls = varbar.add(
        "op_calls", calls.filter(lambda row: row["name"] == eval_op_uri), hidden=True
    )

    op_call_ids = op_calls["span_id"]

    baseline_eval_id_val = varbar.add(
        "baseline_eval_id_val", op_call_ids[0], hidden=True
    )

    candidate_eval_id_val = varbar.add(
        "candidate_eval_id_val", op_call_ids[1], hidden=True
    )

    varbar.add(
        "baseline_eval_id",
        weave.panels.Dropdown(
            baseline_eval_id_val,
            choices=op_call_ids,
        ),
    )

    varbar.add(
        "candidate_eval_id",
        weave.panels.Dropdown(
            candidate_eval_id_val,
            choices=op_call_ids,
        ),
    )

    baseline_eval_run = varbar.add(
        "baseline_eval_run",
        op_calls.filter(lambda run: run["span_id"] == baseline_eval_id_val)[0],
        hidden=True,
    )

    candidate_eval_run = varbar.add(
        "candidate_eval_run",
        op_calls.filter(lambda run: run["span_id"] == candidate_eval_id_val)[0],
        hidden=True,
    )

    summary = varbar.add(
        "summary",
        weave.ops.make_list(
            a=weave.ops.TypedDict.merge(
                weave.ops.dict_(name="baseline"), baseline_eval_run["output"]["summary"]
            ),
            b=weave.ops.TypedDict.merge(
                weave.ops.dict_(name="candidate"),
                candidate_eval_run["output"]["summary"],
            ),
        ),
        hidden=True,
    )

    concatted_evals = varbar.add(
        "concatted_evals",
        weave.ops.List.concat(
            weave.ops.make_list(
                a=baseline_eval_run["output"]["eval_table"]
                .get()
                .map(
                    lambda row: weave.ops.TypedDict.merge(
                        weave.ops.dict_(name="baseline"), row
                    )
                ),
                b=candidate_eval_run["output"]["eval_table"]
                .get()
                .map(
                    lambda row: weave.ops.TypedDict.merge(
                        weave.ops.dict_(name="candidate"), row
                    )
                ),
            )
        ),
        hidden=True,
    )

    # join evals together first
    joined_evals = varbar.add(
        "joined_evals",
        weave.ops.join_all(
            weave.ops.make_list(
                a=baseline_eval_run["output"]["eval_table"].get(),
                b=candidate_eval_run["output"]["eval_table"].get(),
            ),
            lambda row: row["dataset_id"],
            False,
        ),
        hidden=True,
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
        hidden=True,
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

    return weave.panels.Board(vars=varbar, panels=main)


if __name__ == "__main__":
    op_def = op_evaluate.evaluate_multi_task_f1
    op_def_ref = weave.storage.publish(
        op_def,
        f"{settings.project}/{op_def.name}",
    )
    cli.publish(
        make_board(str(op_def_ref), settings.entity, settings.project),
        "model_compare",
    )
