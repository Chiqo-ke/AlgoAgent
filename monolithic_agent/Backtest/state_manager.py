"""
Strategy State Management
=========================

Persistent state tracking for strategy lifecycle using SQLModel.

Features:
- Track strategy status across the pipeline
- Record attempts, errors, and results
- Enable retry logic and debugging
- Support for concurrent operations
- Audit trail for all state changes

Version: 1.0.0
"""

from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json
from pathlib import Path


class StrategyStatus(str, Enum):
    """Strategy lifecycle status"""
    DISCOVERED = "discovered"  # JSON found, no Python yet
    QUEUED = "queued"  # Queued for generation
    GENERATING = "generating"  # Code generation in progress
    GENERATED = "generated"  # Code generated, not tested
    TESTING = "testing"  # Tests running
    FIXING = "fixing"  # Auto-fix in progress
    READY = "ready"  # Tests passed, ready for use
    FAILED = "failed"  # Failed after max retries
    DEPLOYED = "deployed"  # Deployed to production
    ARCHIVED = "archived"  # Archived/deprecated


class StrategyRecord(SQLModel, table=True):
    """
    Persistent record for strategy lifecycle tracking
    """
    __tablename__ = "strategies"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    json_path: str
    py_path: Optional[str] = None
    status: str = Field(default=StrategyStatus.DISCOVERED.value, index=True)
    
    # Attempt tracking
    generation_attempts: int = Field(default=0)
    test_attempts: int = Field(default=0)
    fix_attempts: int = Field(default=0)
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = Field(default=0)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_generation_at: Optional[datetime] = None
    last_test_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    
    # Results
    last_backtest_results: Optional[str] = None  # JSON string
    
    # Metadata
    version: str = Field(default="1.0.0")
    tags: Optional[str] = None  # JSON string array
    strategy_metadata: Optional[str] = None  # JSON string for flexible metadata (renamed from 'metadata' to avoid SQLModel conflict)


class JobQueue(SQLModel, table=True):
    """
    Job queue for async strategy operations
    """
    __tablename__ = "job_queue"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(index=True, unique=True)
    strategy_name: str = Field(index=True)
    job_type: str  # generate, test, fix, backtest
    status: str = Field(default="pending", index=True)  # pending, running, completed, failed
    priority: int = Field(default=0)
    
    # Job details
    payload: Optional[str] = None  # JSON string
    result: Optional[str] = None  # JSON string
    error: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Retry logic
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)


class AuditLog(SQLModel, table=True):
    """
    Audit log for all state changes and operations
    """
    __tablename__ = "audit_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    
    # What happened
    event_type: str = Field(index=True)  # status_change, generation, test, fix, deploy
    strategy_name: str = Field(index=True)
    
    # Details
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    details: Optional[str] = None  # JSON string
    
    # Who/What
    actor: Optional[str] = None  # user, system, ai_agent
    session_id: Optional[str] = None


