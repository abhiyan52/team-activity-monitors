import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

class QueryParser:
    def __init__(self):
        # Common patterns for extracting information from queries
        self.name_patterns = [
            r"@(\w+)",  # @username
            r"by\s+(\w+)",  # by username
            r"from\s+(\w+)",  # from username
            r"(\w+)'s",  # username's
        ]
        
        self.date_patterns = [
            r"last\s+(\d+)\s+days?",  # last 7 days
            r"past\s+(\d+)\s+days?",  # past 7 days
            r"(\d+)\s+days?\s+ago",  # 7 days ago
            r"this\s+week",  # this week
            r"last\s+week",  # last week
            r"this\s+month",  # this month
            r"yesterday",  # yesterday
            r"today",  # today
        ]
    
    def extract_team_members(self, query: str) -> List[str]:
        """Extract team member names from the query"""
        members = []
        
        for pattern in self.name_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            members.extend(matches)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(members))
    
    def extract_date_range(self, query: str) -> Optional[Dict[str, datetime]]:
        """Extract date range from the query"""
        query_lower = query.lower()
        now = datetime.now()
        
        # Check for specific day patterns
        for pattern in self.date_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if "last" in pattern or "past" in pattern:
                    try:
                        days = int(match.group(1))
                        return {
                            "start": now - timedelta(days=days),
                            "end": now
                        }
                    except (IndexError, ValueError):
                        continue
                elif "days ago" in pattern:
                    try:
                        days = int(match.group(1))
                        return {
                            "start": now - timedelta(days=days),
                            "end": now - timedelta(days=days-1)
                        }
                    except (IndexError, ValueError):
                        continue
                elif "this week" in query_lower:
                    # Start of current week (Monday)
                    start_of_week = now - timedelta(days=now.weekday())
                    return {
                        "start": start_of_week.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": now
                    }
                elif "last week" in query_lower:
                    start_of_last_week = now - timedelta(days=now.weekday() + 7)
                    end_of_last_week = start_of_last_week + timedelta(days=6)
                    return {
                        "start": start_of_last_week.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": end_of_last_week.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif "this month" in query_lower:
                    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    return {
                        "start": start_of_month,
                        "end": now
                    }
                elif "yesterday" in query_lower:
                    yesterday = now - timedelta(days=1)
                    return {
                        "start": yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                    }
                elif "today" in query_lower:
                    return {
                        "start": now.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end": now
                    }
        
        return None
    
    def extract_project_info(self, query: str) -> Optional[str]:
        """Extract project key from query (for JIRA)"""
        # Look for patterns like "project ABC" or "ABC-123"
        project_patterns = [
            r"project\s+([A-Z]+)",
            r"([A-Z]{2,10})-\d+",  # JIRA issue key pattern
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def extract_repository_info(self, query: str) -> Optional[str]:
        """Extract repository name from query (for GitHub)"""
        # Look for patterns like "repo xyz" or "repository xyz"
        repo_patterns = [
            r"repo(?:sitory)?\s+([a-zA-Z0-9\-_]+)",
            r"in\s+([a-zA-Z0-9\-_]+)\s+repo",
        ]
        
        for pattern in repo_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_status_info(self, query: str) -> Optional[str]:
        """Extract status information from query"""
        status_patterns = [
            r"status\s+([a-zA-Z\s]+)",
            r"(open|closed|merged|in progress|to do|done|resolved)\s+",
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip().lower()
        
        return None
    
    def determine_data_sources(self, query: str) -> Dict[str, bool]:
        """Determine which data sources to query based on the query content"""
        query_lower = query.lower()
        
        # Keywords that suggest specific sources
        jira_keywords = ["jira", "issue", "ticket", "story", "bug", "task", "sprint", "project"]
        github_keywords = ["github", "commit", "pull request", "pr", "merge", "branch", "repository", "repo"]
        
        sources = {
            "jira": False,
            "github": False
        }
        
        # Check for explicit mentions
        for keyword in jira_keywords:
            if keyword in query_lower:
                sources["jira"] = True
                break
        
        for keyword in github_keywords:
            if keyword in query_lower:
                sources["github"] = True
                break
        
        # If no specific source is mentioned, query both
        if not sources["jira"] and not sources["github"]:
            sources["jira"] = True
            sources["github"] = True
        
        return sources
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse the complete query and extract all relevant information"""
        return {
            "original_query": query,
            "team_members": self.extract_team_members(query),
            "date_range": self.extract_date_range(query),
            "project_key": self.extract_project_info(query),
            "repository": self.extract_repository_info(query),
            "status": self.extract_status_info(query),
            "data_sources": self.determine_data_sources(query)
        }
