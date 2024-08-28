import os
import time
from config import path


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
            return p.Value.Value # p.Value is a Quantity object, Value of Quantity object is float (I know, cringe, blame Ansys)


'''
for now filename is in same folder as everything
'''
def exec_container_cmd(container, filepath, language=None):
    container.Edit()

    f = open(filepath, 'r')
    cmd = f.read()

    if language:
        container.SendCommand(Language=language, Command=cmd)
    else:
        container.SendCommand(Command=cmd)

    container.Exit()


# see https://www.cfd-online.com/Forums/ansys-meshing/162493-model-information-incompatible-incoming-mesh.html
def run_ansys_update(params):
    f_system = GetSystem(Name='FFF')
    f_mesh_component = f_system.GetComponent(Name='Mesh')
    f_mesh_container = f_setup_component.GetContainer(ComponentName='Mesh')
    f_sol_component = f_system.GetComponent(Name='Solution')
    f_setup_component = f_system.GetComponent(Name='Setup')
    f_setup_container = f_system.GetContainer(ComponentName='Setup')

    for name, value in params.items():
        set_ANSYS_param(name, value)
    
    f_mesh_component.Refresh() # load geometry with new Ansys parameter values
    exec_container_cmd(f_mesh_container, path('mesh_script'), 'Python')
    
    f_setup_component.Reset()
    fluent_settings = f_setup_container.GetFluentLauncherSettings()
    fluent_settings.SetEntityProperties(Properties=Set(DisplayText='Fluent Launcher Settings', Precision='Double', EnvPath={}, RunParallel=True, NumberOfProcessorsMeshing=20, NumberOfProcessors=20, NumberOfGPGPUs=1))

    exec_container_cmd(f_setup_container, path('fluent_script'))
    # # remember to use backslashes to cancel any "special characters" in path (\n, \t etc.) I don't think r"" works here
    # f_setup_container.Edit()
    # f_setup_container.SendCommand(Command="/file/read-journal \"C:\Users\AeroDesigN\Desktop\\triumf_heatsink\plate_GUI_v1.jou\" ")
    # f_setup_container.Exit()

    f_sol_component.Update()
    
    result = get_ANSYS_param('heatsink_temp-op')
    return result


    
while not os.path.exists(path('optimization_result')):
    if os.path.exists(path('ansys_request')):
        with open(path('ansys_request'), 'r') as f:
            params = eval(f.read())
        os.remove(path('ansys_request'))
        
        result = run_ansys_update(params)
        
        with open(path('ansys_response'), 'w') as f:
            f.write(str(result))
    
    time.sleep(0.1)  # Small delay to prevent busy-waiting
