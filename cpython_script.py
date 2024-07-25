import os
import time
from mixedvar_PSO import PSO_param, PSO_optimizer

def optimization_function(params):
    param_dict = {param.name: float(param.val) for param in params}
    
    # Write params to a file for IronPython to read
    with open(r'C:\Users\AeroDesigN\ansys_request.txt', 'w') as f:
        f.write(str(param_dict))
    
    # Wait for ANSYS result
    while not os.path.exists(r'C:\Users\AeroDesigN\ansys_response.txt'):
        time.sleep(0.1)
    
    with open(r'C:\Users\AeroDesigN\ansys_response.txt', 'r') as f:
        result = float(f.read().strip())
    
    os.remove(r'C:\Users\AeroDesigN\ansys_response.txt')
    return result

input_ANSYS_params = {
    PSO_param('n_length', True, 6, 20),
    PSO_param('n_width', True, 6, 20)
}

HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_ANSYS_params, optimization_function)
result = HUGE_NUCLEAR_OPTIMIZER.optimize(4, 0.8, 0.1, 0.1, 5, 10000) # high convergence range for testing

with open(r'C:\Users\AeroDesigN\optimization_result.txt', 'w') as f:
    f.write(str(result))