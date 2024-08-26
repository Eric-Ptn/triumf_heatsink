import os
import time
from mixedvar_PSO import PSO_param, PSO_optimizer
from sw_hacking import update_sw

def optimization_function(params):
    param_dict = {param.name: float(param.val) for param in params}
    
    update_sw(r"C:\Users\ericp\OneDrive\Desktop\plate_heatsink.SLDPRT", r"C:\Users\ericp\OneDrive\Desktop\equations.txt", param_dict)
    
    # Write params to a file for IronPython to read
    with open(r'C:\Users\ericp\ansys_request.txt', 'w') as f:
        f.write(str(param_dict))
    
    # Wait for ANSYS result
    while not os.path.exists(r'C:\Users\ericp\ansys_response.txt'):
        time.sleep(0.1)
    
    with open(r'C:\Users\ericp\ansys_response.txt', 'r') as f:
        result = float(f.read().strip())
    
    os.remove(r'C:\Users\ericp\ansys_response.txt')
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
    return pw < (60.65846 - 0.5 * (n - 1)) / n # 0.5mm extra space

if __name__ == '__main__':
    HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_ANSYS_params, optimization_function, constraints)
    result = HUGE_NUCLEAR_OPTIMIZER.optimize(1, 0.8, 0.1, 0.1, 5, 5, max_iterations=1)

    with open(r'C:\Users\ericp\optimization_result.txt', 'w') as f:
        f.write(str(result))