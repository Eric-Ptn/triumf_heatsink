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
    PSO_param('plate_width', False, 0.5, 3),
    PSO_param('n_plates', True, 15, 45)
}

def constraints(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    pw = get_param('plate_width').val
    n = get_param('n_plates').val
    return pw < (60.658446 - 0.5 * (n - 1)) / n # 0.5mm extra space

if __name__ == '__main__':
    HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_ANSYS_params, optimization_function, constraints)
    result = HUGE_NUCLEAR_OPTIMIZER.optimize(6, 0.8, 0.1, 0.1, 5, 5)

    with open(r'C:\Users\AeroDesigN\optimization_result.txt', 'w') as f:
        f.write(str(result))