import os
import time


'''
display name as string
value as float
''' 
def set_ANSYS_param(display_name, value):
    dp = Parameters.GetFirstDesignPoint()

    value_str=str(value)

    for p in Parameters.GetAllParameters():
        if p.GetProperties()['DisplayText'] == display_name:
            dp.SetParameterExpression(
                Parameter=p,
                Expression=value_str)


def get_ANSYS_param(display_name):
    for p in Parameters.GetAllParameters():
        if p.GetProperties()['DisplayText'] == display_name:
            return p.Value.Value # p.Value is a Quantity object, Value of Quantity object is float (I know, cringe)


'''
for now filename is in same folder as everything
'''
def exec_container_cmd(container, filename):
    container.Edit()

    this_file_dir = os.path.dirname(os.path.realpath(__file__))
    f = open(os.path.join(this_file_dir, filename), "r")
    cmd = f.read()
    container.SendCommand(Command=cmd)

    container.Exit()


# see https://www.cfd-online.com/Forums/ansys-meshing/162493-model-information-incompatible-incoming-mesh.html
def run_ansys_update(params):
    for name, value in params.items():
        set_ANSYS_param(name, value)
    
    f_system = GetSystem(Name="FFF")
    f_mesh_component = f_system.GetComponent(Name="Mesh")
    f_sol_component = f_system.GetComponent(Name="Solution")
    f_setup_component = f_system.GetComponent(Name="Setup")
    f_setup_container = f_system.GetContainer(ComponentName="Setup")
    
    f_mesh_component.Update()
    
    f_setup_component.Reset()
    fluent_settings = f_setup_container.GetFluentLauncherSettings()
    fluent_settings.SetEntityProperties(Properties=Set(DisplayText="Fluent Launcher Settings", Precision="Double", EnvPath={}, RunParallel=True, NumberOfProcessorsMeshing=20, NumberOfProcessors=20, NumberOfGPGPUs=1))

    # exec_container_cmd(f_setup_container, "C:\Users\AeroDesigN\Desktop\\triumf_heatsink\plate_GUI_v1.jou")

    f_setup_container.Edit()
    # remember to use backslashes to cancel any "special characters" in path (\n, \t etc.) I don't think r"" works here
    f_setup_container.SendCommand(Command="/file/read-journal \"C:\Users\AeroDesigN\Desktop\\triumf_heatsink\plate_GUI_v1.jou\" ")
    f_setup_container.Exit()

    f_sol_component.Update()
    
    result = get_ANSYS_param('heatsink_temp-op')
    return result


    
while not os.path.exists('optimization_result.txt'):
    if os.path.exists('ansys_request.txt'):
        with open('ansys_request.txt', 'r') as f:
            params = eval(f.read())
        os.remove('ansys_request.txt')
        
        result = run_ansys_update(params)
        
        with open('ansys_response.txt', 'w') as f:
            f.write(str(result))
    
    time.sleep(0.1)  # Small delay to prevent busy-waiting
