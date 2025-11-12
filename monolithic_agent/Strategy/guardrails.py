"""
Guardrails - Security checks, validation, and safety filters for strategies
Ensures strategies don't contain dangerous patterns or violate safety rules.
"""

from typing import Dict, Any, List, Tuple, Optional
import re


class SecurityViolation(Exception):
    """Raised when a security violation is detected."""
    pass


class Guardrails:
    """Security and safety checks for trading strategies."""
    
    # Red flag keywords that might indicate manipulation or scams
    SCAM_KEYWORDS = [
        "pump and dump", "pump & dump", "guaranteed profit", "guaranteed returns",
        "can't lose", "risk-free", "insider", "manipulation", "front-run",
        "front run", "wash trade", "spoofing", "layering", "quote stuffing"
    ]
    
    # Suspicious promises
    SUSPICIOUS_PROMISES = [
        r"\d+%\s+guaranteed",
        r"no\s+risk",
        r"zero\s+risk",
        r"always\s+profit",
        r"never\s+lose"
    ]
    
    # Dangerous operations keywords
    DANGEROUS_OPS = [
        "margin call", "unlimited risk", "naked option", "unlimited leverage"
    ]
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize guardrails.
        
        Args:
            strict_mode: If True, raise exceptions on violations. If False, just warn.
        """
        self.strict_mode = strict_mode
        self.violations = []
        self.warnings = []
    
    def check_strategy(self, strategy_dict: Dict[str, Any], raw_input: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Run all safety checks on a strategy.
        
        Args:
            strategy_dict: Parsed strategy dictionary
            raw_input: Original raw input text (for keyword scanning)
            
        Returns:
            Tuple of (is_safe, list_of_issues)
        """
        self.violations = []
        self.warnings = []
        
        # Run checks
        if raw_input:
            self._check_for_scam_keywords(raw_input)
            self._check_for_dangerous_operations(raw_input)
        
        self._check_risk_controls(strategy_dict)
        self._check_leverage(strategy_dict)
        self._check_position_sizing(strategy_dict)
        self._validate_provenance(strategy_dict)
        
        # Combine issues
        all_issues = self.violations + self.warnings
        is_safe = len(self.violations) == 0
        
        return is_safe, all_issues
    
    def _check_for_scam_keywords(self, text: str) -> None:
        """Check for scam/manipulation keywords."""
        text_lower = text.lower()
        
        found_keywords = [kw for kw in self.SCAM_KEYWORDS if kw in text_lower]
        
        if found_keywords:
            msg = f"Potential scam/manipulation indicators detected: {', '.join(found_keywords)}"
            self.violations.append(msg)
            if self.strict_mode:
                raise SecurityViolation(msg)
        
        # Check suspicious promises
        for pattern in self.SUSPICIOUS_PROMISES:
            if re.search(pattern, text_lower):
                msg = f"Suspicious promise detected (pattern: {pattern})"
                self.violations.append(msg)
                if self.strict_mode:
                    raise SecurityViolation(msg)
    
    def _check_for_dangerous_operations(self, text: str) -> None:
        """Check for dangerous trading operations."""
        text_lower = text.lower()
        
        found_dangerous = [op for op in self.DANGEROUS_OPS if op in text_lower]
        
        if found_dangerous:
            msg = f"Dangerous operation detected: {', '.join(found_dangerous)}"
            self.warnings.append(msg)
    
    def _check_risk_controls(self, strategy: Dict[str, Any]) -> None:
        """Verify basic risk controls are present."""
        steps = strategy.get("steps", [])
        
        if not steps:
            return
        
        # Check for any risk control measures
        has_stop_loss = False
        has_size_limit = False
        
        for step in steps:
            exit_rule = step.get("exit", {})
            risk_controls = step.get("risk_controls", {})
            action = step.get("action", {})
            
            # Check stop loss
            if isinstance(exit_rule, dict) and exit_rule.get("stop_loss"):
                has_stop_loss = True
            elif isinstance(exit_rule, str) and "stop" in exit_rule.lower():
                has_stop_loss = True
            
            if risk_controls.get("stop_loss"):
                has_stop_loss = True
            
            # Check size limits
            size = action.get("size", {})
            if size.get("mode") in ["percent_of_equity", "risk_per_trade", "volatility_target"]:
                has_size_limit = True
        
        if not has_stop_loss:
            self.warnings.append(
                "No stop-loss detected. This could lead to unlimited losses."
            )
        
        if not has_size_limit:
            self.warnings.append(
                "No dynamic position sizing detected. Consider risk-based sizing."
            )
    
    def _check_leverage(self, strategy: Dict[str, Any]) -> None:
        """Check for excessive leverage."""
        # Look for leverage mentions in strategy
        strategy_str = str(strategy).lower()
        
        # Extract leverage numbers
        leverage_pattern = r'leverage[:\s]*(\d+(?:\.\d+)?)[x\s]'
        matches = re.findall(leverage_pattern, strategy_str)
        
        for match in matches:
            leverage = float(match)
            if leverage > 10:
                self.warnings.append(
                    f"Very high leverage detected ({leverage}x). Extreme risk."
                )
            elif leverage > 3:
                self.warnings.append(
                    f"High leverage detected ({leverage}x). Increased risk."
                )
    
    def _check_position_sizing(self, strategy: Dict[str, Any]) -> None:
        """Validate position sizing is reasonable."""
        steps = strategy.get("steps", [])
        
        for step in steps:
            action = step.get("action", {})
            size = action.get("size", {})
            
            if size.get("mode") == "percent_of_equity":
                percent = size.get("value", 0)
                if percent > 100:
                    self.violations.append(
                        f"Invalid position size: {percent}% of equity (>100%)"
                    )
                elif percent > 50:
                    self.warnings.append(
                        f"Very large position size: {percent}% of equity"
                    )
                elif percent > 25:
                    self.warnings.append(
                        f"Large position size: {percent}% of equity"
                    )
    
    def _validate_provenance(self, strategy: Dict[str, Any]) -> None:
        """Check that provenance is tracked."""
        provenance = strategy.get("provenance", {})
        sources = provenance.get("sources", [])
        
        if not sources:
            self.warnings.append(
                "No provenance tracked. Strategy source should be documented."
            )
        
        # Check for suspicious sources
        for source in sources:
            url = source.get("url", "")
            if url:
                # Very basic check - in production, use a proper URL reputation service
                suspicious_domains = ["bit.ly", "tinyurl.com"]  # shortened URLs
                if any(domain in url.lower() for domain in suspicious_domains):
                    self.warnings.append(
                        f"Suspicious URL detected: {url} (shortened URL)"
                    )
    
    def check_credentials_request(self, text: str) -> bool:
        """
        Check if text requests admin/root credentials.
        
        Returns:
            True if credential request detected, False otherwise
        """
        text_lower = text.lower()
        
        credential_keywords = [
            "admin password", "root password", "sudo password",
            "api key", "secret key", "private key", "access token"
        ]
        
        request_keywords = ["enter", "provide", "give", "input", "type"]
        
        for cred_kw in credential_keywords:
            if cred_kw in text_lower:
                for req_kw in request_keywords:
                    if req_kw in text_lower:
                        return True
        
        return False
    
    def check_live_trading_request(self, text: str) -> bool:
        """
        Check if request is for live trading without proper approval.
        
        Returns:
            True if live trading detected, False otherwise
        """
        text_lower = text.lower()
        
        live_keywords = [
            "live trade", "live trading", "real money", "production",
            "execute live", "run live", "deploy live"
        ]
        
        return any(keyword in text_lower for keyword in live_keywords)
    
    def require_approval_token(self, action: str) -> str:
        """
        Generate requirement message for approval token.
        
        Args:
            action: The action requiring approval
            
        Returns:
            Approval requirement message
        """
        return f"""
⚠️  APPROVAL REQUIRED ⚠️

Action: {action}

This action requires explicit approval with a two-factor confirmation:
1. UI Confirmation: Click "Approve" in the interface
2. CLI Token: Provide the approval token

To proceed:
- Ensure you have reviewed all test results
- Understand the risks involved
- Have a risk management plan in place

Do not proceed if you have any doubts.
"""
    
    def get_violations(self) -> List[str]:
        """Get all violations."""
        return self.violations.copy()
    
    def get_warnings(self) -> List[str]:
        """Get all warnings."""
        return self.warnings.copy()
    
    def format_issues(self) -> str:
        """Format all issues for display."""
        output = []
        
        if self.violations:
            output.append("🚫 VIOLATIONS (Strategy blocked):")
            for i, violation in enumerate(self.violations, 1):
                output.append(f"  {i}. {violation}")
        
        if self.warnings:
            output.append("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                output.append(f"  {i}. {warning}")
        
        return "\n".join(output) if output else "✅ No issues detected"


def check_strategy_safety(
    strategy_dict: Dict[str, Any],
    raw_input: Optional[str] = None,
    strict_mode: bool = False
) -> Tuple[bool, List[str]]:
    """
    Convenience function to check strategy safety.
    
    Args:
        strategy_dict: Parsed strategy dictionary
        raw_input: Original input text
        strict_mode: Raise exceptions on violations
        
    Returns:
        Tuple of (is_safe, list_of_issues)
    """
    guardrails = Guardrails(strict_mode=strict_mode)
    return guardrails.check_strategy(strategy_dict, raw_input)


if __name__ == "__main__":
    # Test guardrails
    
    # Test 1: Safe strategy
    safe_strategy = {
        "steps": [{
            "action": {
                "size": {"mode": "percent_of_equity", "value": 5}
            },
            "exit": {"stop_loss": "2%"}
        }],
        "provenance": {"sources": [{"url": "https://example.com"}]}
    }
    
    guardrails = Guardrails(strict_mode=False)
    is_safe, issues = guardrails.check_strategy(safe_strategy)
    
    print("Test 1: Safe Strategy")
    print(f"Is safe: {is_safe}")
    print(guardrails.format_issues())
    
    # Test 2: Dangerous strategy
    dangerous_input = "This is a guaranteed profit pump and dump strategy with no risk!"
    dangerous_strategy = {
        "steps": [{
            "action": {
                "size": {"mode": "percent_of_equity", "value": 150}
            }
        }],
        "provenance": {"sources": []}
    }
    
    print("\n\nTest 2: Dangerous Strategy")
    guardrails2 = Guardrails(strict_mode=False)
    try:
        is_safe2, issues2 = guardrails2.check_strategy(dangerous_strategy, dangerous_input)
        print(f"Is safe: {is_safe2}")
        print(guardrails2.format_issues())
    except SecurityViolation as e:
        print(f"Security violation caught: {e}")
