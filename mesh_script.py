named_selection_list = Model.NamedSelections.GetChildren(DataModelObjectCategory.NamedSelection, True)

solid_ns = next((obj for obj in named_selection_list if obj.Name == "solid"), None)
fluid_heatsink_ns = next((obj for obj in named_selection_list if obj.Name == "fluid_heatsink"), None)

color_ns_list = [obj for obj in named_selection_list if "color" in obj.Name.lower()]
for color_ns in color_ns_list:
    color_ns.Delete()

mesh = Model.Mesh

mesh.ClearGeneratedData()

for meshcontrol in Model.Mesh.GetChildren(DataModelObjectCategory.MeshControl, True):
    meshcontrol.Delete()
    
mesh.ElementSize = Quantity(1e-3, "m")

fluid_sizing = mesh.AddSizing()
fluid_sizing.NamedSelection = fluid_heatsink_ns
fluid_sizing.ElementSize = Quantity(3.5e-4, "m")

solid_sizing = mesh.AddSizing()
solid_sizing.NamedSelection = solid_ns
solid_sizing.ElementSize = Quantity(8e-4, "m")

# mesh the solid parts

# Model.Connections.Children[0].Children
# Model.Connections.CreateAutomaticConnections()

# for connection in Model.Connections.Children[0].Children:
#     connection.Delete()

mesh.Update()
