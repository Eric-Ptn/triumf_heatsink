# basic Particle Swarm Optimization algorithm that accomodates continuous and discrete parameter types
# wiki: https://en.wikipedia.org/wiki/Particle_swarm_optimization
# good intro: https://machinelearningmastery.com/a-gentle-introduction-to-particle-swarm-optimization/

import numpy as np
import datetime
import copy
import pickle
from scipy.stats import norm
import scipy.optimize as optimize
import numpy.linalg as LA
from config import path

# tiny helper function so cuteeee
def myround(x, base, prec=2):
    return np.round(base * np.round(float(x)/base), prec)


# parameter is just a container to hold its own information
# eq and hash are defined so that we can index into a dictionary containing past evaluations, if all the parameters are discrete
class PSO_param:
    def __init__(self, name, discrete, min_val, max_val, val=None, vel=None, discretization=None):
        self.name = name
        self.discrete = discrete # boolean
        self.min_val = min_val
        self.max_val = max_val
        self.val = val
        self.vel = vel
        self.discretization = discretization

        if not self.discretization and self.discrete:
            print(f'{self.name}: Using default discretization of 1')
            self.discretization = 1

    # I do NOT require that velocities be the same - I'm using the has for function evaluations, which only depends on position of parameter
    def __eq__(self, other):
        if not isinstance(other, PSO_param):
            return False

        return (self.name == other.name and
                self.discrete == other.discrete and
                self.min_val == other.min_val and
                self.max_val == other.max_val and
                self.val == other.val and
                self.discretization == other.discretization)
            
    # same as above for the hash
    def __hash__(self):
        return hash((self.name, self.discrete, self.min_val, self.max_val, self.val, self.discretization))

    def __repr__(self):
        return f'PSO_param({self.name}, {self.discrete}, {self.min_val}, {self.max_val}, {"{:.2f}".format(self.val)})'


# params and bparams are sets of PSO_param objects
class PSO_particle:
    def __init__(self, f, swarm):
        self.f = f
        self.bparams = None
        self.bval = float('inf')
        self.swarm = swarm

    # run this once when initializing all particles
    def set_motion(self, params):
        self.params = params
        return self.evaluate()

    # all new values discovered are automatically fed to the swarm
    def evaluate(self):
        recollection = self.swarm.swarm_memory(self.params)

        if recollection:
            val = recollection
        else:
            val = self.f(self.params)
            self.swarm.swarm_inform(self.params, val)

        if val < self.bval:         # recollection could be from other particles, so need to do this for both cases
            self.bval = val
            self.bparams = copy.deepcopy(self.params)

        return val

    def param_val(self, name):
        for param in self.params:
            if param.name == name:
                return param.val

        return None

    def bparam_val(self, name):
        for param in self.bparams:
            if param.name == name:
                return param.val

        return None


# bparams is set of PSO_param objects
class PSO_swarm:
    def __init__(self):
        self.bparams = None
        self.bval = float('inf')

    # call this once right after __init__ to add particle associations, needs to be outside of __init__ because objects defs would be circular that way
    # swarm would need particle objects for init but particle object needs swarm for init
    def add_particles(self, PSO_particles, all_params_discrete):
        self.particles = PSO_particles
        if all_params_discrete:
            self.param_val_dict = {}

    def swarm_inform(self, params, val):      
        # deepcopy() needed because otherwise ELEMENTS of frozenset() can be edited
        if hasattr(self, 'param_val_dict'):
            self.param_val_dict[frozenset(copy.deepcopy(params))] = val

    def swarm_memory(self, params):
        # I do not know why I need to use copy.deepcopy() to do indexing correctly and I do not care
        # need to use hasattr() and get() because no guarantees for either condition (don't want errors)
        if hasattr(self, 'param_val_dict') and self.param_val_dict.get(frozenset(copy.deepcopy(params))):
            return self.param_val_dict[frozenset(copy.deepcopy(params))]

        return None

    def bparam_val(self, name):
        for param in self.bparams:
            if param.name == name:
                return param.val

        return None
    
    def update_best_location(self):
        for particle in self.particles:
            if particle.bval < self.bval:
                self.bval = particle.bval
                self.bparams = copy.deepcopy(particle.bparams)


