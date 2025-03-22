import yaml
from crewai import Crew, Agent, Task
from tools.scraping_tools import BeautifulSoupTool, RequestsTool
from tools.analysis_tools import PropertyAnalysisTool, DataValidationTool
from typing import Dict, List, Callable, Optional
import json
from datetime import datetime
import hashlib
from queue import Queue
import threading

class PropertyResearchCrew:
    def __init__(self, status_callback: Optional[Callable] = None):
        self.status_callback = status_callback
        self.agents = self._load_agents()
        self.tasks = self._load_tasks()
        self.crew = None
        self._emit_status("Crew initialized and ready")

    def _emit_status(self, message: str, agent: str = None, task: str = None, step: str = None):
        """Emit status update through callback if available"""
        if self.status_callback:
            status = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "agent": agent,
                "task": task,
                "step": step
            }
            self.status_callback(status)

    def _load_agents(self) -> Dict[str, Agent]:
        self._emit_status("Loading agent configurations...")
        with open('config/agents.yaml', 'r') as f:
            agents_config = yaml.safe_load(f)

        agents = {}
        for agent_id, config in agents_config.items():
            self._emit_status(f"Initializing agent: {config['name']}", agent=agent_id)
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
                goal=config['goal'],
                backstory=config['backstory'],
                tools=tools,
                verbose=config.get('verbose', True),
                allow_delegation=config.get('allow_delegation', False),
                llm_config={
                    "model": config['llm']['model'],
                    "temperature": config['llm']['temperature']
                }
            )
            self._emit_status(f"Agent {config['name']} initialized with {len(tools)} tools", agent=agent_id)

        return agents

    def _load_tasks(self) -> List[Task]:
        self._emit_status("Loading task configurations...")
        with open('config/tasks.yaml', 'r') as f:
            tasks_config = yaml.safe_load(f)

        tasks = []
        for task_id, config in tasks_config.items():
            self._emit_status(f"Creating task: {config['name']}", task=task_id)
            context_item = {
                "description": config['description'],
                "expected_output": config.get('output_format', 'json'),
                "parameters": config.get('parameters', {})
            }
            
            task = Task(
                description=config['description'],
                agent=self.agents[config['assignee']],
                expected_output=config.get('output_format', 'json'),
                context=[context_item]
            )
            tasks.append(task)
            self._emit_status(f"Task {config['name']} assigned to {config['assignee']}", task=task_id)

        return tasks

    def _hash_search_criteria(self, criteria: Dict) -> str:
        """
        Create a deterministic hash of the search criteria for cache comparison
        """
        # Sort the criteria to ensure consistent hashing
        sorted_criteria = {
            k: sorted(v) if isinstance(v, list) else v
            for k, v in sorted(criteria.items())
        }
        # Convert to string and hash
        criteria_str = json.dumps(sorted_criteria, sort_keys=True)
        return hashlib.md5(criteria_str.encode()).hexdigest()

    def _save_results(self, results, search_criteria: Dict):
        """Save results and search criteria to cache"""
        # Convert CrewOutput to dictionary with properly structured data
        results_list = results.tasks_output
        if not isinstance(results_list, list):
            results_list = [results_list]

        # Create cache entry with results and search criteria
        cache_entry = {
            "result": results_list,
            "search_criteria": search_criteria,
            "criteria_hash": self._hash_search_criteria(search_criteria),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to JSON file
        with open('data/properties.json', 'w') as f:
            json.dump(cache_entry, f, indent=2, cls=PropertyJSONEncoder)
            print(f"Results saved to data/properties.json")

    def run(self, search_criteria: Dict, force_refresh: bool = False) -> Dict:
        """
        Execute the property research workflow
        Args:
            search_criteria: Dictionary containing search parameters
            force_refresh: Boolean to force new search even if results exist
        """
        self._emit_status("Starting property research workflow")
        
        # Check for existing results unless force refresh is requested
        if not force_refresh:
            try:
                with open('data/properties.json', 'r') as f:
                    cached_data = json.load(f)
                    # Compare search criteria hash
                    current_hash = self._hash_search_criteria(search_criteria)
                    if cached_data.get('criteria_hash') == current_hash:
                        self._emit_status("Using cached results from previous search")
                        return cached_data
                    else:
                        self._emit_status("Search criteria changed, initiating new search")
            except (FileNotFoundError, json.JSONDecodeError):
                self._emit_status("No valid cache found, starting fresh search")

        # Execute new search
        self._emit_status("Initializing AI crew for property search")
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            verbose=True
        )

        # Execute the crew's tasks
        self._emit_status("Starting task execution sequence")
        results = self.crew.kickoff()
        
        # Process and save results with search criteria
        self._emit_status("Processing and saving search results")
        self._save_results(results, search_criteria)
        
        # Return the results
        self._emit_status("Search workflow completed successfully")
        return {
            "result": results.tasks_output if isinstance(results.tasks_output, list) else [results.tasks_output],
            "search_criteria": search_criteria,
            "criteria_hash": self._hash_search_criteria(search_criteria),
            "timestamp": datetime.now().isoformat()
        }

    def get_agent(self, agent_id: str) -> Agent:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID"""
        return next((task for task in self.tasks if task.id == task_id), None)

class PropertyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj) 