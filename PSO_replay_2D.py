import os
import pickle
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# need this imports for the pickle apparently
from PSO_tests import test_objective1, test_objective2, test_objective3, test_objective4

log_path = os.path.dirname(os.path.realpath(__file__))
pickle_file = os.path.join(log_path, 'PSO_replay.pkl')

# Dictionary to store iteration-swarm pairs
iteration_swarm_map = {}
iteration = 0

with open(pickle_file, 'rb') as f:
    while True:
        try:
            swarm = pickle.load(f)
            iteration_swarm_map[iteration] = swarm
            iteration += 1
        except EOFError:
            break  # Reached the end of the file

# If you want to access a specific iteration's swarm:
# specific_swarm = iteration_swarm_map[desired_iteration_number]

### PLOT

fig, ax = plt.subplots()
particles, = ax.plot([], [], 'bo', markersize=6)
pbests, = ax.plot([], [], '+', color='orange', markersize=10)
sbests, = ax.plot([], [], 'rx', markersize=10)

iteration_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

def init():
    ax.set_xlim(-15, 15)
    ax.set_ylim(-15, 15)
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
anim.save('PSO_replay.mp4', fps=1)
anim.save('PSO_replay.gif', writer='pillow', fps=2)