# params is a set of PSO_param objects
# position and velocity don't need to be defined for these PSO_param instances, 
# as they're just a template to define what TYPE of parameter the optimizer is dealing with, and initialize the particles that way
#
# f is the optimization function that receives a set of PSO_param objects and is minimized
class PSO_optimizer:
    def __init__(self, params, f, constraint_func=None):
        self.params = params
        self.f = f
        
        if constraint_func == None:
            self.constraint_func = lambda _ : True
        else:
            self.constraint_func = constraint_func

    # this function exists just to bring particles originally outside the allowed boundary back into the viable region
    # the region is not just defined by param min and max values, but also constraint_func of PSO_optimizer
    def clip_to_constraint(self, params):
        # do NOT use self.params as those are empty templates we don't want edited remember, use deepcopy
        temp_params = sorted(copy.deepcopy(params), key=lambda p: p.name)
        x0 = np.array([param.val for param in temp_params])

        def objective(x):
            return LA.norm(np.subtract(x, x0))  # Sum of squared distances from original point - find closest point to x0 that obeys constraint

        def constraint(x):
            # assign values being tested by scipy optimize to temp_params for constraint_func to evaluate
            for param, value in zip(temp_params, x):
                param.val = value

            # inequality of optimize.minimize() expects a number, not a bool - so tack on float()
            return float(self.constraint_func(set(temp_params)))

        bounds = [(param.min_val, param.max_val) for param in temp_params]

        result = optimize.minimize(
            objective,
            x0,
            method='SLSQP',
            constraints={'type': 'ineq', 'fun': constraint},
            bounds=bounds
        )

        if not result.success:
            print('Warning: Could not find a point satisfying the constraint')
            raise ValueError('Warning: Could not find a point satisfying the constraint')

        for param, value in zip(temp_params, result.x):
            param.val = value

        # result just optimized points to be as close to the original point as possible while obeying constraint,
        # but now every parameter holds a continuous value, including discrete parameters
        # 
        # need to snap the discrete parameters to a nearby legal point
        if next((x for x in temp_params if x.discrete == True), None):
            def generate_rounded_combinations(params, MU_MU_MU_MULTIPLIER):
                combinations = []
                for param in params:
                    if param.discrete:
                        # for discrete parameters, try snapping to every legal point in a square, range defined by MU_MU_MU_MULTIPLIER value
                        rounded_value = myround(param.val, param.discretization)
                        combinations.append([max(min(rounded_value + i * param.discretization, param.max_val), param.min_val) for i in range(-MU_MU_MU_MULTIPLIER, MU_MU_MU_MULTIPLIER + 1)])
                    else:
                        # don't change the continuous variables
                        combinations.append([param.val])

                all_combinations = np.array(np.meshgrid(*combinations)).T.reshape(-1, len(params))
                return all_combinations

            MU_MU_MU_MULTIPLIER = 0
            while True:
                rounded_combinations = generate_rounded_combinations(temp_params, MU_MU_MU_MULTIPLIER)
                # try every discrete parameter combination in the MU_MU_MU_MULTIPLIER range to see what works
                for rounded_vals in rounded_combinations:
                    if constraint(rounded_vals):
                        for param, value in zip(temp_params, rounded_vals):
                            param.val = value
                        return set(temp_params)
                
                MU_MU_MU_MULTIPLIER += 1

                if MU_MU_MU_MULTIPLIER > 50: # yeah 50 for now is too bad, magic number yeah so what
                    print('Warning: Could not find a point satisfying the constraint with discrete rounding')
                    raise ValueError('Warning: Could not find a point satisfying the constraint with discrete rounding')

        else:
            return set(temp_params)
    
    def initialize_particles(self, n_particles, logging, box_init):
        self.n_particles = n_particles
        self.swarm = PSO_swarm()
        self.swarm.add_particles([PSO_particle(self.f, self.swarm) for _ in range(n_particles)], all(param.discrete for param in self.params))

        if box_init:
            # make a grid of points
            # Calculate the number of points along each dimension
            points_per_dim = int(np.ceil(n_particles ** (1 / len(self.params))))

            grids = [np.linspace(0, 1, points_per_dim, endpoint=False) + 1 / (2 * points_per_dim) for _ in range(len(self.params))]
            grid = np.array(np.meshgrid(*grids)).T.reshape(-1, len(self.params))

            # If we have more points than needed, randomly select n_particles
            if len(grid) > n_particles:
                indices = np.random.choice(len(grid), n_particles, replace=False)
                grid = grid[indices]


            for i, particle in enumerate(self.swarm.particles):
                particle_params = set()

                for j, param in enumerate(self.params):
                    if param.discrete:
                        grid_pos = myround(grid[i, j] * (param.max_val - param.min_val) + param.min_val, param.discretization)
                    else:
                        grid_pos = grid[i, j] * (param.max_val - param.min_val) + param.min_val

                    vel = np.random.uniform(-1, 1) * (param.max_val - param.min_val) * 0.2 # found that this 0.2 scaling works nicely on initial vel, another day another magic number

                    particle_params.add(PSO_param(param.name, param.discrete, param.min_val, param.max_val, grid_pos, vel, param.discretization))

                particle_params = self.clip_to_constraint(particle_params)
                
                f_output = particle.set_motion(particle_params)

                if logging:
                    self.log_lines.append(f'Particle {i}, Output: {f_output}, {particle.params}, {datetime.datetime.now()}')
                    print(f'Particle {i}, Output: {f_output}, {particle.params}')

        else:
            # Initialize particles using random sampling within constraints
            constraints_satisfied = 0
            while constraints_satisfied < n_particles:
                particle_params = set()
                for param in self.params:
                    if param.discrete:
                        rand_val = np.random.uniform(param.min_val, param.max_val)
                        rand_val = myround(rand_val, param.discretization)
                    else:
                        rand_val = np.random.uniform(param.min_val, param.max_val)

                    vel = np.random.uniform(-1, 1) * (param.max_val - param.min_val) * 0.2 # found that this 0.2 scaling works nicely on initial vel, another day another magic number
                    particle_params.add(PSO_param(param.name, param.discrete, param.min_val, param.max_val, rand_val, vel, param.discretization))

                # Check if the constraints are satisfied
                if self.constraint_func(particle_params):
                    # Set particle parameters and add to swarm
                    f_output = self.swarm.particles[constraints_satisfied].set_motion(particle_params)

                    if logging:
                        self.log_lines.append(f'Particle {constraints_satisfied}, Output: {f_output}, {particle_params}, {datetime.datetime.now()}')
                        print(f'Particle {constraints_satisfied}, Output: {f_output}, {particle_params}')

                    constraints_satisfied += 1


    def update(self, w_inertia, c_cog, c_social, logging):
        for i, particle in enumerate(self.swarm.particles):
            for param in particle.params:
                r_cog, r_social = np.random.rand(2)

                param.vel = w_inertia * param.vel + c_cog * r_cog * (particle.bparam_val(param.name) - param.val) + c_social * r_social * (self.swarm.bparam_val(param.name) - param.val)
                new_val = param.val + param.vel

                # for discrete PSO parameters, create a Gaussian probability curve centered around "continuous" point to determine
                # where to jump next
                if param.discrete:
                    # scale = param.discretization means one grid point is one standard deviation
                    probabilities = norm.pdf(list(np.arange(param.min_val, param.max_val + param.discretization, param.discretization)), loc=new_val, scale=param.discretization)
                    probabilities /= np.sum(probabilities)
                    new_val = np.random.choice(list(np.arange(param.min_val, param.max_val + param.discretization, param.discretization)), p=probabilities)

                param.val = new_val

            particle.params = self.clip_to_constraint(particle.params)

            f_output = particle.evaluate()

            if logging:
                self.log_lines.append(f'Particle {i}, Output: {f_output}, {particle.params}, {datetime.datetime.now()}')
                print(f'Particle {i}, Output: {f_output}, {particle.params}')

        self.swarm.update_best_location()


    def optimize(self, n_particles, w_inertia, c_cog, c_social, range_count_thresh, convergence_range, max_iterations=200, logging=True, box_init=False):
        if logging:
            self.log_lines = []
            self.log_lines.append(f'PSO_optimizer initialized at {datetime.datetime.now()}')
        
        self.initialize_particles(n_particles, logging, box_init)
        
        self.swarm.update_best_location()

        if logging:
            self.log_lines.append(f'Iteration 0, best value: {self.swarm.bval}, {self.swarm.bparams}')

            print(f'Iteration 0, best value: {self.swarm.bval}, {self.swarm.bparams}')

            # clear pickle file
            with open(path('logging_pkl_write'), 'wb') as f:
                pickle.dump(self.swarm, f)

            with open(path('logging_txt_write'), 'w') as f:
                for line in self.log_lines:
                    f.write(line + '\n')


        iterations = 1
        within_range_count = 0

        # when all particles' bests are within the range of the swarm best for multiple iterations, solution is said to have converged
        # not just one iteration, because particles have a tendency to overshoot and swing by what it currently thinks is the best, which is good behaviour
        while within_range_count < range_count_thresh and iterations <= max_iterations:
            self.log_lines = [] # clear log lines every iteration
            self.update(w_inertia, c_cog, c_social, logging)

            if logging:
                self.log_lines.append(f'Iteration {iterations}, best value: {self.swarm.bval}, {self.swarm.bparams}')

                print(f'Iteration {iterations}, best value: {self.swarm.bval}, {self.swarm.bparams}')

                with open(path('logging_pkl_write'), 'ab') as f:
                    pickle.dump(self.swarm, f)

                with open(path('logging_txt_write'), 'a') as f:
                    for line in self.log_lines:
                        f.write(line + '\n')

            iterations += 1

            # check that all "particle bests" are within range of "swarm best"
            particle_dists = []
            for particle in self.swarm.particles:
                param_dists = []
                for param in particle.params:
                    param_dists.append(self.swarm.bparam_val(param.name) - particle.bparam_val(param.name))
                particle_dists.append(np.sqrt(sum(param_dist**2 for param_dist in param_dists)))

            if all(dist < convergence_range for dist in particle_dists):
                within_range_count += 1
            else:
                # reset consecutive count if some particle bests are out of range
                within_range_count = 0

        return self.swarm.bparams, self.swarm.bval
