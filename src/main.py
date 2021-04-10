import sys
from agent import Agent
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


def play_master(agent_id, agent_name, global_state):
    a = Agent(agent_id, agent_name)
    a.play_master(global_state)


def play_slave(agent_id, agent_name, state, shared_map):
    a = Agent(agent_id, agent_name, state, shared_map)
    a.play_slave()


def debugger(global_state, quiet=False):
    g_map = global_state['maps']
    renders_per_agent = {}
    while True:
        maps = {}
        for a in g_map:
            if g_map[a]['map_id'] not in maps:
                maps[g_map[a]['map_id']] = [a]
            else:
                maps[g_map[a]['map_id']].append(a)

        debug_map(maps, g_map, renders_per_agent, quiet)
        time.sleep(1)


def debug_map(maps, global_map, number_of_renders, quiet):
    for single_map in maps:
        if len(maps[single_map]) > 1:
            # Copy agent shared map into our image
            not quiet and print('[DEBUG_MAP]: ', single_map, maps[single_map])
            shm_map = shared_memory.SharedMemory(name=single_map)
            void_map = np.zeros((70, 70))
            new_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_map.buf)
            image = np.zeros((70, 70))
            image[:] = new_map[:]

            # Agents with same map_id must appear at the same map
            for agent in maps[single_map]:
                image[global_map[agent]['y'], global_map[agent]['x']] = 100

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
            number_of_renders[single_map] = number_of_renders.get(single_map, 0) + 1
            plt.savefig('img/' + single_map + '_map_' + str(number_of_renders[single_map]) + '.png')


def main(argv=None):
    team_id = 'A'
    team_size = 15
    agent_id = None
    args_dictionary = {}
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
    agents_name.append('master')
    agents = []

    global_state = {
        'states': {},
        'maps': {},
        'maps_shm': {}
    }

    map_size = (70, 70)
    manager = Manager()

    print('[MAIN]', 'args:', args_dictionary)

    for i, a in enumerate(agents_name):
        print('[MAIN]', 'Process: ' + a)
        if a == 'master':
            # Create master agent instance
            # (this one do not interact with anything else but global_state)
            agents.append(Process(target=play_master, args=(
                0,
                a,
                global_state)
            ))
        else:
            # Create a new empty map for this agent
            void_map = np.zeros(map_size)
            global_state['maps_shm'][a] = shared_memory.SharedMemory(name='map_' + a, create=True, size=void_map.nbytes)
            new_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=global_state['maps_shm'][a].buf)
            new_map[:] = void_map[:]

            # Allocate shared memory, shared memory pointer, and position of this agent
            single_map = manager.dict()
            single_map['map_id'] = global_state['maps_shm'][a].name
            single_map['y'] = int(map_size[0]/2)
            single_map['x'] = int(map_size[1]/2)
            global_state['maps'][a] = single_map

            # Allocate space for agent internal states
            single_state = manager.dict()
            global_state['states'][a] = single_state

            # Create agent instance
            agents.append(Process(target=play_slave, args=(
                agent_ids[i],
                a,
                global_state['states'][a],
                global_state['maps'][a])
            ))



    for a in agents:
        a.start()

    for a in agents:
        a.join()


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
