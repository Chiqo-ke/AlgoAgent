"""
Strategy Parser - Extract structured steps from free-form strategy descriptions
Handles natural language parsing and step extraction for strategy canonicalization.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    ENTER = "enter"
    EXIT = "exit"
    MODIFY = "modify"
    HOLD = "hold"
    CANCEL = "cancel"
    NOTIFY = "notify"
    WAIT = "wait"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    CONDITIONAL = "conditional"
    OTHER = "other"

@dataclass
class ParsedStep:
    """Represents a parsed strategy step before canonicalization."""
    order: int
    title: str
    trigger: str
    action_type: ActionType
    order_type: Optional[OrderType] = None
    instrument: Optional[str] = None
    size_info: Optional[Dict[str, Any]] = None
    exit_conditions: Optional[Dict[str, Any]] = None
    conditions: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    rationale: Optional[str] = None
    raw_text: str = ""

class StrategyParser:
    """
    Parses free-form strategy descriptions into structured steps.
    """
    
    def __init__(self):
        self.setup_patterns()
    
    def setup_patterns(self):
        """Initialize regex patterns for parsing."""
        
        # Entry triggers
        self.entry_patterns = [
            r'(?:buy|enter long|go long|purchase)\s+(?:when|if|after)\s+(.+?)(?:\.|,|$)',
            r'(?:enter|open)\s+(?:position|trade)\s+(?:when|if|after)\s+(.+?)(?:\.|,|$)',
            r'(?:signal|trigger):\s*(.+?)(?:\.|,|$)',
            r'entry:\s*(.+?)(?:\.|,|$)'
        ]
        
        # Exit patterns
        self.exit_patterns = [
            r'(?:stop\s*loss|sl|stop)(?:\s*at|:)?\s*(.+?)(?:\.|,|$)',
            r'(?:take\s*profit|tp|target)(?:\s*at|:)?\s*(.+?)(?:\.|,|$)',
            r'(?:exit|close)\s+(?:when|if|at)\s+(.+?)(?:\.|,|$)',
            r'(?:sell|exit)\s+(?:when|if|at)\s+(.+?)(?:\.|,|$)'
        ]
        
        # Size patterns
        self.size_patterns = [
            r'(?:buy|purchase|enter)\s+(\d+)\s+(?:shares|contracts|lots|units)',
            r'(?:position\s*size|size):\s*(\d+(?:\.\d+)?)\s*(?:%|percent|shares|contracts)?',
            r'risk\s+(\d+(?:\.\d+)?)\s*(?:%|percent)\s+(?:of|per)\s+(?:account|equity|trade)',
            r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s+(?:of\s+)?(?:portfolio|equity|account)'
        ]
        
        # Condition patterns
        self.condition_patterns = [
            r'(?:if|when|provided|given)\s+(.+?)(?:\s+then|\.|,|$)',
            r'condition:\s*(.+?)(?:\.|,|$)',
            r'only\s+(?:if|when)\s+(.+?)(?:\.|,|$)'
        ]
        
        # Indicator patterns
        self.indicator_patterns = [
            r'(\d+)\s*(?:period\s+)?(?:ema|exponential moving average)',
            r'(\d+)\s*(?:period\s+)?(?:sma|simple moving average|moving average)',
            r'rsi\s*(?:\((\d+)\))?',
            r'macd\s*(?:\((\d+),\s*(\d+),\s*(\d+)\))?',
            r'bollinger\s*bands?\s*(?:\((\d+),\s*(\d+(?:\.\d+)?)\))?',
            r'stochastic\s*(?:\((\d+),\s*(\d+),\s*(\d+)\))?'
        ]
        
        # Timeframe patterns
        self.timeframe_patterns = [
            r'(\d+)\s*(?:m|min|minute)(?:s)?\s+(?:chart|timeframe|tf)',
            r'(\d+)\s*(?:h|hour)(?:s)?\s+(?:chart|timeframe|tf)',
            r'(\d+)\s*(?:d|day)(?:s)?\s+(?:chart|timeframe|tf)',
            r'(?:1|5|15|30|60)\s*(?:m|min|minute)(?:s)?(?:\s+chart|\s+timeframe|\s+tf)?'
        ]
    
    def parse_strategy_text(self, text: str) -> List[ParsedStep]:
        """
        Main parsing function to extract steps from strategy text.
        """
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Try to identify numbered steps first
        numbered_steps = self._extract_numbered_steps(text)
        
        if numbered_steps:
            parsed_steps = []
            for i, step_text in enumerate(numbered_steps, 1):
                parsed_step = self._parse_single_step(step_text, i)
                if parsed_step:
                    parsed_steps.append(parsed_step)
            return parsed_steps
        
        # If no numbered steps, try to parse as single strategy description
        single_step = self._parse_single_step(text, 1)
        return [single_step] if single_step else []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize input text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\.\,\:\;\!\?\(\)\-\%\$\+\/<>=]', '', text)
        return text.strip()
    
    def _extract_numbered_steps(self, text: str) -> List[str]:
        """Extract numbered steps from text."""
        # Pattern for numbered steps
        step_pattern = r'(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\n\s*$|$)'
        matches = re.findall(step_pattern, text, re.MULTILINE | re.DOTALL)
        
        if matches:
            return [match[1].strip() for match in matches]
        
        # Try bullet points
        bullet_pattern = r'(?:^|\n)\s*[•\-\*]\s*(.+?)(?=\n\s*[•\-\*]|\n\s*$|$)'
        bullet_matches = re.findall(bullet_pattern, text, re.MULTILINE | re.DOTALL)
        
        if bullet_matches:
            return [match.strip() for match in bullet_matches]
        
        return []
    
    def _parse_single_step(self, step_text: str, order: int) -> Optional[ParsedStep]:
        """Parse a single step description."""
        step_text = step_text.strip()
        if not step_text:
            return None
        
        # Determine if this is an entry or exit step
        is_entry = self._is_entry_step(step_text)
        is_exit = self._is_exit_step(step_text)
        
        if is_entry:
            return self._parse_entry_step(step_text, order)
        elif is_exit:
            return self._parse_exit_step(step_text, order)
        else:
            # Generic step
            return self._parse_generic_step(step_text, order)
    
    def _is_entry_step(self, text: str) -> bool:
        """Check if text describes an entry action."""
        entry_keywords = ['buy', 'enter', 'long', 'purchase', 'open position', 'signal']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in entry_keywords)
    
    def _is_exit_step(self, text: str) -> bool:
        """Check if text describes an exit action."""
        exit_keywords = ['sell', 'exit', 'close', 'stop loss', 'take profit', 'sl', 'tp']
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in exit_keywords)
    
    def _parse_entry_step(self, text: str, order: int) -> ParsedStep:
        """Parse an entry step."""
        # Extract trigger condition
        trigger = self._extract_trigger(text)
        
        # Extract size information
        size_info = self._extract_size_info(text)
        
        # Extract conditions
        conditions = self._extract_conditions(text)
        
        # Extract parameters (indicators, etc.)
        parameters = self._extract_parameters(text)
        
        # Determine order type
        order_type = self._determine_order_type(text)
        
        # Extract instrument if mentioned
        instrument = self._extract_instrument(text)
        
        return ParsedStep(
            order=order,
            title=f"Entry Step {order}",
            trigger=trigger or "Entry trigger not clearly specified",
            action_type=ActionType.ENTER,
            order_type=order_type,
            instrument=instrument,
            size_info=size_info,
            conditions=conditions,
            parameters=parameters,
            raw_text=text
        )
    
    def _parse_exit_step(self, text: str, order: int) -> ParsedStep:
        """Parse an exit step."""
        # Extract exit conditions
        exit_conditions = self._extract_exit_conditions(text)
        
        return ParsedStep(
            order=order,
            title=f"Exit Step {order}",
            trigger="Exit conditions met",
            action_type=ActionType.EXIT,
            exit_conditions=exit_conditions,
            raw_text=text
        )
    
    def _parse_generic_step(self, text: str, order: int) -> ParsedStep:
        """Parse a generic step that's not clearly entry or exit."""
        return ParsedStep(
            order=order,
            title=f"Step {order}",
            trigger=text,
            action_type=ActionType.HOLD,  # Default action
            raw_text=text
        )
    
    def _extract_trigger(self, text: str) -> Optional[str]:
        """Extract trigger condition from text."""
        for pattern in self.entry_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: look for common trigger words
        trigger_indicators = ['when', 'if', 'after', 'cross', 'break', 'above', 'below']
        text_lower = text.lower()
        
        for indicator in trigger_indicators:
            if indicator in text_lower:
                # Extract text after the indicator
                parts = text_lower.split(indicator, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return None
    
    def _extract_size_info(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract position sizing information."""
        for pattern in self.size_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                
                # Determine if it's percentage or fixed
                if '%' in text or 'percent' in text.lower():
                    return {"mode": "percent_of_equity", "value": float(value)}
                elif 'risk' in text.lower():
                    return {"mode": "risk_per_trade", "value": float(value)}
                else:
                    return {"mode": "fixed", "value": int(float(value))}
        
        return None
    
    def _extract_conditions(self, text: str) -> Optional[str]:
        """Extract conditional statements."""
        for pattern in self.condition_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_parameters(self, text: str) -> List[Dict[str, Any]]:
        """Extract indicator parameters."""
        parameters = []
        
        # EMA parameters
        ema_matches = re.findall(r'(\d+)\s*(?:period\s+)?ema', text, re.IGNORECASE)
        for match in ema_matches:
            parameters.append({"name": "ema_period", "value": int(match)})
        
        # SMA parameters
        sma_matches = re.findall(r'(\d+)\s*(?:period\s+)?(?:sma|moving average)', text, re.IGNORECASE)
        for match in sma_matches:
            parameters.append({"name": "sma_period", "value": int(match)})
        
        # RSI parameters
        rsi_match = re.search(r'rsi\s*(?:\((\d+)\))?', text, re.IGNORECASE)
        if rsi_match:
            period = int(rsi_match.group(1)) if rsi_match.group(1) else 14
            parameters.append({"name": "rsi_period", "value": period})
        
        # Percentage values (for stops, targets, etc.)
        percent_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', text)
        for i, match in enumerate(percent_matches):
            parameters.append({"name": f"percentage_{i+1}", "value": float(match)})
        
        return parameters
    
    def _extract_exit_conditions(self, text: str) -> Dict[str, Any]:
        """Extract exit conditions (stop loss, take profit, etc.)."""
        exit_conditions = {}
        
        # Stop loss
        sl_patterns = [
            r'(?:stop\s*loss|sl)\s*(?:at|:)?\s*(\d+(?:\.\d+)?)\s*%',
            r'(?:stop\s*loss|sl)\s*(?:at|:)?\s*\$?(\d+(?:\.\d+)?)',
            r'stop\s*(?:at)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:below|under)'
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if '%' in text:
                    exit_conditions['stop_loss'] = f"{value}% below entry"
                else:
                    exit_conditions['stop_loss'] = f"${value}"
                break
        
        # Take profit
        tp_patterns = [
            r'(?:take\s*profit|tp|target)\s*(?:at|:)?\s*(\d+(?:\.\d+)?)\s*%',
            r'(?:take\s*profit|tp|target)\s*(?:at|:)?\s*\$?(\d+(?:\.\d+)?)',
            r'target\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*%\s*(?:above|over)'
        ]
        
        for pattern in tp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if '%' in text:
                    exit_conditions['take_profit'] = f"{value}% above entry"
                else:
                    exit_conditions['take_profit'] = f"${value}"
                break
        
        return exit_conditions
    
    def _determine_order_type(self, text: str) -> OrderType:
        """Determine order type from text."""
        text_lower = text.lower()
        
        if 'market' in text_lower or 'at market' in text_lower:
            return OrderType.MARKET
        elif 'limit' in text_lower:
            return OrderType.LIMIT
        elif 'stop' in text_lower and 'limit' in text_lower:
            return OrderType.STOP_LIMIT
        elif 'stop' in text_lower:
            return OrderType.STOP
        else:
            return OrderType.MARKET  # Default assumption
    
    def _extract_instrument(self, text: str) -> Optional[str]:
        """Extract instrument/ticker from text."""
        # Common ticker patterns
        ticker_patterns = [
            r'\b([A-Z]{1,5})\b',  # 1-5 uppercase letters
            r'([A-Z]{2,4})\s+(?:stock|shares|equity)',
            r'(?:buy|sell|trade)\s+([A-Z]{2,5})',
        ]
        
        for pattern in ticker_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Return the first reasonable ticker found
                for match in matches:
                    if len(match) >= 2 and match not in ['EMA', 'SMA', 'RSI', 'MACD', 'ATR']:
                        return match
        
        return None
    
    def to_canonical_steps(self, parsed_steps: List[ParsedStep]) -> List[Dict[str, Any]]:
        """Convert parsed steps to canonical step format."""
        canonical_steps = []
        
        for step in parsed_steps:
            canonical_step = {
                "step_id": f"s{step.order}",
                "order": step.order,
                "title": step.title,
                "trigger": step.trigger,
                "action": {
                    "type": step.action_type.value
                }
            }
            
            # Add order type if specified
            if step.order_type:
                canonical_step["action"]["order_type"] = step.order_type.value
            
            # Add instrument if specified
            if step.instrument:
                canonical_step["action"]["instrument"] = step.instrument
            
            # Add size information
            if step.size_info:
                canonical_step["action"]["size"] = step.size_info
            
            # Add conditions
            if step.conditions:
                canonical_step["condition"] = step.conditions
            
            # Add exit conditions
            if step.exit_conditions:
                canonical_step["exit"] = step.exit_conditions
            
            # Add parameters
            if step.parameters:
                canonical_step["params"] = step.parameters
            
            canonical_steps.append(canonical_step)
        
        return canonical_steps


# Utility functions for testing
def test_parser():
    """Test the strategy parser with example inputs."""
    parser = StrategyParser()
    
    test_strategies = [
        "Buy 100 shares when 50 EMA crosses above 200 EMA. Place stop at 1% below entry. Take profit at 2%.",
        
        """1. Enter long when RSI(14) drops below 30 and then crosses back above 30
        2. Position size: 2% of account equity
        3. Stop loss at 1.5% below entry
        4. Take profit at 3% above entry""",
        
        "Scalping strategy: Buy SPY when price breaks above 5-minute high with volume confirmation. Exit after 5 minutes or 0.5% profit.",
    ]
    
    for i, strategy in enumerate(test_strategies, 1):
        print(f"\n--- Test Strategy {i} ---")
        print(f"Input: {strategy}")
        
        parsed_steps = parser.parse_strategy_text(strategy)
        canonical_steps = parser.to_canonical_steps(parsed_steps)
        
        print(f"Parsed {len(parsed_steps)} steps:")
        for step in canonical_steps:
            print(f"  {step['order']}. {step['title']}: {step['trigger']}")
        
        print(f"Canonical JSON: {json.dumps(canonical_steps[0] if canonical_steps else {}, indent=2)}")


if __name__ == "__main__":
    test_parser()