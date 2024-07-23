import os
from mixedvar_PSO import PSO_param, PSO_optimizer


#################

'''INPUT PARAMETERS'''

input_ANSYS_params = {
    PSO_param('n_length', True, 6, 20),
    PSO_param('n_width', True, 6, 20)
}


'''BIG VARIABLES'''

f_system = GetSystem(Name="FFF")
f_sol_component = f_system.GetComponent(Name="Solution")


##################

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


# params is a set of PSO_param objects
def optimization_function(params):
    for param in params:
        set_ANSYS_param(param.name, param.value)

    f_sol_component.Update(AllDependencies=True)

    return get_ANSYS_param('max_k-op')


HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_ANSYS_params, optimization_function)
HUGE_NUCLEAR_OPTIMIZER.optimize(4, 0.8, 0.1, 0.1, 6)
