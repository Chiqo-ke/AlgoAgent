"""
Contract and Schema Validation Tools

Validates todo lists, contracts, and test reports against JSON schemas.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from jsonschema import validate, ValidationError, Draft7Validator
from datetime import datetime


class SchemaValidator:
    """Validates JSON documents against schemas."""
    
    def __init__(self, schemas_dir: Path = None):
        """Initialize validator with schema directory."""
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent
        
        self.schemas_dir = Path(schemas_dir)
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load all schemas from the schemas directory."""
        schemas = {}
        schema_files = {
            'todo': 'todo_schema.json',
            'contract': 'contract_schema.json',
            'test_report': 'test_report_schema.json'
        }
        
        for name, filename in schema_files.items():
            schema_path = self.schemas_dir / filename
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schemas[name] = json.load(f)
        
        return schemas
    
    def validate_todo_list(self, todo_list: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a todo list against the schema.
        
        Args:
            todo_list: Todo list dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self._validate(todo_list, 'todo')
    
    def validate_contract(self, contract: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a contract against the schema.
        
        Args:
            contract: Contract dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self._validate(contract, 'contract')
    
    def validate_test_report(self, report: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a test report against the schema.
        
        Args:
            report: Test report dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self._validate(report, 'test_report')
    
    def _validate(self, data: Dict[str, Any], schema_name: str) -> Tuple[bool, List[str]]:
        """Internal validation method."""
        if schema_name not in self.schemas:
            return False, [f"Schema '{schema_name}' not found"]
        
        schema = self.schemas[schema_name]
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        if not errors:
            return True, []
        
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            error_messages.append(f"{path}: {error.message}")
        
        return False, error_messages
    
    def validate_dependencies(self, todo_list: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that task dependencies are valid (no cycles, all tasks exist).
        
        Args:
            todo_list: Todo list dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        items = todo_list.get('items', [])
        task_ids = {item['id'] for item in items}
        errors = []
        
        # Check all dependencies exist
        for item in items:
            deps = item.get('dependencies', [])
            for dep in deps:
                if dep not in task_ids:
                    errors.append(f"Task {item['id']} depends on non-existent task {dep}")
        
        # Check for cycles using DFS
        def has_cycle(task_id: str, visited: set, stack: set) -> bool:
            visited.add(task_id)
            stack.add(task_id)
            
            # Find this task
            task = next((t for t in items if t['id'] == task_id), None)
            if not task:
                return False
            
            for dep in task.get('dependencies', []):
                if dep not in visited:
                    if has_cycle(dep, visited, stack):
                        return True
                elif dep in stack:
                    return True
            
            stack.remove(task_id)
            return False
        
        visited = set()
        for item in items:
            if item['id'] not in visited:
                if has_cycle(item['id'], visited, set()):
                    errors.append(f"Circular dependency detected involving task {item['id']}")
        
        return len(errors) == 0, errors


def validate_todo_file(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Validate a todo list JSON file.
    
    Args:
        filepath: Path to todo list JSON file
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        with open(filepath, 'r') as f:
            todo_list = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    except FileNotFoundError:
        return False, [f"File not found: {filepath}"]
    
    validator = SchemaValidator()
    
    # Schema validation
    is_valid, errors = validator.validate_todo_list(todo_list)
    if not is_valid:
        return False, errors
    
    # Dependency validation
    is_valid, dep_errors = validator.validate_dependencies(todo_list)
    if not is_valid:
        errors.extend(dep_errors)
        return False, errors
    
    return True, []


def validate_contract_file(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Validate a contract JSON file.
    
    Args:
        filepath: Path to contract JSON file
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        with open(filepath, 'r') as f:
            contract = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"]
    except FileNotFoundError:
        return False, [f"File not found: {filepath}"]
    
    validator = SchemaValidator()
    return validator.validate_contract(contract)


def main():
    """CLI for validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate todo lists and contracts')
    parser.add_argument('file', type=Path, help='JSON file to validate')
    parser.add_argument('--type', choices=['todo', 'contract', 'test_report'],
                       default='todo', help='Type of file to validate')
    
    args = parser.parse_args()
    
    if args.type == 'todo':
        is_valid, errors = validate_todo_file(args.file)
    elif args.type == 'contract':
        is_valid, errors = validate_contract_file(args.file)
    else:
        with open(args.file, 'r') as f:
            data = json.load(f)
        validator = SchemaValidator()
        is_valid, errors = validator.validate_test_report(data)
    
    if is_valid:
        print(f"✅ {args.file} is valid")
        return 0
    else:
        print(f"❌ {args.file} is invalid:")
        for error in errors:
            print(f"  - {error}")
        return 1


if __name__ == '__main__':
    exit(main())
