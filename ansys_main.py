import os
import time
import random

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


def run_ansys_update():
    f_system = GetSystem(Name="FFF")
    f_geo_container = f_system.GetContainer(ComponentName="Geometry")
    f_geo_container.UpdateCAD()
    f_mesh_component = f_system.GetComponent(Name="Mesh")
    f_mesh_component.Update()
    # f_sol_component = f_system.GetComponent(Name="Solution")
    # f_sol_component.Update(AllDependencies=True)
    
    # result = get_ANSYS_param('heatsink_temp-op')
    # return result
    return random.randint(300, 500)


    
while not os.path.exists('optimization_result.txt'):
    if os.path.exists('ansys_request.txt'):
        with open('ansys_request.txt', 'r') as f:
            params = eval(f.read())
        os.remove('ansys_request.txt')
        
        result = run_ansys_update()
        
        with open('ansys_response.txt', 'w') as f:
            f.write(str(result))
    
    time.sleep(0.1)  # Small delay to prevent busy-waiting
