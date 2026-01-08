import dspy
from dspy.utils.callback import BaseCallback
from dspy_skills import SkillsReActAgent, SkillsConfig
from pathlib import Path


class AgentLoggingCallback(BaseCallback):

    def on_module_end(self, call_id, outputs, exception):
        step = "Reasoning" if self._is_reasoning_output(outputs) else "Acting"
        print(f"== {step} Step ===")
        for k, v in outputs.items():
            print(f"  {k}: {v}")
        print("\n")

    def _is_reasoning_output(self, outputs):
        return any(k.startswith("Thought") for k in outputs.keys())


dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"), callbacks=[AgentLoggingCallback()])

# Load config from YAML file
config = SkillsConfig.from_yaml(Path("skills_config.yaml"))

agent = SkillsReActAgent(
    signature="request: str -> response: str",
    config=config,
)

print("=" * 60)
print("Skills Agent Chat")
print(f"Loaded {len(agent.discovered_skills)} skills: {', '.join(agent.discovered_skills)}")
print("Type 'quit' or 'exit' to stop, 'skills' to list skills")
print("=" * 60)

while True:
    try:
        user_input = input("\n> ").strip()

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if user_input.lower() == "skills":
            print(f"Available skills: {', '.join(agent.discovered_skills)}")
            if agent.active_skill:
                print(f"Active skill: {agent.active_skill}")
            continue

        result = agent(request=user_input)
        print("=" * 60)
        print(f"\n{result.response}")
        print("=" * 60)
        # print(result)

    except KeyboardInterrupt:
        print("\nGoodbye!")
        break
    except Exception as e:
        print(f"\nError: {e}")