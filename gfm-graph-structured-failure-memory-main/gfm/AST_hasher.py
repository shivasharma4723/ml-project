"""
AST-based Hashing Engine for Error/Action Signatures
"""

import ast
import hashlib
import inspect
from typing import Dict, Any, Optional, Union
import json


class ASTHasher:
    """
    Generates unique fingerprints for code patterns and API calls using AST parsing.
    Enables detection of similar error patterns across different executions.
    """
    
    def __init__(self, hash_algorithm: str = "sha256"):
        """
        Initialize the AST Hasher.
        
        Args:
            hash_algorithm: Hash algorithm to use (md5, sha1, sha256, etc.)
        """
        self.hash_algorithm = hash_algorithm
        self.hash_func = getattr(hashlib, hash_algorithm)
    
    def hash_code(self, code: str) -> str:
        """
        Generate hash for a code snippet using AST structure.
        
        Args:
            code: Python code string
            
        Returns:
            Hash string representing the code structure
        """
        try:
            tree = ast.parse(code)
            ast_string = self._ast_to_string(tree)
            return self._hash_string(ast_string)
        except SyntaxError:
            # Fallback to simple hash if code is invalid
            return self._hash_string(code)
    
    def hash_error(self, error_type: str, error_message: str, 
                   context: Dict[str, Any] = None) -> str:
        """
        Generate hash for an error pattern.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Execution context
            
        Returns:
            Hash string representing the error pattern
        """
        error_data = {
            'type': error_type,
            'message': self._normalize_error_message(error_message),
            'context_keys': sorted(context.keys()) if context else []
        }
        
        return self._hash_string(json.dumps(error_data, sort_keys=True))
    
    def hash_action(self, action_type: str, action_description: str,
                   parameters: Dict[str, Any] = None) -> str:
        """
        Generate hash for an action pattern.
        
        Args:
            action_type: Type of action
            action_description: Description of the action
            parameters: Action parameters
            
        Returns:
            Hash string representing the action pattern
        """
        action_data = {
            'type': action_type,
            'description': action_description.lower().strip(),
            'param_keys': sorted(parameters.keys()) if parameters else []
        }
        
        return self._hash_string(json.dumps(action_data, sort_keys=True))
    
    def hash_function_call(self, func_name: str, args: tuple, 
                          kwargs: Dict[str, Any] = None) -> str:
        """
        Generate hash for a function call pattern.
        
        Args:
            func_name: Name of the function being called
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Hash string representing the function call pattern
        """
        call_data = {
            'function': func_name,
            'arg_count': len(args),
            'kwarg_keys': sorted(kwargs.keys()) if kwargs else []
        }
        
        return self._hash_string(json.dumps(call_data, sort_keys=True))
    
    def hash_api_call(self, endpoint: str, method: str = "GET",
                     params: Dict[str, Any] = None) -> str:
        """
        Generate hash for an API call pattern.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            
        Returns:
            Hash string representing the API call pattern
        """
        api_data = {
            'endpoint': endpoint.lower(),
            'method': method.upper(),
            'param_keys': sorted(params.keys()) if params else []
        }
        
        return self._hash_string(json.dumps(api_data, sort_keys=True))
    
    def hash_state(self, state: Dict[str, Any]) -> str:
        """
        Generate hash for an agent state.
        
        Args:
            state: Agent state dictionary
            
        Returns:
            Hash string representing the state
        """
        # Normalize state by removing volatile fields
        normalized_state = {
            k: v for k, v in state.items()
            if k not in ['timestamp', 'iteration', 'token_usage']
        }
        
        return self._hash_string(json.dumps(normalized_state, sort_keys=True))
    
    def compare_code_similarity(self, code1: str, code2: str) -> float:
        """
        Compare similarity between two code snippets.
        
        Args:
            code1: First code snippet
            code2: Second code snippet
            
        Returns:
            Similarity score between 0 and 1
        """
        hash1 = self.hash_code(code1)
        hash2 = self.hash_code(code2)
        
        # Simple hash comparison
        if hash1 == hash2:
            return 1.0
        
        # Character-level similarity
        set1 = set(hash1)
        set2 = set(hash2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _ast_to_string(self, tree: ast.AST) -> str:
        """
        Convert AST to a canonical string representation.
        
        Args:
            tree: AST node
            
        Returns:
            String representation of the AST structure
        """
        class ASTVisitor(ast.NodeVisitor):
            def __init__(self):
                self.structure = []
            
            def visit(self, node):
                node_type = node.__class__.__name__
                self.structure.append(node_type)
                
                # Add relevant attributes based on node type
                if isinstance(node, ast.FunctionDef):
                    self.structure.append(node.name)
                elif isinstance(node, ast.Name):
                    self.structure.append(node.id)
                elif isinstance(node, ast.Constant):
                    self.structure.append(str(type(node.value).__name__))
                
                # Visit child nodes using the parent class method
                ast.NodeVisitor.generic_visit(self, node)
        
        visitor = ASTVisitor()
        visitor.visit(tree)
        return '|'.join(visitor.structure)
    
    def _normalize_error_message(self, message: str) -> str:
        """
        Normalize error message by removing variable-specific content.
        
        Args:
            message: Raw error message
            
        Returns:
            Normalized error message
        """
        # Remove common variable patterns
        normalized = message
        normalized = normalized.replace("'", "")  # Remove quotes
        normalized = normalized.replace('"', '')  # Remove double quotes
        
        # Replace numbers with placeholder
        import re
        normalized = re.sub(r'\d+', 'N', normalized)
        
        # Replace common identifiers
        normalized = re.sub(r'\b[a-zA-Z_]\w*\b', 'X', normalized)
        
        return normalized.lower().strip()
    
    def _hash_string(self, string: str) -> str:
        """
        Hash a string using the configured algorithm.
        
        Args:
            string: String to hash
            
        Returns:
            Hexadecimal hash string
        """
        return self.hash_func(string.encode()).hexdigest()
    
    def get_code_structure(self, code: str) -> Dict[str, Any]:
        """
        Extract structural information from code.
        
        Args:
            code: Python code string
            
        Returns:
            Dictionary with structural information
        """
        try:
            tree = ast.parse(code)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
            
            return {
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'lines': len(code.split('\n')),
                'valid_syntax': True
            }
        except SyntaxError as e:
            return {
                'functions': [],
                'classes': [],
                'imports': [],
                'lines': len(code.split('\n')),
                'valid_syntax': False,
                'syntax_error': str(e)
            }
