#idf_component_register(SRCS "mesh_main.c"
#                            "ble_mesh_init.c"
#                            "mesh_board.c"
#                    INCLUDE_DIRS "." "include")
set(COMPONENT_SRCS "mesh_main.c"
        "ble_mesh_demo_init.c"
        "mesh_board.c")

set(COMPONENT_ADD_INCLUDEDIRS ".")

register_component()
