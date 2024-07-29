# basic Particle Swarm Optimization algorithm that accomodates continuous and discrete parameter types
# wiki: https://en.wikipedia.org/wiki/Particle_swarm_optimization
# good intro: https://machinelearningmastery.com/a-gentle-introduction-to-particle-swarm-optimization/

import numpy as np
import datetime
import os
import copy
import pickle
from scipy.stats import norm
import scipy.optimize as optimize

# tiny helper function so cuteeee
def myround(x, base, prec=2):
  return np.round(base * np.round(float(x)/base), prec)


# parameter is just a container to hold its own information
# eq and hash are defined so that we can index into a dictionary containing past evaluations, if necessary (untested)
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

    # I do NOT require that velocities be the same - because that's cringe
    # totally screws up the "discrete vals dictionary" functionality of swarm
    def __eq__(self, other):
        if not isinstance(other, PSO_param):
            return False

        return (self.name == other.name and
                self.discrete == other.discrete and
                self.min_val == other.min_val and
                self.max_val == other.max_val and
                self.val == other.val and
                self.discretization == other.discretization)
            
    # same as above for the hash holy fucking shit
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

    # call this once right after __init__ to add particle associations, needs to be outside of __init__ because objects defs would be circular that way...
    def add_particles(self, PSO_particles, all_params_discrete):
        self.particles = PSO_particles
        if all_params_discrete:
            self.param_val_dict = {}

    def swarm_inform(self, params, val):
        if val < self.bval:
            self.bval = val
            self.bparams = copy.deepcopy(params)
        
        # deepcopy() needed because otherwise ELEMENTS of frozenset() can be edited
        if hasattr(self, 'param_val_dict'):
            self.param_val_dict[frozenset(copy.deepcopy(params))] = val

    def swarm_memory(self, params):
        # I do not fucking know why I need to use copy.deepcopy() to do indexing correctly and I do not fucking care
        # need to use hasattr() and get() because no guarantees for either condition (don't want errors)
        if hasattr(self, 'param_val_dict') and self.param_val_dict.get(frozenset(copy.deepcopy(params))):
            return self.param_val_dict[frozenset(copy.deepcopy(params))]

        return None

    def bparam_val(self, name):
        for param in self.bparams:
            if param.name == name:
                return param.val

        return None


