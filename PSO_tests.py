# 3D tests can be seen here: https://www.geogebra.org/3d/czsdv6xm

from mixedvar_PSO import PSO_param, PSO_optimizer
import numpy as np

# solution is f(0,0) = 0
input_params1 = {
    PSO_param('x', True, -2, 2, discretization=0.05),
    PSO_param('y', True, -2, 2, discretization=0.15)
}

def test_objective1(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    x = get_param('plate_width').val
    y = get_param('n_plates').val
    return x**2 + y**2

def test_constraint1(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    x = get_param('x').val
    y = get_param('y').val
    return x + y > 3 and x + y < 8

def test_constraint2(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    x = get_param('x').val
    y = get_param('y').val
    return (x-3)**2 + (y-3)**2 < 2


# solution is f(3.182, 3.131) = ~-1.8
input_params2 = {
    PSO_param('x', True, 0, 5, discretization=0.1),
    PSO_param('y', True, 0, 5, discretization=0.1)
}

def test_objective2(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    x = get_param('x').val
    y = get_param('y').val
    return (x - 3.14)**2 + (y - 2.72)**2 + np.sin(3*x + 1.41) + np.sin(4*y - 1.73)


# 6D hartman function: https://www.sfu.ca/~ssurjano/hart6.html
# answer should be -3.32237 at (0.20169, 0.150011, 0.476874, 0.275332, 0.311652, 0.6573)

input_params3 = {
    PSO_param('a', False, 0, 1),
    PSO_param('b', False, 0, 1),
    PSO_param('c', False, 0, 1),
    PSO_param('d', False, 0, 1),
    PSO_param('e', False, 0, 1),
    PSO_param('f', False, 0, 1)
}

def test_objective3(params):

    # really weird matrix definitions (yes they are just hard decimal values)
    alpha = [1.0, 1.2, 3.0, 3.2]
    A = [[10, 3, 17, 3.50, 1.7, 8],
         [0.05, 10, 17, 0.1, 8, 14],
         [3, 3.5, 1.7, 10, 17, 8],
         [17, 8, 0.05, 10, 0.1, 14]]
    P = [[1312, 1696, 5569, 124, 8283, 5886],
        [2329, 4135, 8307, 3736, 1004, 9991],
        [2348, 1451, 3522, 2883, 3047, 6650],
        [4047, 8828, 8732, 5743, 1091, 381]]

    param_list = sorted(params, key=lambda x: x.name)

    for i in range(4):
      for j in range(6):
        P[i][j] = 1e-4 * P[i][j]

    f = 0

    for i in range(4):
      sum = 0
      for j in range(6):
        sum = sum - A[i][j] * (param_list[j].val - P[i][j]) ** 2

      f = f - alpha[i] * np.exp(sum)

    return f


# ackley function
input_params4 = {
    PSO_param('x', True, -15, 15, discretization=2),
    PSO_param('y', True, -15, 15, discretization=2)    
}

def test_objective4(params):

    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    x = get_param('plate_width').val
    y = get_param('n_plates').val

    first_exp = -20 * np.exp(-0.2 * np.sqrt(0.5 * (x**2 + y**2)))
    second_exp = -np.exp(0.5 * (np.cos(x) + np.cos(y)))

    return first_exp + second_exp + 20 + np.exp(1)

input_params5 = {
    PSO_param('plate_width', False, 0.5, 3),
    PSO_param('n_plates', True, 15, 60)    
}

def test_constraint3(params):
    def get_param(name):
        for param in params:
            if param.name == name:
                return param

        return None

    pw = get_param('plate_width').val
    n = get_param('n_plates').val
    return pw < 60.658446 / n

if __name__ == '__main__':
    HUGE_NUCLEAR_OPTIMIZER = PSO_optimizer(input_params2, test_objective2)
    HUGE_NUCLEAR_OPTIMIZER.optimize(n_particles=4, w_inertia=0.8, c_cog=0.1, c_social=0.1, range_count_thresh=5, convergence_range=0.2)
