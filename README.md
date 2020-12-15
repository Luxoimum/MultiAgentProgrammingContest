# MultiAgentProgrammingContest
Contest for MAPC 2020 using Python. Include agent and some modules such us an implementation of EISMASSIM for communicate with server.

Initial Structure
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

