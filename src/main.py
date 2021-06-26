import sys
from modules.agent_manager import AgentManager
import json


TEAM_SIZE = "--team-size"
TEAM_ID = "--team-name"
AGENT_ID = "--agent-id"
AGENT_IDS = "--agent-ids"
CONFIG = "--config-file"


def main(argv=None):
    team_id = 'A'
    team_size = 15
    agent_id = None
    config = {}

    if TEAM_SIZE in argv:
        team_size = int(argv[argv.index(TEAM_SIZE) + 1])

    if TEAM_ID in argv:
        team_id = argv[argv.index(TEAM_ID) + 1]

    if AGENT_ID in argv:
        agent_id = argv[argv.index(AGENT_ID) + 1] if team_size == 1 else None

    if CONFIG in argv:
        with open(argv[argv.index(CONFIG) + 1]) as json_file:
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
        manager.step()
        step += 1


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
