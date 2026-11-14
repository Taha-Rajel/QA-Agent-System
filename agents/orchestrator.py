"""Coordinates all QA agents for a single run."""

from agents.auth_agent import AuthAgent
from agents.correction_agent import CorrectionAgent
from agents.form_agent import FormAgent
from agents.navigation_agent import NavigationAgent
from agents.ui_agent import UIAgent
from agents.visual_agent import VisualAgent
from agents.website_description_agent import WebsiteDescriptionAgent
from config import TARGET_URL as DEFAULT_TARGET_URL
from tools.browser_tool import navigate
from tools.log_tool import log_step


class Orchestrator:
    """Runs agents in the fixed order, then adds correction guidance."""

    def __init__(self, page, target_url: str | None = None):
        self.page = page
        self.target_url = target_url or DEFAULT_TARGET_URL
        self.visual_agent = VisualAgent()
        self.agents = [
            WebsiteDescriptionAgent(page, self.target_url),
            UIAgent(page, self.visual_agent, self.target_url),
            AuthAgent(page, self.visual_agent, self.target_url),
            NavigationAgent(page, self.target_url),
            FormAgent(page, self.visual_agent, self.target_url),
        ]
        self.correction_agent = CorrectionAgent()

    async def run(self):
        """Run all agents and return a flat list of TestResult objects."""
        await navigate(self.page, self.target_url)

        results = []
        for agent in self.agents:
            log_step(f"Starting {agent.name} agent")
            agent_results = await agent.run()
            results.extend(agent_results)
            log_step(f"Finished {agent.name} agent")

        log_step(f"Starting {self.correction_agent.name} agent")
        correction_results = await self.correction_agent.run(results)
        results.extend(correction_results)
        log_step(f"Finished {self.correction_agent.name} agent")
        return results
