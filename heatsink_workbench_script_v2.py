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

# PSO must act differently dependent on discrete or continuous parameter
# perhaps if discrete, PSO will "rubber band" to the nearest point that is not the current point
# if all the parameters in PSO are discrete, then PSO will keep track of the positions and values

class PSO_optimizer:
    def __init__(self, n_particles, w_inertia, c_cog, c_social, PSO_param_list, f):
        self.n_particles = n_particles
        self.w_inertia = w_inertia
        self.c_cog = c_cog
        self.c_social = c_social
        self.PSO_param_list = PSO_param_list
        self.f = f                                  # is there some way to extract number of arguments (parameters) f takes?

        self.pos_particles = []
        self.vel_particles = []
        self.bpos_particles = []
        self.bpos_swarm = ()

        self.bval_particles = []
        self.bval_swarm = float('inf')

        self.pos_dict = {}                          # maps positions to values to avoid repeated evaluations

        
        # TODO: need to initialize the positions and velocities

        self.initialize_particles()

    def initialize_particles(self):
        dim = len(self.PSO_param_list)
        pos_grid = np.linspace(0, 1, self.n_particles)
        
        for i in range(self.n_particles):
            pos = []
            vel = []
            for j, param in enumerate(self.PSO_param_list):
                if param.discrete:
                    grid_pos = int(np.round(pos_grid[i] * (param.max_val - param.min_val) + param.min_val))
                    pos.append(grid_pos)
                    vel.append(np.random.randint(-1, 2))
                else:
                    grid_pos = pos_grid[i] * (param.max_val - param.min_val) + param.min_val
                    pos.append(grid_pos)
                    vel.append(np.random.uniform(-1, 1))
            self.pos_particles.append(pos)
            self.vel_particles.append(vel)
            self.bpos_particles.append(pos)
            self.bval_particles.append(float('inf'))
        
        self.bpos_swarm = self.bpos_particles[0]


    def update(self):
        
        r_cog, r_social = np.random.rand(self.n_particles, 2) # wonder if this will work

        self.vel_particles = self.w_inertia * self.vel_particles + self.c_cog * r_cog * (self.bpos_particles - self.pos_particles) + self.c_social * r_social * ([self.bpos_swarm] * self.n_particles - self.pos_particles)
        self.pos_particles = self.pos_particles + self.vel_particles

        cur_val = self.f(self.pos_particles)

        for i in range(self.n_particles):
            if cur_val[i] < self.bval_particles[i]:
                self.bval_particles[i] = cur_val[i]
                self.bpos_particles[i] = self.pos_particles[i]

            if cur_val[i] < self.bval_swarm:
                self.bval_swarm = cur_val[i]
                self.bpos_swarm = self.pos_particles[i]

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
