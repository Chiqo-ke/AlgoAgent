"""
Secret scanner tool for detecting leaked API keys and credentials in artifacts.

Scans:
- Source code files
- Log files
- Test artifacts
- Configuration files

Uses regex patterns to detect common secret formats.
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
import json

logger = logging.getLogger(__name__)


class SecretFound(Exception):
    """Raised when secrets are found in artifacts."""
    
    def __init__(self, message: str, findings: List[Dict[str, Any]]):
        super().__init__(message)
        self.findings = findings


# Regex patterns for common secret formats
SECRET_PATTERNS = {
    'generic_api_key': {
        'pattern': r'(?i)(api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'description': 'Generic API key'
    },
    'gemini_key': {
        'pattern': r'AIza[0-9A-Za-z\-_]{35}',
        'description': 'Google/Gemini API key'
    },
    'openai_key': {
        'pattern': r'sk-[a-zA-Z0-9]{20,}',
        'description': 'OpenAI API key'
    },
    'anthropic_key': {
        'pattern': r'sk-ant-[a-zA-Z0-9\-_]{20,}',
        'description': 'Anthropic API key'
    },
    'aws_key': {
        'pattern': r'AKIA[0-9A-Z]{16}',
        'description': 'AWS Access Key'
    },
    'aws_secret': {
        'pattern': r'(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',
        'description': 'AWS Secret Key'
    },
    'jwt_token': {
        'pattern': r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
        'description': 'JWT Token'
    },
    'bearer_token': {
        'pattern': r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*',
        'description': 'Bearer Token'
    },
    'private_key': {
        'pattern': r'-----BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE KEY-----',
        'description': 'Private Key'
    },
    'connection_string': {
        'pattern': r'(?i)(mongodb|postgres|mysql|redis)://[^\s]+:[^\s]+@[^\s]+',
        'description': 'Database Connection String'
    }
}


# File extensions to scan
SCANNABLE_EXTENSIONS = {
    '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env',
    '.log', '.txt', '.md', '.csv', '.sh', '.ps1', '.bat'
}


# Patterns to whitelist (known false positives)
WHITELIST_PATTERNS = [
    r'example[_-]?key',
    r'test[_-]?key',
    r'fake[_-]?key',
    r'placeholder',
    r'your[_-]?api[_-]?key',
    r'xxx+',
    r'\*\*\*+',
]


class SecretScanner:
    """Scanner for detecting secrets in files and artifacts."""
    
    def __init__(
        self,
        patterns: Dict[str, Dict[str, str]] = None,
        whitelist: List[str] = None
    ):
        """
        Initialize secret scanner.
        
        Args:
            patterns: Custom secret patterns (uses defaults if None)
            whitelist: Custom whitelist patterns
        """
        self.patterns = patterns or SECRET_PATTERNS
        self.whitelist = whitelist or WHITELIST_PATTERNS
        
        # Compile patterns
        self.compiled_patterns = {
            name: re.compile(info['pattern'])
            for name, info in self.patterns.items()
        }
        
        self.compiled_whitelist = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.whitelist
        ]
        
        logger.info(f"Secret scanner initialized with {len(self.patterns)} patterns")
    
    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Scan a single file for secrets.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of findings with details
        """
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        # Check if file should be scanned
        if file_path.suffix not in SCANNABLE_EXTENSIONS:
            logger.debug(f"Skipping non-scannable file: {file_path}")
            return []
        
        try:
            content = file_path.read_text(errors='ignore')
            return self.scan_content(content, str(file_path))
            
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            return []
    
    def scan_content(
        self,
        content: str,
        source: str = "unknown"
    ) -> List[Dict[str, Any]]:
        """
        Scan text content for secrets.
        
        Args:
            content: Text content to scan
            source: Source identifier (file path, etc.)
            
        Returns:
            List of findings
        """
        findings = []
        
        for pattern_name, pattern_regex in self.compiled_patterns.items():
            matches = pattern_regex.finditer(content)
            
            for match in matches:
                secret = match.group(0)
                
                # Check whitelist
                if self._is_whitelisted(secret):
                    logger.debug(f"Whitelisted secret in {source}: {secret[:20]}...")
                    continue
                
                # Get line number
                line_num = content[:match.start()].count('\n') + 1
                
                # Get context (line content)
                lines = content.split('\n')
                context = lines[line_num - 1] if line_num <= len(lines) else ""
                
                finding = {
                    'type': pattern_name,
                    'description': self.patterns[pattern_name]['description'],
                    'secret': secret[:50] + '...' if len(secret) > 50 else secret,
                    'source': source,
                    'line': line_num,
                    'context': context[:100]
                }
                
                findings.append(finding)
                logger.warning(f"Secret found in {source}:{line_num} - {pattern_name}")
        
        return findings
    
    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        exclude_patterns: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan directory for secrets.
        
        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            exclude_patterns: Glob patterns to exclude
            
        Returns:
            List of all findings
        """
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return []
        
        exclude_patterns = exclude_patterns or [
            '__pycache__', '*.pyc', '.git', 'node_modules',
            '*.min.js', '*.bundle.js'
        ]
        
        all_findings = []
        
        # Get files to scan
        if recursive:
            files = directory.rglob('*')
        else:
            files = directory.glob('*')
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            # Check exclude patterns
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
            
            findings = self.scan_file(file_path)
            all_findings.extend(findings)
        
        return all_findings
    
    def scan_artifact_dir(self, artifact_dir: Path) -> Dict[str, Any]:
        """
        Scan test artifact directory.
        
        Args:
            artifact_dir: Path to artifact directory
            
        Returns:
            {
                'clean': bool,
                'findings': List[Dict],
                'files_scanned': int,
                'secrets_found': int
            }
        """
        logger.info(f"Scanning artifacts in {artifact_dir}")
        
        findings = self.scan_directory(artifact_dir, recursive=True)
        
        # Get unique files scanned
        files_scanned = len(set(f['source'] for f in findings)) if findings else 0
        
        result = {
            'clean': len(findings) == 0,
            'findings': findings,
            'files_scanned': files_scanned,
            'secrets_found': len(findings)
        }
        
        if not result['clean']:
            logger.error(
                f"Secret scan FAILED: {result['secrets_found']} secrets found "
                f"in {files_scanned} files"
            )
        else:
            logger.info(f"Secret scan PASSED: No secrets detected")
        
        return result
    
    def _is_whitelisted(self, secret: str) -> bool:
        """Check if secret matches whitelist patterns."""
        for pattern in self.compiled_whitelist:
            if pattern.search(secret):
                return True
        return False
    
    def generate_report(
        self,
        findings: List[Dict[str, Any]],
        output_path: Path
    ):
        """
        Generate JSON report of findings.
        
        Args:
            findings: List of findings
            output_path: Output file path
        """
        report = {
            'scan_date': str(Path.cwd()),
            'total_findings': len(findings),
            'findings_by_type': {},
            'findings': findings
        }
        
        # Group by type
        for finding in findings:
            finding_type = finding['type']
            if finding_type not in report['findings_by_type']:
                report['findings_by_type'][finding_type] = 0
            report['findings_by_type'][finding_type] += 1
        
        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Secret scan report written to {output_path}")


def scan_and_fail_on_secrets(artifact_dir: Path) -> bool:
    """
    Scan artifacts and fail if secrets found.
    
    Args:
        artifact_dir: Path to artifact directory
        
    Returns:
        True if clean, raises SecretFound if secrets detected
    """
    scanner = SecretScanner()
    result = scanner.scan_artifact_dir(artifact_dir)
    
    if not result['clean']:
        raise SecretFound(
            f"Secrets detected in artifacts: {result['secrets_found']} findings",
            findings=result['findings']
        )
    
    return True


def main():
    """CLI entry point for secret scanner."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan files for secrets')
    parser.add_argument('path', type=Path, help='File or directory to scan')
    parser.add_argument('--output', '-o', type=Path, help='Output report path')
    parser.add_argument('--fail-on-found', action='store_true',
                        help='Exit with error code if secrets found')
    
    args = parser.parse_args()
    
    scanner = SecretScanner()
    
    if args.path.is_file():
        findings = scanner.scan_file(args.path)
    else:
        findings = scanner.scan_directory(args.path)
    
    if args.output:
        scanner.generate_report(findings, args.output)
    
    # Print summary
    print(f"\nScan Results:")
    print(f"Files scanned: {len(set(f['source'] for f in findings)) if findings else 0}")
    print(f"Secrets found: {len(findings)}")
    
    if findings:
        print("\nFindings:")
        for finding in findings[:10]:  # Show first 10
            print(f"  - {finding['type']} in {finding['source']}:{finding['line']}")
        if len(findings) > 10:
            print(f"  ... and {len(findings) - 10} more")
    
    # Exit with error if requested
    if args.fail_on_found and findings:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
