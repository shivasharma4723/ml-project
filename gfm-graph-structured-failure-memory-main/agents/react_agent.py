"""
Baseline ReAct Agent Implementation for Comparison
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class AgentStep:
    """Represents a single step in agent execution"""
    thought: str
    action: str
    observation: str
    step_number: int


class ReactAgent:
    """
    Baseline ReAct (Reasoning + Acting) agent implementation.
    Used for comparison with the GFM-enhanced agent.
    """
    
    def __init__(self, max_steps: int = 10, verbose: bool = True):
        """
        Initialize the ReAct agent.
        
        Args:
            max_steps: Maximum number of reasoning-acting cycles
            verbose: Whether to print execution details
        """
        self.max_steps = max_steps
        self.verbose = verbose
        self.steps: List[AgentStep] = []
        self.error_count = 0
        self.success = False
    
    def run(self, task: str, tools: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using the ReAct loop.
        
        Args:
            task: The task description to execute
            tools: Dictionary of available tools/functions
            
        Returns:
            Execution results with statistics
        """
        if self.verbose:
            print(f"Starting ReAct Agent for task: {task}")
        
        self.steps = []
        self.error_count = 0
        self.success = False
        
        observation = task
        
        for step_num in range(1, self.max_steps + 1):
            # Thought phase
            thought = self._generate_thought(observation, step_num)
            
            # Action phase
            action, action_input = self._generate_action(observation, thought, tools)
            
            # Execution phase
            try:
                result = self._execute_action(action, action_input, tools)
                observation = result
                outcome = "success"
            except Exception as e:
                observation = f"Error: {str(e)}"
                self.error_count += 1
                outcome = "failure"
            
            # Record step
            step = AgentStep(
                thought=thought,
                action=f"{action}({action_input})",
                observation=observation,
                step_number=step_num
            )
            self.steps.append(step)
            
            if self.verbose:
                print(f"\nStep {step_num}:")
                print(f"Thought: {thought}")
                print(f"Action: {action}({action_input})")
                print(f"Observation: {observation}")
            
            # Check for task completion
            if self._is_task_complete(observation):
                self.success = True
                if self.verbose:
                    print(f"\nTask completed successfully in {step_num} steps!")
                break
            
            # Check for error loop
            if self._detect_error_loop():
                if self.verbose:
                    print(f"\nError loop detected after {step_num} steps!")
                break
        
        return self._generate_results()
    
    def _generate_thought(self, observation: str, step_num: int) -> str:
        """
        Generate a thought based on current observation.
        In a real implementation, this would use an LLM.
        """
        if "Error" in observation:
            return f"I encountered an error. I need to analyze what went wrong and try a different approach."
        elif step_num == 1:
            return f"I need to understand the task and determine the first action to take."
        else:
            return f"Based on the previous observation, I should continue with the next logical step."
    
    def _generate_action(self, observation: str, thought: str, 
                       tools: Dict[str, Any]) -> tuple:
        """
        Generate an action based on thought and observation.
        In a real implementation, this would use an LLM.
        """
        # Simple heuristic: try available tools in order
        tool_names = list(tools.keys())
        
        if "Error" in observation:
            # Try a different tool on error
            if tool_names:
                return tool_names[len(self.steps) % len(tool_names)], observation
            return "retry", observation
        else:
            if tool_names:
                return tool_names[0], observation
            return "think", observation
    
    def _execute_action(self, action: str, action_input: str, 
                       tools: Dict[str, Any]) -> str:
        """
        Execute the selected action.
        """
        if action in tools:
            tool_func = tools[action]
            return tool_func(action_input)
        elif action == "retry":
            return "Retrying with modified approach..."
        else:
            return f"Unknown action: {action}"
    
    def _is_task_complete(self, observation: str) -> bool:
        """Check if the task is complete."""
        return "success" in observation.lower() or "completed" in observation.lower()
    
    def _detect_error_loop(self) -> bool:
        """Detect if the agent is in an error loop."""
        if len(self.steps) < 3:
            return False
        
        # Check if last 3 steps all had errors
        recent_errors = sum(1 for step in self.steps[-3:] if "Error" in step.observation)
        return recent_errors >= 3
    
    def _generate_results(self) -> Dict[str, Any]:
        """Generate execution results."""
        return {
            'success': self.success,
            'total_steps': len(self.steps),
            'error_count': self.error_count,
            'steps': [
                {
                    'step': s.step_number,
                    'thought': s.thought,
                    'action': s.action,
                    'observation': s.observation
                }
                for s in self.steps
            ],
            'agent_type': 'ReAct'
        }
    
    def get_execution_trace(self) -> List[Dict[str, str]]:
        """Get the full execution trace."""
        return [
            {
                'step': s.step_number,
                'thought': s.thought,
                'action': s.action,
                'observation': s.observation
            }
            for s in self.steps
        ]