# params is a set of PSO_param objects
# position and velocity don't need to be defined for these PSO_param instances, as they're just a template to define
# the params for its particles
#
# f is the optimization function that receives a set of PSO_param objects and is minimized
class PSO_optimizer:
    def __init__(self, params, f, constraint_func=None):
        self.params = params
        self.f = f
        
        if constraint_func == None:
            self.constraint_func = lambda: True
        else:
            self.constraint_func = constraint_func
            
        self.log_lines = []
        self.log_lines.append(f'PSO_optimizer initialized at {datetime.datetime.now()}')

    def clip_to_constraint(self, params):
        # do NOT use self.params as those are empty templates remember
        temp_params = sorted(copy.deepcopy(params), key=lambda p: p.name)
        x0 = np.array([param.val for param in temp_params])

        def objective(x):
            return np.sum((x - x0)**2)  # Sum of squared distances from original point - find closest point to x0 given constraint

        def constraint(x):
            # assign values being tested by scipy optimize to temp_params for constraint_func to evaluate
            for param, value in zip(temp_params, x):
                param.val = value
            return self.constraint_func(set(temp_params))

        bounds = [(param.min_val, param.max_val) for param in temp_params]

        result = optimize.minimize(
            objective,
            x0,
            method='SLSQP',
            constraints={'type': 'ineq', 'fun': constraint},
            bounds=bounds
        )

        if not result.success:
            print("Warning: Could not find a point satisfying the constraint")
            raise ValueError("Warning: Could not find a point satisfying the constraint")

        for param, value in zip(temp_params, result.x):
            param.val = value

        # check for any discrete params
        if next((x for x in temp_params if x.discrete == True), None):
            # jank sol for discrete vars for now: for every discrete var, round to a few nearby points and try all combinations - if none work then L
            def generate_rounded_combinations(params):
                combinations = []
                for param in params:
                    if param.discrete:
                        rounded_value = myround(param.val, param.discretization)
                        combinations.append([rounded_value, rounded_value + param.discretization, rounded_value - param.discretization])
                    else:
                        combinations.append([param.val])
                return np.array(np.meshgrid(*combinations)).T.reshape(-1, len(params))

            rounded_combinations = generate_rounded_combinations(temp_params)

            for rounded_vals in rounded_combinations:
                if constraint(rounded_vals):
                    for param, value in zip(temp_params, rounded_vals):
                        param.val = value
                    break
            else:
                print("Warning: Could not find a point satisfying the constraint with discrete rounding")
                raise ValueError("Warning: Could not find a point satisfying the constraint with discrete rounding")

        return set(temp_params)

    
    def initialize_particles(self, n_particles, logging):
        self.n_particles = n_particles
        self.swarm = PSO_swarm()
        self.swarm.add_particles([PSO_particle(self.f, self.swarm) for _ in range(n_particles)], all(param.discrete for param in self.params))


        #### make a grid of points
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

                vel = np.random.uniform(-1, 1) * (param.max_val - param.min_val) * 0.2 # yeah yeah magic number mhm

                particle_params.add(PSO_param(param.name, param.discrete, param.min_val, param.max_val, grid_pos, vel))

            particle_params = self.clip_to_constraint(particle_params)
            
            f_output = particle.set_motion(particle_params)

            if logging:
                self.log_lines.append(f'Particle {i}, Output: {f_output}, {particle.params}, {datetime.datetime.now()}')
                print(f'Particle {i}, Output: {f_output}, {particle.params}')


    def update(self, w_inertia, c_cog, c_social, logging):
        for i, particle in enumerate(self.swarm.particles):
            for param in particle.params:
                r_cog, r_social = np.random.rand(2)

                param.vel = w_inertia * param.vel + c_cog * r_cog * (particle.bparam_val(param.name) - param.val) + c_social * r_social * (self.swarm.bparam_val(param.name) - param.val)
                new_val = param.val + param.vel

                # for discrete PSO parameters, create a Gaussian probability curve centered around "continuous" point to determine
                # where to jump next
                if param.discrete:
                    probabilities = norm.pdf(list(range(param.min_val, param.max_val + 1, param.discretization)), loc=new_val, scale=0.5) # scale = 1 means one grid point is one standard deviation
                    probabilities /= np.sum(probabilities)
                    new_val = np.random.choice(list(range(param.min_val, param.max_val + 1, param.discretization)), p=probabilities)

                # if new_val < param.min_val:
                #     new_val = param.min_val
                # elif new_val > param.max_val:
                #     new_val = param.max_val

                param.val = new_val

            particle.params = self.clip_to_constraint(particle.params)

            f_output = particle.evaluate()

            if logging:
                self.log_lines.append(f'Particle {i}, Output: {f_output}, {particle.params}, {datetime.datetime.now()}')
                print(f'Particle {i}, Output: {f_output}, {particle.params}')


    def optimize(self, n_particles, w_inertia, c_cog, c_social, range_count_thresh, convergence_range, max_iterations=200, logging=True):
        self.initialize_particles(n_particles, logging)
        if logging:
            log_path = os.path.dirname(os.path.realpath(__file__))
            self.log_lines.append(f'Iteration 0, best value: {self.swarm.bval}, {self.swarm.bparams}')

            print(f'Iteration 0, best value: {self.swarm.bval}, {self.swarm.bparams}')

            # clear pickle file
            with open(os.path.join(log_path, 'PSO_replay.pkl'), 'wb') as f:
                pickle.dump(self.swarm, f)

            with open(os.path.join(log_path, 'PSO_log.txt'), 'w') as f:
                for line in self.log_lines:
                    f.write(line + "\n")


        iterations = 1
        within_range_count = 0

        # at one iteration max_hist = min_hist which breaks it - which is why len(bval_hist) < hist_len is needed
        # use abs val convergence criteria, NOT percent because percent is finnicky (you could do percent of total range though)
        # when all particles' bests are within the range of the swarm best for multiple iterations, solution is said to have converged
        # not just one iteration, because particles have a tendency to overshoot and swing by what it currently thinks is the best, which is good behaviour
        while within_range_count < range_count_thresh and iterations <= max_iterations:
            self.log_lines = [] # clear log lines every iteration
            self.update(w_inertia, c_cog, c_social, logging)

            if logging:
                self.log_lines.append(f'Iteration {iterations}, best value: {self.swarm.bval}, {self.swarm.bparams}')

                print(f'Iteration {iterations}, best value: {self.swarm.bval}, {self.swarm.bparams}')

                with open(os.path.join(log_path, 'PSO_replay.pkl'), 'ab') as f:
                    pickle.dump(self.swarm, f)

                with open(os.path.join(log_path, 'PSO_log.txt'), "a") as f:
                    for line in self.log_lines:
                        f.write(line + "\n")

            iterations += 1

            # check that all "particle bests" are within range of "swarm best"
            particle_dists = []
            for particle in self.swarm.particles:
                param_dists = []
                for param in particle.params:
                    param_dists.append(self.swarm.bparam_val(param.name) - particle.bparam_val(param.name))
                particle_dists.append(np.sqrt(sum(param_dist**2 for param_dist in param_dists)))

            # somehow calc dist for all and compare
            if all(dist < convergence_range for dist in particle_dists):
                within_range_count += 1
            else:
                # reset if particles are out of range
                within_range_count = 0

        return self.swarm.bparams, self.swarm.bval