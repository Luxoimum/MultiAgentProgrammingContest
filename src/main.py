import sys
from agent import Agent
from multiprocessing import Process, Queue


TEAM_SIZE = "--team-size"
TEAM_ID = "--team-name"


def play_game(agent_name, q=None):
    Agent(agent_name, q)


def main(argv=None):
    team_id = 'A'
    team_size = 15
    args_dictionary = {}

    for arg in range(len(argv)):
        if '--' in argv[arg]:
            args_dictionary[argv[arg]] = argv[arg + 1]

    if TEAM_SIZE in args_dictionary:
        team_size = int(args_dictionary[TEAM_SIZE])

    if TEAM_ID in args_dictionary:
        team_id = args_dictionary[TEAM_ID]

    agents_name = ['agent' + team_id + str(i) for i in range(1, team_size + 1)]
    agents = []
    q = Queue()
    print('[MAIN]')
    print('args:', args_dictionary)
    for a in agents_name:
        print('Process: ' + a)
        agents.append(Process(target=play_game, args=(a, q)))

    for a in agents:
        a.start()

    for a in agents:
        a.join()


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
