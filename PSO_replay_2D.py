# IN ORDER TO WRITE VIDEO USING FFMPEG, YOU NEED TO INSTALL FFMPEG
# EITHER INSTALL IT, OR USE A DIFFERENT VIDEO WRITER
# install ffmpeg for windows, then add it to PATH and this code will be able to use it

import pickle
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from config import path

# need these imports for the pickle apparently
from cpython_script import optimization_function
from PSO_tests import test_objective1, test_objective2, test_objective3, test_objective4

pickle_file = path('logging_pkl_read')

# Dictionary to store iteration-swarm pairs
# swarm object contains everthing at its particular state - including particle and param data (which we read)
iteration_swarm_map = {}
iteration = 0

with open(pickle_file, 'rb') as f:
    while True:
        try:
            swarm = pickle.load(f)
            iteration_swarm_map[iteration] = swarm
            iteration += 1
        except EOFError:
            break

# If you want to access a specific iteration's swarm:
# specific_swarm = iteration_swarm_map[desired_iteration_number]

### PLOT

fig, ax = plt.subplots()
particles, = ax.plot([], [], 'bo', markersize=6)
pbests, = ax.plot([], [], '+', color='orange', markersize=10)
sbests, = ax.plot([], [], 'rx', markersize=10)

# # Add the geometric constraint curve x = 60.65846/y
# cy = np.linspace(15, 45, 1000)
# cx = (60.65846 - 0.5 * (cy - 1)) / cy
# curve, = ax.plot(cx, cy, 'g-', label='geometric constraint')

iteration_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

def init():
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    particles.set_data([], [])
    pbests.set_data([], [])
    sbests.set_data([], [])
    iteration_text.set_text('')
    return particles, pbests, sbests, iteration_text

def animate(i):

    x = [particle.param_val('x') for particle in iteration_swarm_map[i].particles]
    y = [particle.param_val('y') for particle in iteration_swarm_map[i].particles]
    particles.set_data(x, y)

    bx = [particle.bparam_val('x') for particle in iteration_swarm_map[i].particles]
    by = [particle.bparam_val('y') for particle in iteration_swarm_map[i].particles]
    pbests.set_data(bx, by)

    sbests.set_data([iteration_swarm_map[i].bparam_val('x')], [iteration_swarm_map[i].bparam_val('y')])

    iteration_text.set_text(f'Iteration {i}')
    return particles, iteration_text

anim = FuncAnimation(fig, animate, init_func=init, frames=len(iteration_swarm_map), interval=500, blit=True)
anim.save(path('vid_output'), fps=1)
anim.save(path('gif_output'), writer='pillow', fps=2)
