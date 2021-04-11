import sys
from modules.agent_manager import AgentManager
from multiprocessing import Process, shared_memory, Manager
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
import json


TEAM_SIZE = "--team-size"
TEAM_ID = "--team-name"
AGENT_ID = "--agent-id"
AGENT_IDS = "--agent-ids"
CONFIG = "--config-file"


def debugger(global_state, quiet=False):
    g_map = global_state['maps']
    renders_per_agent = {}
    while True:
        debug_map(g_map, renders_per_agent, quiet)
        time.sleep(3.5)


def debug_map(global_map, number_of_renders, quiet):
    for agent in global_map:
        # Copy agent shared map into our image
        not quiet and print('[DEBUG_MAP]', agent + ': ' + global_map[agent]['map_id'])
        shm_map = shared_memory.SharedMemory(name=global_map[agent]['map_id'])
        void_map = np.zeros((70, 70))
        new_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_map.buf)
        image = np.zeros((70, 70))
        image[:] = new_map[:]

        # Agents with same map_id must appear at the same map
        for a in global_map:
            if global_map[agent]['map_id'] == global_map[a]['map_id']:
                image[global_map[a]['y'], global_map[a]['x']] = 100

        # Set params and save an image in png of the map
        cmap = colors.ListedColormap([(0.186, 0.186, 0.186),
                                      (0.91, 0.91, 0.91),
                                      (0.26, 0.26, 0.26),
                                      'blue'])
        bounds = [0, 0.9, 9, 99, 200]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        plt.imshow(image,
                   interpolation='nearest',
                   cmap=cmap,
                   norm=norm)
        number_of_renders[agent] = number_of_renders.get(agent, 0) + 1
        plt.savefig('img/' + global_map[agent]['map_id'] + '_map_' + str(number_of_renders[agent]) + '.png')


def main(argv=None):
    team_id = 'A'
    team_size = 15
    agent_id = None
    config = {}

    for arg in range(len(argv)):
        if TEAM_SIZE in argv[arg]:
            team_size = int(argv[arg + 1])

        if TEAM_ID in argv[arg]:
            team_id = argv[arg + 1]

        if AGENT_ID in argv[arg]:
            agent_id = argv[arg + 1] if team_size == 1 else None

        if CONFIG in argv[arg]:
            with open(argv[arg + 1]) as json_file:
                config = json.load(json_file)
                team_size = config[TEAM_SIZE] if TEAM_SIZE in config else 15
                team_id = config[TEAM_ID] if TEAM_ID in config else 'A'
                agent_id = config[AGENT_ID] if AGENT_ID in config else None

    if AGENT_IDS in config:
        agent_ids = config[AGENT_IDS]
    else:
        agent_ids = [i for i in range(1, team_size + 1)]

    agents_name = ['agent' + team_id + str(agent_id or i) for i in agent_ids]

    print('[MAIN]', 'args:', argv)

    manager = AgentManager(agents_name)
    step = 0
    while step < 750:
        print('[MAIN] step ' + str(step))
        manager.step()
        step += 1


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
