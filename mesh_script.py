named_selection_list = Model.NamedSelections.GetChildren(DataModelObjectCategory.NamedSelection, True)

heatsink_ns = next((obj for obj in named_selection_list if obj.Name == "heatsink"), None)
fluid_ns = next((obj for obj in named_selection_list if obj.Name == "fluid"), None)
boi_ns = next((obj for obj in named_selection_list if obj.Name == "boi"), None)

# delete "Color" named selections that overlap with other named selections
color_ns_objs = [obj for obj in named_selection_list if "Color" in obj.Name]
for color_ns in color_ns_objs:
    color_ns.Delete()

mesh = Model.Mesh

mesh.ClearGeneratedData()

for meshcontrol in Model.Mesh.GetChildren(DataModelObjectCategory.MeshControl, True):
    meshcontrol.Delete()
    
mesh.ElementSize = Quantity(1e-3, "m")

fluid_sizing = mesh.AddSizing()
fluid_sizing.NamedSelection = fluid_ns
fluid_sizing.Type = SizingType.BodyOfInfluence
fluid_sizing.BodyOfInfluence = boi_ns
fluid_sizing.ElementSize = Quantity(3.5e-4, "m")

solid_sizing = mesh.AddSizing()
solid_sizing.NamedSelection = heatsink_ns
solid_sizing.ElementSize = Quantity(8e-4, "m")

geo = Model.Geometry
solid_part = next((obj for obj in geo.Children[0].Children if obj.Name == "solid"), None)
fluid_part = next((obj for obj in geo.Children[0].Children if obj.Name == "fluid"), None)

solid_part.GenerateMesh()
fluid_part.GenerateMesh()
Model.Connections.CreateAutomaticConnections()  # MUST GENERATE CONNECTIONS LIKE THIS, 
                                                # they don't appear on their own always and are necessary for heat transfer to occur between solid and fluid regions
mesh.Update() # must update mesh component even when meshing is done to load info into fluent
