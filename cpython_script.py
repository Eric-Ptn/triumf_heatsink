import os
import time
from mixedvar_PSO import PSO_param, PSO_optimizer
from config import path


input_ANSYS_params = {
    PSO_param('pin_width', True, 1, 5, discretization=0.25),
    PSO_param('n_width', True, 8, 40), 
    PSO_param('pin_height', True, 1, 5, discretization=0.25),
    PSO_param('n_length', True, 8, 40)
}


def optimization_function(params):
    param_dict = {param.name: float(param.val) for param in params}
    
    # Write params to a file for IronPython to read
    with open(path('ansys_request'), 'w') as f:
        f.write(str(param_dict))
    
    # Wait for ANSYS result
    while not os.path.exists(path('ansys_response')):
        time.sleep(0.1)
    
    with open(path('ansys_response'), 'r') as f:
        result = float(f.read().strip())
    
    os.remove(path('ansys_response'))
    return result


def input_constraint(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    pw = get_param('pin_width').val
    nw = get_param('n_width').val
    ph = get_param('pin_height').val
    nl = get_param('n_length').val

    clearance = 0.5 # 0.5mm extra space

    return pw < (60.65846 - clearance * (nw - 1)) / nw and ph < (58 - clearance * (nl - 1)) / nl 


if __name__ == '__main__':
    HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_ANSYS_params, optimization_function, input_constraint)
    result = HUGE_NUCLEAR_OPTIMIZER.optimize(n_particles=16, 
                                             w_inertia=0.8, 
                                             c_cog=0.1, 
                                             c_social=0.1, 
                                             range_count_thresh=5, 
                                             convergence_range=5,
                                             max_iterations=50)

    with open(path('optimization_result'), 'w') as f:
        f.write(str(result))