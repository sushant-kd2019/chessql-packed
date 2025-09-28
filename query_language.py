"""
Chess Query Language Module
Provides a query language interface for searching chess games in the database.
"""

from typing import List, Dict, Any, Optional, Union
from database import ChessDatabase
import re


class ChessQueryLanguage:
    """Query language processor for chess game searches."""
    
    def __init__(self, db_path: str = "chess_games.db"):
        """Initialize the query language with database connection."""
        self.db = ChessDatabase(db_path)
        self.operators = {
            'AND': 'AND',
            'OR': 'OR',
            'NOT': 'NOT',
            'and': 'AND',
            'or': 'OR',
            'not': 'NOT'
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse a query string into structured query components."""
        query = query.strip()
        
        # Handle different query types
        if query.startswith('SELECT'):
            return self._parse_select_query(query)
        elif query.startswith('FIND'):
            return self._parse_find_query(query)
        else:
            # Treat as a simple search query
            return self._parse_simple_query(query)
    
    def _parse_select_query(self, query: str) -> Dict[str, Any]:
        """Parse SQL-like SELECT queries."""
        # Basic SELECT parsing (simplified)
        # Example: SELECT * FROM games WHERE white_player = "Magnus Carlsen"
        
        query_type = "SELECT"
        
        # Extract WHERE clause
        where_match = re.search(r'WHERE\s+(.+)', query, re.IGNORECASE)
        where_clause = where_match.group(1) if where_match else ""
        
        # Parse WHERE conditions
        conditions = self._parse_where_conditions(where_clause)
        
        return {
            'type': query_type,
            'conditions': conditions,
            'limit': 100  # Default limit
        }
    
    def _parse_find_query(self, query: str) -> Dict[str, Any]:
        """Parse FIND queries for specific game patterns."""
        # Example: FIND games where white_player = "Magnus Carlsen" AND result = "1-0"
        
        query_type = "FIND"
        
        # Extract the conditions part
        where_match = re.search(r'FIND\s+games?\s+where\s+(.+)', query, re.IGNORECASE)
        if not where_match:
            # Try alternative format
            where_match = re.search(r'FIND\s+(.+)', query, re.IGNORECASE)
        
        where_clause = where_match.group(1) if where_match else query[4:].strip()
        conditions = self._parse_where_conditions(where_clause)
        
        return {
            'type': query_type,
            'conditions': conditions,
            'limit': 100
        }
    
    def _parse_simple_query(self, query: str) -> Dict[str, Any]:
        """Parse simple text search queries."""
        return {
            'type': 'SEARCH',
            'search_term': query,
            'limit': 100
        }
    
    def _parse_where_conditions(self, where_clause: str) -> List[Dict[str, Any]]:
        """Parse WHERE clause conditions."""
        conditions = []
        
        # Split by AND/OR operators
        parts = re.split(r'\s+(AND|OR)\s+', where_clause, flags=re.IGNORECASE)
        
        i = 0
        while i < len(parts):
            if i % 2 == 0:  # Condition part
                condition = self._parse_single_condition(parts[i])
                if condition:
                    conditions.append(condition)
            else:  # Operator part
                if parts[i].upper() in ['AND', 'OR']:
                    if conditions:
                        conditions[-1]['operator'] = parts[i].upper()
            i += 1
        
        return conditions
    
    def _parse_single_condition(self, condition: str) -> Optional[Dict[str, Any]]:
        """Parse a single condition."""
        condition = condition.strip()
        
        # Handle different condition formats
        patterns = [
            # field = "value"
            (r'(\w+)\s*=\s*"([^"]*)"', 'equals'),
            # field = value
            (r'(\w+)\s*=\s*(\S+)', 'equals'),
            # field contains "value"
            (r'(\w+)\s+contains\s+"([^"]*)"', 'contains'),
            # field like "value"
            (r'(\w+)\s+like\s+"([^"]*)"', 'like'),
            # field > value
            (r'(\w+)\s*>\s*(\S+)', 'greater_than'),
            # field < value
            (r'(\w+)\s*<\s*(\S+)', 'less_than'),
        ]
        
        for pattern, operator in patterns:
            match = re.match(pattern, condition, re.IGNORECASE)
            if match:
                field = match.group(1).lower()
                value = match.group(2)
                
                return {
                    'field': field,
                    'operator': operator,
                    'value': value
                }
        
        return None
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a parsed query and return results."""
        parsed_query = self.parse_query(query)
        
        if parsed_query['type'] == 'SEARCH':
            return self.db.search_games(parsed_query['search_term'])
        
        elif parsed_query['type'] in ['SELECT', 'FIND']:
            filters = self._build_filters(parsed_query['conditions'])
            return self.db.get_games(filters, parsed_query['limit'])
        
        return []
    
    def _build_filters(self, conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build database filters from parsed conditions."""
        filters = {}
        
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value']
            
            if operator == 'equals':
                if field in ['white_player', 'black_player', 'result', 'eco_code']:
                    filters[field] = value
                elif field == 'date':
                    filters['date_played'] = value
            
            elif operator == 'contains':
                if field == 'opening':
                    filters['opening_contains'] = value
                elif field in ['white_player', 'black_player']:
                    # For contains, we'll use search instead
                    pass
            
            elif operator == 'like':
                if field == 'opening':
                    filters['opening_contains'] = value.replace('%', '')
            
            elif operator == 'greater_than':
                if field == 'date':
                    filters['date_from'] = value
            
            elif operator == 'less_than':
                if field == 'date':
                    filters['date_to'] = value
        
        return filters
    
    def get_available_fields(self) -> List[str]:
        """Get list of available fields for queries."""
        return [
            'white_player',
            'black_player', 
            'result',
            'date_played',
            'event',
            'site',
            'round',
            'eco_code',
            'opening',
            'time_control'
        ]
    
    def get_query_examples(self) -> List[str]:
        """Get example queries for the user."""
        return [
            'SELECT * FROM games WHERE white_player = "Magnus Carlsen"',
            'FIND games where result = "1-0" AND eco_code = "E90"',
            'FIND games where white_player contains "Carlsen"',
            'FIND games where opening like "%Sicilian%"',
            'FIND games where date_played > "2020-01-01"',
            'Magnus Carlsen',  # Simple search
            'Sicilian Defense'  # Simple search
        ]


class QueryBuilder:
    """Helper class for building complex queries programmatically."""
    
    def __init__(self):
        self.conditions = []
        self.limit = 100
    
    def where(self, field: str, operator: str, value: str) -> 'QueryBuilder':
        """Add a WHERE condition."""
        self.conditions.append({
            'field': field,
            'operator': operator,
            'value': value
        })
        return self
    
    def and_where(self, field: str, operator: str, value: str) -> 'QueryBuilder':
        """Add an AND WHERE condition."""
        condition = {
            'field': field,
            'operator': operator,
            'value': value,
            'operator': 'AND'
        }
        self.conditions.append(condition)
        return self
    
    def or_where(self, field: str, operator: str, value: str) -> 'QueryBuilder':
        """Add an OR WHERE condition."""
        condition = {
            'field': field,
            'operator': operator,
            'value': value,
            'operator': 'OR'
        }
        self.conditions.append(condition)
        return self
    
    def limit(self, count: int) -> 'QueryBuilder':
        """Set the result limit."""
        self.limit = count
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final query."""
        return {
            'type': 'FIND',
            'conditions': self.conditions,
            'limit': self.limit
        }
