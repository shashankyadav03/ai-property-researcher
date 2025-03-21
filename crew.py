import yaml
from crewai import Crew, Agent, Task
from tools.scraping_tools import BeautifulSoupTool, RequestsTool
from tools.analysis_tools import PropertyAnalysisTool, DataValidationTool
from typing import Dict, List
import json

class PropertyResearchCrew:
    def __init__(self):
        self.agents = self._load_agents()
        self.tasks = self._load_tasks()
        self.crew = None

    def _load_agents(self) -> Dict[str, Agent]:
        with open('config/agents.yaml', 'r') as f:
            agents_config = yaml.safe_load(f)

        agents = {}
        for agent_id, config in agents_config.items():
            tools = []
            for tool_name in config.get('tools', []):
                if tool_name == 'BeautifulSoupTool':
                    tools.append(BeautifulSoupTool())
                elif tool_name == 'RequestsTool':
                    tools.append(RequestsTool())
                elif tool_name == 'PropertyAnalysisTool':
                    tools.append(PropertyAnalysisTool())
                elif tool_name == 'DataValidationTool':
                    tools.append(DataValidationTool())

            agents[agent_id] = Agent(
                name=config['name'],
                role=config['role'],
                goal=config['goals'],
                backstory=config['backstory'],
                tools=tools,
                llm_config={
                    "model": config['llm']['model'],
                    "temperature": config['llm']['temperature']
                }
            )

        return agents

    def _load_tasks(self) -> List[Task]:
        with open('config/tasks.yaml', 'r') as f:
            tasks_config = yaml.safe_load(f)

        tasks = []
        for task_id, config in tasks_config.items():
            task = Task(
                description=config['description'],
                agent=self.agents[config['assignee']],
                expected_output=config.get('output_format', 'json'),
                context=config.get('parameters', {})
            )
            tasks.append(task)

        return tasks

    def _save_results(self, results: List[Dict]):
        with open('data/properties.json', 'w') as f:
            json.dump(results, f, indent=2)

    def run(self, search_criteria: Dict) -> List[Dict]:
        """
        Execute the property research workflow
        """
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            verbose=True
        )

        # Execute the crew's tasks
        results = self.crew.kickoff()
        
        # Process and save results
        self._save_results(results)
        
        return results

    def get_agent(self, agent_id: str) -> Agent:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID"""
        return next((task for task in self.tasks if task.id == task_id), None) 