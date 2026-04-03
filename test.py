from env.environment import EmailTriageEnv
from agent.agent import simple_agent

env = EmailTriageEnv()

obs = env.reset()
print("Observation:", obs)

action = simple_agent(obs)
print("Action:", action)

result = env.step(action)
print("Result:", result)
