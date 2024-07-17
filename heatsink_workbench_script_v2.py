import random
import os
import datetime
import numpy as np


class PSO_param:
    def __init__(self, name, discrete, min_val, max_val):
        self.name = name
        self.discrete = discrete # boolean
        self.min_val = min_val
        self.max_val = max_val
        self.val = None


class PSO_particle:
    def __init__(self, f, swarm):
        self.f = f
        self.bval = float('inf')
        self.bpos = None
        self.swarm = swarm

    def set_motion(self, pos, vel):
        self.pos = pos
        self.vel = vel
        self.evaluate()

    def evaluate(self):

        recollection = self.swarm.swarm_memory(self.pos)
        
        if recollection:
            val = recollection
        else:
            val = self.f(self.pos)
            self.swarm.swarm_inform(self.pos, val)

        if val < self.bval:         # recollection could be from other particles, so need to do this for both cases
            self.bval = val
            self.bpos = self.pos

        return val        
    

class PSO_swarm:
    def __init__(self):
        self.bval = float('inf')
        self.bpos = None

    def add_particles(self, PSO_particles):         # needs to be outside of __init__ because it would be circular that way...
        self.particles = PSO_particles
        if all(pt.discrete for pt in self.particles):
            self.pos_val_dict = {}

    def swarm_inform(self, pos, val):
        if val < self.bval:
            self.bval = val
            self.bpos = pos
        
        if self.pos_val_dict:
            self.pos_val_dict[pos] = val

    def swarm_memory(self, pos):
        if self.pos_val_dict and self.pos_val_dict[pos]:
            return self.pos_val_dict[pos]
        
        return None

# for discrete PSO parameters, do continuous velocity as usual but round the output to discrete points
# if the output does not change the current point, move one step closer to a random particle??
# idea is that at converged solution the "move one step to random particle" doesn't actually result in anything

class PSO_optimizer:
    def __init__(self, PSO_param_list, f):
        self.PSO_param_list = PSO_param_list
        self.f = f        

    def initialize_particles(self, n_particles):

        self.swarm = PSO_swarm()
        self.swarm.add_particles([PSO_particle(self.f, self.swarm) for _ in range(n_particles)])

        # TODO: need to fix this up
        
        pos_grid = np.linspace(0, 1, n_particles)   # used to normalize the parameter range
        
        for i in range(n_particles):
            pos = []                                # each particle position and velocity is contained in an array
            vel = []
            for p in self.PSO_param_list:
                if p.discrete:
                    grid_pos = np.round(pos_grid[i] * (p.max_val - p.min_val) + p.min_val)
                else:
                    grid_pos = pos_grid[i] * (p.max_val - p.min_val) + p.min_val

                pos.append(grid_pos)
                vel.append(np.random.uniform(-1, 1)) # technically this doesn't scale well with unnormalized parameters.... but maybe I leave it for now

            self.pos_particles.append(pos)
            self.vel_particles.append(vel)
            self.bpos_particles.append(pos)
            self.bval_particles.append(self.f(self.PSO_param_list))
        
        self.bpos_swarm = self.pos_particles[self.bval_particles.index(max(self.bval_particles))]

    
    def update(self, n_particles, w_inertia, c_cog, c_social):
        
        # make the loop explicit through each parameter... this is way too confusing even if it's marginally more compact/efficient
        
        r_cog, r_social = np.random.rand(self.n_particles, 2) # wonder if this will work

        for p in self.PSO_param_list:

        self.vel_particles = w_inertia * self.vel_particles + c_cog * r_cog * (self.bpos_particles - self.pos_particles) + c_social * r_social * ([self.bpos_swarm] * n_particles - self.pos_particles)
        self.pos_particles = self.pos_particles + self.vel_particles

        cur_val = self.f(self.pos_particles)

        for i in range(self.n_particles):
            if cur_val[i] < self.bval_particles[i]:
                self.bval_particles[i] = cur_val[i]
                self.bpos_particles[i] = self.pos_particles[i]

            if cur_val[i] < self.bval_swarm:
                self.bval_swarm = cur_val[i]
                self.bpos_swarm = self.pos_particles[i]



    def optimize(self, n_particles, w_inertia, c_cog, c_social):
        self.initialize_particles(n_particles)

        while True:
            self.update(n_particles, w_inertia, c_cog, c_social)

#################

'''INPUT PARAMETERS'''

param_list = [
    PSO_param('n_length', True, 6, 20),
    PSO_param('n_width', True, 6, 20)
]


'''BIG VARIABLES'''

f_system = GetSystem(Name="FFF")
f_sol_component = f_system.GetComponent(Name="Solution")


##################

'''
display name as string
value as float
''' 
def change_parameter_val(display_name, value):
    dp = Parameters.GetFirstDesignPoint()

    value_str=str(value)

    for p in Parameters.GetAllParameters():
        if p.GetProperties()['DisplayText'] == display_name:
            dp.SetParameterExpression(
                Parameter=p,
                Expression=value_str)


def get_parameter_val(display_name):
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


def debug_print(message):
    with open(r"C:\Users\AeroDesigN\Desktop\triumf_heatsink\heatsink_debug_log.txt", "a") as f:   # TODO: get file path automatically using os or set as param
        f.write(str(message) + "\n")


debug_print('starting...')
debug_print(datetime.datetime.now())
debug_print('\n')

for i in range(3):
    
    new_param_vals = {}

    for i, p in enumerate(param_list):
        random_val = random.randint(p.min_val, p.max_val)
        change_parameter_val(p.name, random_val)
        new_param_vals[i] = random_val

    f_sol_component.Update(AllDependencies=True)

    debug_print(datetime.datetime.now())
    debug_print(new_param_vals)
    debug_print(get_parameter_val("max_k-op"))
    debug_print('\n')
