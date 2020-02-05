#idf_component_register(SRCS "mesh_light.c"
#        "mesh_main.c"
#        "ble_mesh_init.c"
#        INCLUDE_DIRS "." "include")

set(COMPONENT_SRCS "mesh_main.c"
        "ble_mesh_init.c"
        "mesh_light.c")

set(COMPONENT_ADD_INCLUDEDIRS ".")

register_component()