class StateManager:
    """
    Manages persistent state for strategy lifecycle
    """
    
    def __init__(self, db_path: str = "state.db"):
        """
        Initialize state manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        
        # Create tables if they don't exist
        SQLModel.metadata.create_all(self.engine)
    
    def register_strategy(
        self,
        name: str,
        json_path: str,
        py_path: Optional[str] = None
    ) -> StrategyRecord:
        """
        Register a new strategy or update existing
        
        Args:
            name: Strategy name
            json_path: Path to JSON definition
            py_path: Path to Python implementation (if exists)
            
        Returns:
            StrategyRecord
        """
        with Session(self.engine) as session:
            # Check if exists
            statement = select(StrategyRecord).where(StrategyRecord.name == name)
            existing = session.exec(statement).first()
            
            if existing:
                # Update paths
                existing.json_path = json_path
                if py_path:
                    existing.py_path = py_path
                existing.updated_at = datetime.now()
                session.add(existing)
                session.commit()
                session.refresh(existing)
                
                self._audit_log(
                    session,
                    event_type="strategy_updated",
                    strategy_name=name,
                    details={"json_path": json_path, "py_path": py_path}
                )
                
                return existing
            else:
                # Create new
                strategy = StrategyRecord(
                    name=name,
                    json_path=json_path,
                    py_path=py_path,
                    status=StrategyStatus.DISCOVERED.value if not py_path else StrategyStatus.GENERATED.value
                )
                session.add(strategy)
                session.commit()
                session.refresh(strategy)
                
                self._audit_log(
                    session,
                    event_type="strategy_registered",
                    strategy_name=name,
                    details={"json_path": json_path, "py_path": py_path}
                )
                
                return strategy
    
    def update_status(
        self,
        name: str,
        status: StrategyStatus,
        error: Optional[str] = None
    ) -> StrategyRecord:
        """
        Update strategy status
        
        Args:
            name: Strategy name
            status: New status
            error: Optional error message
            
        Returns:
            Updated StrategyRecord
        """
        with Session(self.engine) as session:
            statement = select(StrategyRecord).where(StrategyRecord.name == name)
            strategy = session.exec(statement).first()
            
            if not strategy:
                raise ValueError(f"Strategy {name} not found")
            
            old_status = strategy.status
            strategy.status = status.value
            strategy.updated_at = datetime.now()
            
            if error:
                strategy.last_error = error
                strategy.error_count += 1
            
            # Update specific timestamps
            if status == StrategyStatus.GENERATING:
                strategy.generation_attempts += 1
                strategy.last_generation_at = datetime.now()
            elif status == StrategyStatus.TESTING:
                strategy.test_attempts += 1
                strategy.last_test_at = datetime.now()
            elif status == StrategyStatus.FIXING:
                strategy.fix_attempts += 1
            elif status == StrategyStatus.READY:
                strategy.last_success_at = datetime.now()
            
            session.add(strategy)
            session.commit()
            session.refresh(strategy)
            
            self._audit_log(
                session,
                event_type="status_change",
                strategy_name=name,
                old_value=old_status,
                new_value=status.value,
                details={"error": error} if error else None
            )
            
            return strategy
    
    def enqueue_job(
        self,
        job_id: str,
        strategy_name: str,
        job_type: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> JobQueue:
        """
        Enqueue a job for async processing
        
        Args:
            job_id: Unique job identifier
            strategy_name: Strategy name
            job_type: Type of job (generate, test, fix, backtest)
            payload: Job payload as dict
            priority: Priority (higher = more urgent)
            
        Returns:
            JobQueue record
        """
        with Session(self.engine) as session:
            job = JobQueue(
                job_id=job_id,
                strategy_name=strategy_name,
                job_type=job_type,
                priority=priority,
                payload=json.dumps(payload) if payload else None
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            
            self._audit_log(
                session,
                event_type="job_enqueued",
                strategy_name=strategy_name,
                details={"job_id": job_id, "job_type": job_type}
            )
            
            return job
    
    def get_next_job(self, job_type: Optional[str] = None) -> Optional[JobQueue]:
        """
        Get next pending job
        
        Args:
            job_type: Filter by job type (optional)
            
        Returns:
            Next JobQueue record or None
        """
        with Session(self.engine) as session:
            statement = select(JobQueue).where(JobQueue.status == "pending")
            
            if job_type:
                statement = statement.where(JobQueue.job_type == job_type)
            
            statement = statement.order_by(JobQueue.priority.desc(), JobQueue.created_at)
            
            job = session.exec(statement).first()
            
            if job:
                # Mark as running
                job.status = "running"
                job.started_at = datetime.now()
                job.attempts += 1
                session.add(job)
                session.commit()
                session.refresh(job)
            
            return job
    
    def complete_job(
        self,
        job_id: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Mark job as completed or failed
        
        Args:
            job_id: Job identifier
            result: Result payload as dict
            error: Error message if failed
        """
        with Session(self.engine) as session:
            statement = select(JobQueue).where(JobQueue.job_id == job_id)
            job = session.exec(statement).first()
            
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            job.completed_at = datetime.now()
            
            if error:
                job.status = "failed"
                job.error = error
                
                # Retry if attempts remaining
                if job.attempts < job.max_attempts:
                    job.status = "pending"
                    job.started_at = None
            else:
                job.status = "completed"
                job.result = json.dumps(result) if result else None
            
            session.add(job)
            session.commit()
    
    def get_strategy(self, name: str) -> Optional[StrategyRecord]:
        """Get strategy by name"""
        with Session(self.engine) as session:
            statement = select(StrategyRecord).where(StrategyRecord.name == name)
            return session.exec(statement).first()
    
    def list_strategies(
        self,
        status: Optional[StrategyStatus] = None,
        limit: Optional[int] = None
    ) -> List[StrategyRecord]:
        """
        List strategies with optional filtering
        
        Args:
            status: Filter by status
            limit: Max results
            
        Returns:
            List of StrategyRecord
        """
        with Session(self.engine) as session:
            statement = select(StrategyRecord)
            
            if status:
                statement = statement.where(StrategyRecord.status == status.value)
            
            statement = statement.order_by(StrategyRecord.updated_at.desc())
            
            if limit:
                statement = statement.limit(limit)
            
            return list(session.exec(statement).all())
    
    def get_audit_log(
        self,
        strategy_name: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit log entries
        
        Args:
            strategy_name: Filter by strategy
            event_type: Filter by event type
            limit: Max results
            
        Returns:
            List of AuditLog entries
        """
        with Session(self.engine) as session:
            statement = select(AuditLog)
            
            if strategy_name:
                statement = statement.where(AuditLog.strategy_name == strategy_name)
            
            if event_type:
                statement = statement.where(AuditLog.event_type == event_type)
            
            statement = statement.order_by(AuditLog.timestamp.desc()).limit(limit)
            
            return list(session.exec(statement).all())
    
    def _audit_log(
        self,
        session: Session,
        event_type: str,
        strategy_name: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        actor: str = "system"
    ):
        """Internal method to add audit log entry"""
        log = AuditLog(
            event_type=event_type,
            strategy_name=strategy_name,
            old_value=old_value,
            new_value=new_value,
            details=json.dumps(details) if details else None,
            actor=actor
        )
        session.add(log)


# CLI for state management
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Strategy state management CLI")
    parser.add_argument("--db", type=str, default="state.db", help="Database path")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List strategies")
    list_parser.add_argument("--status", type=str, choices=[s.value for s in StrategyStatus])
    list_parser.add_argument("--limit", type=int, default=50)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Get strategy status")
    status_parser.add_argument("name", type=str, help="Strategy name")
    
    # Audit command
    audit_parser = subparsers.add_parser("audit", help="View audit log")
    audit_parser.add_argument("--strategy", type=str, help="Filter by strategy")
    audit_parser.add_argument("--event", type=str, help="Filter by event type")
    audit_parser.add_argument("--limit", type=int, default=50)
    
    # Jobs command
    jobs_parser = subparsers.add_parser("jobs", help="List pending jobs")
    jobs_parser.add_argument("--type", type=str, help="Filter by job type")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    manager = StateManager(args.db)
    
    if args.command == "list":
        status_filter = StrategyStatus(args.status) if args.status else None
        strategies = manager.list_strategies(status=status_filter, limit=args.limit)
        
        print(f"\n{'Name':<30} {'Status':<15} {'Attempts':<10} {'Updated':<20}")
        print("-" * 80)
        for s in strategies:
            total_attempts = s.generation_attempts + s.test_attempts + s.fix_attempts
            print(f"{s.name:<30} {s.status:<15} {total_attempts:<10} {s.updated_at.strftime('%Y-%m-%d %H:%M:%S'):<20}")
        
        print(f"\nTotal: {len(strategies)} strategies")
    
    elif args.command == "status":
        strategy = manager.get_strategy(args.name)
        if not strategy:
            print(f"Strategy '{args.name}' not found")
            sys.exit(1)
        
        print(f"\nStrategy: {strategy.name}")
        print(f"Status: {strategy.status}")
        print(f"JSON Path: {strategy.json_path}")
        print(f"Python Path: {strategy.py_path or 'N/A'}")
        print(f"\nAttempts:")
        print(f"  Generation: {strategy.generation_attempts}")
        print(f"  Testing: {strategy.test_attempts}")
        print(f"  Fixing: {strategy.fix_attempts}")
        print(f"  Errors: {strategy.error_count}")
        
        if strategy.last_error:
            print(f"\nLast Error:\n{strategy.last_error}")
    
    elif args.command == "audit":
        logs = manager.get_audit_log(
            strategy_name=args.strategy,
            event_type=args.event,
            limit=args.limit
        )
        
        print(f"\n{'Timestamp':<20} {'Event':<20} {'Strategy':<30}")
        print("-" * 80)
        for log in logs:
            print(f"{log.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20} {log.event_type:<20} {log.strategy_name:<30}")
        
        print(f"\nTotal: {len(logs)} log entries")
    
    elif args.command == "jobs":
        with Session(manager.engine) as session:
            statement = select(JobQueue).where(JobQueue.status.in_(["pending", "running"]))
            if args.type:
                statement = statement.where(JobQueue.job_type == args.type)
            statement = statement.order_by(JobQueue.priority.desc(), JobQueue.created_at)
            jobs = session.exec(statement).all()
            
            print(f"\n{'Job ID':<15} {'Type':<15} {'Strategy':<30} {'Status':<10} {'Priority':<8}")
            print("-" * 90)
            for job in jobs:
                print(f"{job.job_id:<15} {job.job_type:<15} {job.strategy_name:<30} {job.status:<10} {job.priority:<8}")
            
            print(f"\nTotal: {len(jobs)} jobs")
