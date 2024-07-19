# basic Particle Swarm Optimization algorithm that accomodates continuous and discrete parameter types

import numpy as np
import collections
import datetime
import os 

# TODO: make some kind of log/plot capability so I can "replay" and debug an optimization.....
# step 1: make a log file
# step 2: read log file to make plot
# this way I can not only plot my practice cases but the Ansys cases too

# parameter is just a container to hold its own information
# eq and hash are defined so that we can index into a dictionary containing past evaluations, if necessary
class PSO_param:
    def __init__(self, name, discrete, min_val, max_val, val=None, vel=None):
        self.name = name
        self.discrete = discrete # boolean
        self.min_val = min_val
        self.max_val = max_val
        self.val = val
        self.vel = vel

    def __eq__(self, other):
        if not isinstance(other, PSO_param):
            return False
        return (self.name == other.name and
                self.discrete == other.discrete and
                self.min_val == other.min_val and
                self.max_val == other.max_val and
                self.val == other.val and
                self.vel == other.vel)

    def __hash__(self):
        return hash((self.name, self.discrete, self.min_val, self.max_val, self.val, self.vel))

# do I need to have a parameter for cur_val? (as in function output...)
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
        self.evaluate()

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
            self.bparams = self.params

        return val

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
    def add_particles(self, PSO_particles):
        self.particles = PSO_particles
        if all(pt.discrete for pt in self.particles):
            self.param_val_dict = {}

    def swarm_inform(self, params, val):
        if val < self.bval:
            self.bval = val
            self.bparams = params
        
        if self.param_val_dict:
            self.param_val_dict[frozenset(params)] = val

    def swarm_memory(self, params):
        if self.param_val_dict and self.param_val_dict[frozenset(params)]:
            return self.param_val_dict[frozenset(params)]
        
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
    def __init__(self, params, f):
        self.params = params
        self.f = f
        self.log_lines = []
        self.log_lines.append(f'PSO_optimizer initialized at {datetime.datetime.now()}')        

    def initialize_particles(self, n_particles):
        self.n_particles = n_particles
        self.swarm = PSO_swarm()
        self.swarm.add_particles([PSO_particle(self.f, self.swarm) for _ in range(n_particles)])
        
        pos_grid = np.linspace(0, 1, n_particles)   # used to scale the parameter range
        
        for i in range(n_particles):
            particle_params = set()
            
            # what happens with grid_pos stuff if the number of particles is weird (ex. 5), do you just "miss a corner"
            for param in self.params:
                if param.discrete:
                    grid_pos = np.round(pos_grid[i] * (param.max_val - param.min_val) + param.min_val)
                else:
                    grid_pos = pos_grid[i] * (param.max_val - param.min_val) + param.min_val

                # TODO: find appropriate vel expression
                # maybe a percentage of total parameter range? this would become an optimization parameter
                vel = np.random.uniform(-1, 1) # technically this doesn't scale well with unnormalized parameters.... but maybe I leave it for now

                particle_params.add(PSO_param(param.name, param.discrete, param.min_val, param.max_val, grid_pos, vel))

            self.swarm.particles[i].set_motion(particle_params)
        
    
    def update(self, w_inertia, c_cog, c_social, logging):
                
        # TODO: values from 0 to 1, appropriate?
        r_cog, r_social = np.random.rand(self.n_particles, 2) # wonder if this will work

        for i, particle in enumerate(self.swarm.particles):
            for param in particle.params:
                param.vel = w_inertia * param.vel + c_cog * r_cog * (particle.bparam_val(param.name) - param.val) + c_social * r_social * (self.swarm.bparam_val(param.name) - param.val)
                new_val = param.val + param.vel

                # for discrete PSO parameters, do continuous velocity as usual but round the output to discrete points
                if param.discrete:
                    new_val = np.round(new_val)
                
                # if particle hasn't moved, then pull it closer to random particle - random at beginning but less random near end - may implement later if needed
                # if new_val == param.val:
                    # implement pull rule... one grid distance closer to another random particle

                param.val = new_val

            f_output = particle.evaluate()

            if logging:
                values = ''
                for param in particle.params:
                    values += f'{param.name}: {param.val}, '

                self.log_lines.append(f'Particle {i}, Output: {f_output}, {values}{datetime.datetime.now()}')


    def optimize(self, n_particles, w_inertia, c_cog, c_social, hist_len, convergence_percent=5.0, max_iterations=200, logging=True):
        self.initialize_particles(n_particles)

        iterations = 0
        bval_hist = collections.deque(maxlen=hist_len)
        max_hist = max(bval_hist)
        min_hist = min(bval_hist)

        while (not max_hist - min_hist <= convergence_percent / 100.0 * min_hist) and iterations < max_iterations:
            self.update(n_particles, w_inertia, c_cog, c_social, logging)

            iterations += 1
            bval_hist.append(self.swarm.bval)
            max_hist = max(bval_hist)
            min_hist = min(bval_hist)

        if logging:
            log_path = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(log_path, 'PSO_log.txt'), "a") as f:
                for line in self.log_lines:
                    f.write(line + "\n")

        return self.swarm.bparams, self.swarm.bval