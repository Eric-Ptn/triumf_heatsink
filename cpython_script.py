import os
import time
from mixedvar_PSO import PSO_param, PSO_optimizer

def optimization_function(params):
    param_dict = {param.name: param.val for param in params}
    
    # Write params to a file for IronPython to read
    with open('ansys_request.txt', 'w') as f:
        f.write(str(param_dict))
    
    # Wait for ANSYS result
    while not os.path.exists('ansys_response.txt'):
        time.sleep(0.1)
    
    with open('ansys_response.txt', 'r') as f:
        result = float(f.read().strip())
    
    os.remove('ansys_response.txt')
    return result

input_ANSYS_params = {
    PSO_param('n_length', True, 6, 20),
    PSO_param('n_width', True, 6, 20)
}

HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_ANSYS_params, optimization_function)
result = HUGE_NUCLEAR_OPTIMIZER.optimize(4, 0.8, 0.1, 0.1, 5, 10000)

with open('optimization_result.txt', 'w') as f:
    f.write(str(result))