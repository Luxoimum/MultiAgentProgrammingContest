import sys
from agent import Agent
from multiprocessing import Process, shared_memory, Array
import time
import numpy as np


TEAM_SIZE = "--team-size"
TEAM_ID = "--team-name"
AGENT_ID = "--agent-id"


def play_game(agent_name, state, shared_map_id, position, rol):
    a = Agent(agent_name, state, shared_map_id, position)

    if rol == 'slave':
        a.play_slave()
    else:
        a.play_master()


def debug_state(global_state):
    while True:
        print('[MASTER]')
        print(global_state)
        time.sleep(3.5)


def main(argv=None):
    team_id = 'A'
    team_size = 15
    agent_id = None
    args_dictionary = {}

    for arg in range(len(argv)):
        if '--' in argv[arg]:
            args_dictionary[argv[arg]] = argv[arg + 1]

    if TEAM_SIZE in args_dictionary:
        team_size = int(args_dictionary[TEAM_SIZE])

    if TEAM_ID in args_dictionary:
        team_id = args_dictionary[TEAM_ID]

    if AGENT_ID in args_dictionary:
        agent_id = args_dictionary[AGENT_ID] if team_size == 1 else None

    agents_name = ['agent' + team_id + str(agent_id or i) for i in range(1, team_size + 1)]
    agents_name.append('master')
    agents = []

    global_state = {
        'states': {},
        'maps': {},
        'positions': {}
    }

    map_size = (70, 70)

    print('[MAIN]')
    print('args:', args_dictionary)

    for a in agents_name:
        print('Process: ' + a)

        if a == 'master':
            """agents.append(Process(
                target=debug_state,
                args=(global_state,)
            ))"""
        else:
            global_state['states'][a] = Array('i', [0])

            void_map = np.zeros(map_size)
            shm_map = shared_memory.SharedMemory(name='map_'+a, create=True, size=void_map.nbytes)
            new_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_map.buf)
            new_map[:] = void_map[:]
            global_state['maps'][a] = shm_map.name

            global_state['positions'][a] = Array('i', [int(i/2) for i in map_size])

            agents.append(Process(
                target=play_game,
                args=(
                    a,
                    global_state['states'][a],
                    shm_map.name,
                    global_state['positions'][a],
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
