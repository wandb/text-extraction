import weave
from weave.panels import panel_board
from weave import ops_domain
from weave import weave_internal

import settings

def make_board(initial_entity_name: str, initial_project_name: str):
    varbar = panel_board.varbar()

    entity_name_val = varbar.add('entity_name_val', initial_entity_name, hidden=True)
    entity = ops_domain.entity(entity_name_val)
    entity_name = varbar.add('entity_name',
                            weave.panels.Dropdown(entity_name_val,
                                                choices=ops_domain.viewer().entities().name()))

    project_name_val = varbar.add('project_name_val', initial_project_name, hidden=True)
    project = ops_domain.project(entity_name_val, project_name_val)
    project_name = varbar.add('project_name',
                            weave.panels.Dropdown(project_name_val,
                                                choices=entity.projects().name()))

    dataset_name_val = varbar.add('dataset_name_val', None, hidden=True)


    dataset_name = varbar.add('dataset_name',
                            weave.panels.Dropdown(dataset_name_val,
                                                choices=project.artifactType('Dataset').artifacts().name())) 

    # Unused for now.
    # dataset_ref = varbar.add('dataset_ref', weave.ops.ref(
    #     weave_internal.const('wandb-artifact:///')
    #     + entity_name_val + '/' + project_name_val + '/' + dataset_name_val + ':latest/obj'),
    #                     hidden=True)

    dataset = varbar.add('dataset', weave.ops.get(
        weave_internal.const('wandb-artifact:///')
        + entity_name_val + '/' + project_name_val + '/' + dataset_name_val + ':latest/obj'),
                        )

    main = weave.panels.Group(
            layoutMode="grid",
            showExpressions=True,
            enableAddPanel=True,
        )

    main.add(
        "table",
        weave.ops.obj_getattr(dataset, 'rows'),
        layout=weave.panels.GroupPanelLayout(x=0, y=0, w=24, h=16),
    )

    return weave.panels.Board(vars=varbar, panels=main)

if __name__ == '__main__':
    entity, project = settings.wandb_project.split("/")
    board_ref = weave.storage.publish(make_board(entity, project), f"{project}/datasets")
    print(board_ref)