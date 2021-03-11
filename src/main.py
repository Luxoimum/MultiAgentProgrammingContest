import sys
from agent import Agent
from multiprocessing import Process, shared_memory, Array, Manager
import time
import numpy as np
import matplotlib.pyplot as plt
import json


TEAM_SIZE = "--team-size"
TEAM_ID = "--team-name"
AGENT_ID = "--agent-id"
AGENT_IDS = "--agent-ids"
CONFIG = "--config-file"


def play_game(agent_id, agent_name, state, shared_map, rol):
    a = Agent(agent_id, agent_name, state, shared_map)

    if rol == 'slave':
        a.play_slave()
    else:
        a.play_master()


def master(global_state):
    g_map = global_state['maps']
    states = global_state['states']
    number_of_renders = {}
    while True:
        edges = {}
        for a in states:
            if 'entities' in states[a] and len(states[a]['entities']) > 0:
                for e in states[a]['entities']:
                    key = str(abs(e[0]))+str(abs(e[1]))
                    edges[key] = [*edges.get(key, []), (a, e)]

        for edge in edges:
            queue = [m for m in edges[edge]]
            while len(queue) > 1:
                current = queue.pop(0)
                target = queue.pop(0)
                if g_map[current[0]]['map_id'] != g_map[target[0]]['map_id']:
                    update_map(g_map[current[0]]['map_id'], g_map[target[0]]['map_id'], target[1])
                    global_state['maps'][target[0]]['y'] = global_state['maps'][current[0]]['y'] + current[1][0]
                    global_state['maps'][target[0]]['x'] = global_state['maps'][current[0]]['x'] + current[1][1]
                    global_state['maps'][target[0]]['map_id'] = global_state['maps'][current[0]]['map_id']

        time.sleep(3.5)
        debug_map(g_map, number_of_renders)


def debug_map(global_map, number_of_renders):
    print('[debug_map]')
    print([m for m in global_map])
    for m in global_map:
        print(m + ': ' + global_map[m]['map_id'])
        number_of_renders[m] = number_of_renders.get(m, 0) + 1
        shm_map = shared_memory.SharedMemory(name=global_map[m]['map_id'])
        void_map = np.zeros((70, 70))
        new_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_map.buf)
        positions = np.zeros((70, 70))
        positions[:] = new_map[:]

        # get agents with same map so it can be printed together
        for agent in global_map:
            if global_map[m]['map_id'] == global_map[agent]['map_id']:
                positions[global_map[agent]['y'], global_map[agent]['x']] = 100
                print(agent, global_map[agent]['y'], global_map[agent]['x'])

        plt.imshow(positions, interpolation='nearest')
        plt.savefig('img/' + m + '_map_' + str(number_of_renders[m]) + '.png')

    time.sleep(3.5)


def update_map(shared_map_id, shared_map_to_merge_id, position):
    void_map = np.zeros((70, 70))
    # Get shared memory of both maps
    shm_m_1 = shared_memory.SharedMemory(name=shared_map_id)
    map_1 = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m_1.buf)
    shm_m_2 = shared_memory.SharedMemory(name=shared_map_to_merge_id)
    map_2 = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m_2.buf)

    # roll map to merge with
    map_2 = np.roll(map_2, position[0], axis=0)
    map_2 = np.roll(map_2, position[1], axis=1)

    mask = map_2 > 0

    map_1[mask] = map_2[mask]


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

    print('[MAIN]')
    print('args:', args_dictionary)

    for i, a in enumerate(agents_name):
        print('Process: ' + a)

        if a == 'master':
            agents.append(Process(
                target=master,
                args=(global_state,)
            ))
        else:
            void_map = np.zeros(map_size)
            global_state['maps_shm'][a] = shared_memory.SharedMemory(name='map_' + a, create=True, size=void_map.nbytes)
            new_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=global_state['maps_shm'][a].buf)
            new_map[:] = void_map[:]

            single_map = manager.dict()
            single_map['map_id'] = global_state['maps_shm'][a].name
            single_map['y'] = int(map_size[0]/2)
            single_map['x'] = int(map_size[1]/2)
            global_state['maps'][a] = single_map

            single_state = manager.dict()
            global_state['states'][a] = single_state
            agents.append(Process(
                target=play_game,
                args=(
                    agent_ids[i],
                    a,
                    global_state['states'][a],
                    global_state['maps'][a],
                    'slave'
                )
            ))

    for a in agents:
        a.start()

    for a in agents:
        a.join()


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
