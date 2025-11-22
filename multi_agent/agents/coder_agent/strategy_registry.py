"""
Strategy Registry - Utility for managing uniquely named strategy files

Provides functionality to:
- Parse unique filenames and extract metadata
- Query strategies by workflow, task, or date
- Track strategy lineage and versions
- Generate file inventories
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


@dataclass
class StrategyMetadata:
    """Metadata extracted from unique filename."""
    filename: str
    filepath: Path
    timestamp: datetime
    workflow_id: str
    task_id: str
    descriptive_name: str
    file_size: int
    created_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'filename': self.filename,
            'filepath': str(self.filepath),
            'timestamp': self.timestamp.isoformat(),
            'workflow_id': self.workflow_id,
            'task_id': self.task_id,
            'descriptive_name': self.descriptive_name,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat()
        }


class StrategyRegistry:
    """
    Registry for managing uniquely named strategy files.
    
    Filename format: {timestamp}_{workflow_id}_{task_id}_{descriptive_name}.py
    Example: 20251121_143052_wf_abc123_task_data_loading_rsi_strategy.py
    """
    
    def __init__(self, codes_dir: Optional[Path] = None):
        """
        Initialize registry.
        
        Args:
            codes_dir: Directory containing strategy files
        """
        self.codes_dir = codes_dir or Path.cwd() / 'Backtest' / 'codes'
        self.codes_dir.mkdir(parents=True, exist_ok=True)
        
        # Regex pattern for parsing filenames
        self.filename_pattern = re.compile(
            r'^(\d{8}_\d{6})_([^_]+(?:_[^_]+)?)_([^_]+(?:_[^_]+)?)_(.+)\.py$'
        )
    
    def parse_filename(self, filename: str) -> Optional[StrategyMetadata]:
        """
        Parse unique filename and extract metadata.
        
        Args:
            filename: Strategy filename
            
        Returns:
            StrategyMetadata or None if parsing fails
        """
        match = self.filename_pattern.match(filename)
        if not match:
            return None
        
        timestamp_str, workflow_id, task_id, desc_name = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            return None
        
        filepath = self.codes_dir / filename
        
        metadata = StrategyMetadata(
            filename=filename,
            filepath=filepath,
            timestamp=timestamp,
            workflow_id=workflow_id,
            task_id=task_id,
            descriptive_name=desc_name,
            file_size=filepath.stat().st_size if filepath.exists() else 0,
            created_at=datetime.fromtimestamp(filepath.stat().st_ctime) if filepath.exists() else timestamp
        )
        
        return metadata
    
    def scan_directory(self) -> List[StrategyMetadata]:
        """
        Scan codes directory and parse all strategy files.
        
        Returns:
            List of StrategyMetadata for all parsed files
        """
        strategies = []
        
        for filepath in self.codes_dir.glob("*.py"):
            if filepath.name.startswith('__') or filepath.name == 'strategy_template_adapter_driven.py':
                continue
            
            metadata = self.parse_filename(filepath.name)
            if metadata:
                strategies.append(metadata)
        
        return strategies
    
    def get_by_workflow(self, workflow_id: str) -> List[StrategyMetadata]:
        """
        Get all strategies for a specific workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of matching strategies, sorted by timestamp
        """
        strategies = self.scan_directory()
        
        # Match full or shortened workflow ID
        matching = [
            s for s in strategies 
            if s.workflow_id == workflow_id or workflow_id in s.workflow_id
        ]
        
        return sorted(matching, key=lambda s: s.timestamp)
    
    def get_by_task(self, task_id: str) -> List[StrategyMetadata]:
        """
        Get all strategies for a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of matching strategies, sorted by timestamp
        """
        strategies = self.scan_directory()
        
        matching = [
            s for s in strategies 
            if s.task_id == task_id or task_id in s.task_id
        ]
        
        return sorted(matching, key=lambda s: s.timestamp)
    
    def get_by_date_range(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[StrategyMetadata]:
        """
        Get strategies within a date range.
        
        Args:
            start_date: Start datetime (inclusive)
            end_date: End datetime (inclusive)
            
        Returns:
            List of matching strategies, sorted by timestamp
        """
        strategies = self.scan_directory()
        
        if start_date:
            strategies = [s for s in strategies if s.timestamp >= start_date]
        
        if end_date:
            strategies = [s for s in strategies if s.timestamp <= end_date]
        
        return sorted(strategies, key=lambda s: s.timestamp)
    
    def get_latest_by_workflow(self, workflow_id: str) -> Optional[StrategyMetadata]:
        """
        Get the most recent strategy for a workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Latest StrategyMetadata or None
        """
        strategies = self.get_by_workflow(workflow_id)
        return strategies[-1] if strategies else None
    
    def get_latest_by_task(self, task_id: str) -> Optional[StrategyMetadata]:
        """
        Get the most recent strategy for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Latest StrategyMetadata or None
        """
        strategies = self.get_by_task(task_id)
        return strategies[-1] if strategies else None
    
    def search_by_description(self, search_term: str) -> List[StrategyMetadata]:
        """
        Search strategies by descriptive name.
        
        Args:
            search_term: Term to search for in descriptive names
            
        Returns:
            List of matching strategies
        """
        strategies = self.scan_directory()
        search_lower = search_term.lower()
        
        matching = [
            s for s in strategies 
            if search_lower in s.descriptive_name.lower()
        ]
        
        return sorted(matching, key=lambda s: s.timestamp, reverse=True)
    
    def generate_inventory(self, output_file: Optional[Path] = None) -> Dict:
        """
        Generate comprehensive inventory of all strategies.
        
        Args:
            output_file: Optional path to save JSON inventory
            
        Returns:
            Inventory dictionary
        """
        strategies = self.scan_directory()
        
        inventory = {
            'generated_at': datetime.now().isoformat(),
            'total_strategies': len(strategies),
            'strategies': [s.to_dict() for s in strategies],
            'by_workflow': self._group_by_workflow(strategies),
            'by_task': self._group_by_task(strategies),
            'by_date': self._group_by_date(strategies)
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(inventory, f, indent=2)
        
        return inventory
    
    def _group_by_workflow(self, strategies: List[StrategyMetadata]) -> Dict:
        """Group strategies by workflow ID."""
        grouped = {}
        for s in strategies:
            if s.workflow_id not in grouped:
                grouped[s.workflow_id] = []
            grouped[s.workflow_id].append(s.filename)
        return grouped
    
    def _group_by_task(self, strategies: List[StrategyMetadata]) -> Dict:
        """Group strategies by task ID."""
        grouped = {}
        for s in strategies:
            if s.task_id not in grouped:
                grouped[s.task_id] = []
            grouped[s.task_id].append(s.filename)
        return grouped
    
    def _group_by_date(self, strategies: List[StrategyMetadata]) -> Dict:
        """Group strategies by date."""
        grouped = {}
        for s in strategies:
            date_key = s.timestamp.strftime('%Y-%m-%d')
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(s.filename)
        return grouped
    
    def print_summary(self):
        """Print human-readable summary of registry."""
        strategies = self.scan_directory()
        
        print(f"\n{'='*70}")
        print(f"Strategy Registry Summary")
        print(f"{'='*70}")
        print(f"Directory: {self.codes_dir}")
        print(f"Total Strategies: {len(strategies)}")
        
        if not strategies:
            print("\nNo strategies found.")
            return
        
        # Group by workflow
        workflows = self._group_by_workflow(strategies)
        print(f"\nWorkflows: {len(workflows)}")
        for wf_id, files in sorted(workflows.items()):
            print(f"  {wf_id}: {len(files)} strategies")
        
        # Recent strategies
        print(f"\nRecent Strategies (last 5):")
        recent = sorted(strategies, key=lambda s: s.timestamp, reverse=True)[:5]
        for s in recent:
            print(f"  {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {s.filename}")
        
        print(f"{'='*70}\n")


def main():
    """CLI utility for strategy registry."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Strategy Registry Utility')
    parser.add_argument('--codes-dir', type=Path, help='Directory containing strategy files')
    parser.add_argument('--workflow', help='List strategies for workflow')
    parser.add_argument('--task', help='List strategies for task')
    parser.add_argument('--search', help='Search by description')
    parser.add_argument('--inventory', action='store_true', help='Generate inventory')
    parser.add_argument('--output', type=Path, help='Output file for inventory')
    
    args = parser.parse_args()
    
    registry = StrategyRegistry(args.codes_dir)
    
    if args.workflow:
        strategies = registry.get_by_workflow(args.workflow)
        print(f"\nStrategies for workflow '{args.workflow}':")
        for s in strategies:
            print(f"  {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {s.filename}")
    
    elif args.task:
        strategies = registry.get_by_task(args.task)
        print(f"\nStrategies for task '{args.task}':")
        for s in strategies:
            print(f"  {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {s.filename}")
    
    elif args.search:
        strategies = registry.search_by_description(args.search)
        print(f"\nStrategies matching '{args.search}':")
        for s in strategies:
            print(f"  {s.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {s.filename}")
    
    elif args.inventory:
        inventory = registry.generate_inventory(args.output)
        print(f"\nInventory generated: {inventory['total_strategies']} strategies")
        if args.output:
            print(f"Saved to: {args.output}")
    
    else:
        registry.print_summary()


if __name__ == '__main__':
    main()
