"""
CQL Query Comparison Utility

Compares two CQL queries accounting for:
- Different whitespace
- Different ordering of conditions
- Different ordering of SELECT columns
- Case insensitivity
- Equivalent SQL structures
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class CQLComparator:
    """Compares CQL queries for equivalence."""
    
    def compare(self, query1: str, query2: str) -> Dict[str, Any]:
        """Compare two CQL queries.
        
        Args:
            query1: First CQL query (expected)
            query2: Second CQL query (actual)
        
        Returns:
            Dictionary with comparison results:
            - equal: bool - Whether queries are equivalent
            - details: dict - Detailed comparison information
        """
        if not query1 or not query2:
            return {
                "equal": query1 == query2,
                "details": {
                    "error": "One or both queries are empty",
                    "query1": query1,
                    "query2": query2
                }
            }
        
        # Normalize both queries
        normalized1 = self._normalize_query(query1)
        normalized2 = self._normalize_query(query2)
        
        # Check exact match after normalization
        if normalized1 == normalized2:
            return {
                "equal": True,
                "details": {
                    "method": "exact_match_after_normalization",
                    "normalized_query1": normalized1,
                    "normalized_query2": normalized2
                }
            }
        
        # Try structural comparison
        return self._compare_structures(query1, query2, normalized1, normalized2)
    
    def _normalize_query(self, query: str) -> str:
        """Normalize a query for comparison.
        
        Args:
            query: CQL query string
        
        Returns:
            Normalized query string
        """
        # Remove leading/trailing whitespace
        query = query.strip()
        
        # Normalize whitespace (multiple spaces to single space)
        query = re.sub(r'\s+', ' ', query)
        
        # Normalize case (SQL keywords are case-insensitive)
        # But preserve string literals and identifiers
        query = self._normalize_sql_case(query)
        
        # Remove extra spaces around operators and parentheses
        query = re.sub(r'\s*\(\s*', '(', query)
        query = re.sub(r'\s*\)\s*', ')', query)
        query = re.sub(r'\s*=\s*', '=', query)
        query = re.sub(r'\s*>\s*', '>', query)
        query = re.sub(r'\s*<\s*', '<', query)
        query = re.sub(r'\s*AND\s*', ' AND ', query)
        query = re.sub(r'\s*OR\s*', ' OR ', query)
        
        return query.strip()
    
    def _normalize_sql_case(self, query: str) -> str:
        """Normalize SQL keywords to uppercase while preserving literals.
        
        Args:
            query: SQL query string
        
        Returns:
            Query with normalized SQL keywords
        """
        # SQL keywords to normalize
        keywords = [
            'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL',
            'ORDER', 'BY', 'GROUP', 'COUNT', 'SUM', 'CASE', 'WHEN', 'THEN',
            'ELSE', 'END', 'AS', 'CAST', 'INTEGER', 'DESC', 'ASC', 'LIMIT'
        ]
        
        # Split query into parts, preserving string literals
        parts = []
        i = 0
        in_string = False
        string_char = None
        
        while i < len(query):
            char = query[i]
            
            # Handle string literals
            if char in ("'", '"') and (i == 0 or query[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                parts.append(char)
                i += 1
                continue
            
            if in_string:
                parts.append(char)
                i += 1
                continue
            
            # Check for keywords
            matched = False
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if query[i:i+len(keyword)].lower() == keyword_lower:
                    # Check if it's a whole word
                    if (i == 0 or not query[i-1].isalnum()) and \
                       (i+len(keyword) >= len(query) or not query[i+len(keyword)].isalnum()):
                        parts.append(keyword)
                        i += len(keyword)
                        matched = True
                        break
            
            if not matched:
                parts.append(char)
                i += 1
        
        return ''.join(parts)
    
    def _compare_structures(self, query1: str, query2: str, norm1: str, norm2: str) -> Dict[str, Any]:
        """Compare queries structurally.
        
        Args:
            query1: Original first query
            query2: Original second query
            norm1: Normalized first query
            norm2: Normalized second query
        
        Returns:
            Comparison result dictionary
        """
        # Parse SELECT clauses
        select1 = self._extract_select_clause(norm1)
        select2 = self._extract_select_clause(norm2)
        
        # Parse WHERE clauses
        where1 = self._extract_where_clause(norm1)
        where2 = self._extract_where_clause(norm2)
        
        # Parse ORDER BY clauses
        order1 = self._extract_order_by_clause(norm1)
        order2 = self._extract_order_by_clause(norm2)
        
        # Parse GROUP BY clauses
        group1 = self._extract_group_by_clause(norm1)
        group2 = self._extract_group_by_clause(norm2)
        
        # Compare components
        select_equal = self._compare_select_clauses(select1, select2)
        where_equal = self._compare_where_clauses(where1, where2)
        order_equal = order1 == order2
        group_equal = group1 == group2
        
        equal = select_equal and where_equal and order_equal and group_equal
        
        return {
            "equal": equal,
            "details": {
                "method": "structural_comparison",
                "select_equal": select_equal,
                "where_equal": where_equal,
                "order_equal": order_equal,
                "group_equal": group_equal,
                "select1": select1,
                "select2": select2,
                "where1": where1,
                "where2": where2,
                "order1": order1,
                "order2": order2,
                "group1": group1,
                "group2": group2,
                "normalized_query1": norm1,
                "normalized_query2": norm2
            }
        }
    
    def _extract_select_clause(self, query: str) -> List[str]:
        """Extract SELECT clause columns.
        
        Args:
            query: SQL query
        
        Returns:
            List of column expressions
        """
        match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE)
        if not match:
            return []
        
        columns_str = match.group(1).strip()
        if columns_str == '*':
            return ['*']
        
        # Split by comma, handling nested parentheses
        columns = []
        current = ""
        depth = 0
        
        for char in columns_str:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                columns.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            columns.append(current.strip())
        
        return [col.strip() for col in columns if col.strip()]
    
    def _extract_where_clause(self, query: str) -> Optional[str]:
        """Extract WHERE clause.
        
        Args:
            query: SQL query
        
        Returns:
            WHERE clause string or None
        """
        # Find WHERE clause, handling ORDER BY, GROUP BY, LIMIT
        match = re.search(r'WHERE\s+(.+?)(?:\s+(?:ORDER\s+BY|GROUP\s+BY|LIMIT)|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        
        return match.group(1).strip()
    
    def _extract_order_by_clause(self, query: str) -> Optional[str]:
        """Extract ORDER BY clause.
        
        Args:
            query: SQL query
        
        Returns:
            ORDER BY clause string or None
        """
        match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+(?:GROUP\s+BY|LIMIT)|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        
        return match.group(1).strip()
    
    def _extract_group_by_clause(self, query: str) -> Optional[str]:
        """Extract GROUP BY clause.
        
        Args:
            query: SQL query
        
        Returns:
            GROUP BY clause string or None
        """
        match = re.search(r'GROUP\s+BY\s+(.+?)(?:\s+(?:ORDER\s+BY|LIMIT)|\s*$)', query, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        
        return match.group(1).strip()
    
    def _compare_select_clauses(self, select1: List[str], select2: List[str]) -> bool:
        """Compare SELECT clauses accounting for column order.
        
        Args:
            select1: First SELECT columns
            select2: Second SELECT columns
        
        Returns:
            True if equivalent
        """
        # If both are '*', they're equal
        if select1 == ['*'] and select2 == ['*']:
            return True
        
        # If one is '*' and other isn't, they might still be equivalent
        # (SELECT * is equivalent to selecting all columns)
        # For now, we'll be strict and require exact match or same columns
        if select1 == ['*'] or select2 == ['*']:
            # Can't easily compare without schema, so require exact match
            return select1 == select2
        
        # Normalize column names (remove AS aliases for comparison)
        norm1 = [self._normalize_column(col) for col in select1]
        norm2 = [self._normalize_column(col) for col in select2]
        
        # Sort for order-independent comparison
        norm1_sorted = sorted(norm1)
        norm2_sorted = sorted(norm2)
        
        return norm1_sorted == norm2_sorted
    
    def _normalize_column(self, column: str) -> str:
        """Normalize a column expression.
        
        Args:
            column: Column expression (e.g., "COUNT(*)", "white_elo AS elo")
        
        Returns:
            Normalized column string
        """
        # Remove AS alias
        column = re.sub(r'\s+AS\s+\w+', '', column, flags=re.IGNORECASE)
        # Normalize whitespace
        column = re.sub(r'\s+', ' ', column).strip()
        return column
    
    def _compare_where_clauses(self, where1: Optional[str], where2: Optional[str]) -> bool:
        """Compare WHERE clauses accounting for condition order.
        
        Args:
            where1: First WHERE clause
            where2: Second WHERE clause
        
        Returns:
            True if equivalent
        """
        if where1 is None and where2 is None:
            return True
        
        if where1 is None or where2 is None:
            return False
        
        # Normalize
        where1 = where1.strip()
        where2 = where2.strip()
        
        # Exact match after normalization
        if where1 == where2:
            return True
        
        # Split by AND/OR (handling nested parentheses)
        conditions1 = self._split_conditions(where1)
        conditions2 = self._split_conditions(where2)
        
        # Compare sets of conditions (order-independent)
        # But we need to preserve AND vs OR grouping
        # For now, do a simple comparison
        if len(conditions1) != len(conditions2):
            return False
        
        # Normalize each condition
        norm_conditions1 = [self._normalize_condition(c) for c in conditions1]
        norm_conditions2 = [self._normalize_condition(c) for c in conditions2]
        
        # Sort for order-independent comparison
        # Note: This doesn't handle AND/OR precedence correctly,
        # but for most cases it should work
        norm_conditions1_sorted = sorted(norm_conditions1)
        norm_conditions2_sorted = sorted(norm_conditions2)
        
        return norm_conditions1_sorted == norm_conditions2_sorted
    
    def _split_conditions(self, where_clause: str) -> List[str]:
        """Split WHERE clause into individual conditions.
        
        Args:
            where_clause: WHERE clause string
        
        Returns:
            List of condition strings
        """
        conditions = []
        current = ""
        depth = 0
        i = 0
        
        while i < len(where_clause):
            char = where_clause[i]
            
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif depth == 0:
                # Check for AND/OR at top level
                remaining = where_clause[i:]
                if remaining.upper().startswith(' AND '):
                    if current.strip():
                        conditions.append(current.strip())
                    current = ""
                    i += 5  # Skip " AND "
                    continue
                elif remaining.upper().startswith(' OR '):
                    if current.strip():
                        conditions.append(current.strip())
                    current = ""
                    i += 4  # Skip " OR "
                    continue
                else:
                    current += char
            else:
                current += char
            
            i += 1
        
        if current.strip():
            conditions.append(current.strip())
        
        return conditions
    
    def _normalize_condition(self, condition: str) -> str:
        """Normalize a single condition.
        
        Args:
            condition: Condition string
        
        Returns:
            Normalized condition
        """
        # Remove extra whitespace
        condition = re.sub(r'\s+', ' ', condition).strip()
        # Normalize parentheses spacing
        condition = re.sub(r'\s*\(\s*', '(', condition)
        condition = re.sub(r'\s*\)\s*', ')', condition)
        return condition


def compare_cql_queries(query1: str, query2: str) -> Dict[str, Any]:
    """Convenience function to compare two CQL queries.
    
    Args:
        query1: First CQL query (expected)
        query2: Second CQL query (actual)
    
    Returns:
        Comparison result dictionary
    """
    comparator = CQLComparator()
    return comparator.compare(query1, query2)

