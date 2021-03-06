# MultiAgentProgrammingContest
Contest for MAPC 2020 using Python. Include agent and some modules such us an implementation of EISMASSIM for communicate with server.

Starting
---
Once upon you started the server you can start playing by executing the file "main.py" located in "/src". Several flags are available:

-   "--team-size": (integer) The number of agents playing the game.
-   "--team-name": (char) The main character of a team, it can be "A" or "B".
-   "--agent-id": (integer) The id of the agent you want to wake up. 
    
    NOTE: "--agent-id" works only when "--team-size" == 1

Example:

    (venv) project_root/src>python main.py --team-size 15 --team-id A 

Notice that we must execute "main.py" into a virtual environment after being executed the following sentence:

    pip install -r requirements.txt

Requirements:
---
-   Python ^3.8
-   Pip ^21.0.1


Agent Structure
---
Each agent consist in a group of modules:
-   Agent: Is the main module and unify a group of ones who let it perform some actions. 

-   ServerCommunication: Agents uses this module in order to authenticate with the server and start the communication sending or requesting data about an Entity. Agents send actions each step and receive a percept, actions and percepts are JSON structures.

-   BufferManager: This module is the way agents communicate with the server using different buffers. PerceptBuffer is where the agent read percepts, in the other hand, ActionBuffer is where the agent writes actions he tries to perform each step. 
  
-   CommonStructures: Provide JSON structures and variables used by each agent, some of them have default value, like server hosts.

The Multi Agent Programming Contest
---
This competition is an attempt to stimulate research in the area of multi-agent system development and programming. Two teams of multi-agents look for the victory just performing actions to make complex forms with boxes and delivering to a goal area. The team who got more points at the end of the match wins.

More information about the competition [here.](https://multiagentcontest.org/)

