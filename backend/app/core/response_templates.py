from typing import Dict, Any, List
import openai
from app.core.config import settings

class ResponseGenerator:
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    def generate_activity_summary(self, activity_data: Dict[str, Any]) -> str:
        """Generate a natural language summary of team activity"""
        
        # Extract key metrics
        jira_data = activity_data.get('jira', {})
        github_data = activity_data.get('github', {})
        
        # Basic template-based response (fallback)
        template_response = self._generate_template_response(jira_data, github_data)
        
        # If OpenAI is configured, enhance with AI
        if settings.openai_api_key:
            try:
                return self._generate_ai_response(activity_data, template_response)
            except Exception as e:
                print(f"OpenAI error: {e}")
                return template_response
        
        return template_response
    
    def _generate_template_response(self, jira_data: Dict, github_data: Dict) -> str:
        """Generate a basic template-based response"""
        response_parts = []
        
        # JIRA summary
        if jira_data.get('issues'):
            issue_count = len(jira_data['issues'])
            response_parts.append(f"📋 Found {issue_count} JIRA issue(s)")
            
            # Group by status
            status_counts = {}
            for issue in jira_data['issues']:
                status = issue.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                status_summary = ", ".join([f"{count} {status}" for status, count in status_counts.items()])
                response_parts.append(f"Status breakdown: {status_summary}")
        
        # GitHub summary
        if github_data.get('commits'):
            commit_count = len(github_data['commits'])
            response_parts.append(f"💻 Found {commit_count} recent commit(s)")
        
        if github_data.get('pull_requests'):
            pr_count = len(github_data['pull_requests'])
            response_parts.append(f"🔄 Found {pr_count} pull request(s)")
        
        return "\n".join(response_parts) if response_parts else "No recent activity found."
    
    def _generate_ai_response(self, activity_data: Dict, template_response: str) -> str:
        """Generate an AI-enhanced response using OpenAI"""
        prompt = f"""
        Based on the following team activity data, provide a helpful and concise summary:
        
        Activity Data: {activity_data}
        
        Basic Summary: {template_response}
        
        Please provide a natural, conversational summary that highlights:
        - Key team members and their contributions
        - Important trends or patterns
        - Any notable achievements or blockers
        - Actionable insights for team management
        
        Keep the response friendly and informative, like a helpful team assistant.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful team activity assistant that provides insights about software development team productivity."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
