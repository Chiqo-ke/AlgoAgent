"""
Input Parser - Extract strategy steps from various input formats
Handles free text, numbered steps, and prepares for URL content extraction.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime


class InputParser:
    """Parse trading strategy input from various formats."""
    
    # Common trading action keywords
    ACTION_KEYWORDS = {
        'enter': ['buy', 'enter', 'long', 'go long', 'open position', 'purchase'],
        'exit': ['sell', 'exit', 'close', 'close position', 'liquidate'],
        'modify': ['adjust', 'modify', 'change', 'update'],
        'hold': ['hold', 'wait', 'maintain'],
        'cancel': ['cancel', 'abort', 'stop']
    }
    
    # Trigger/condition keywords
    TRIGGER_KEYWORDS = ['when', 'if', 'after', 'once', 'upon', 'as soon as', 'at']
    
    # Order type keywords
    ORDER_TYPE_KEYWORDS = {
        'market': ['market', 'at market'],
        'limit': ['limit', 'limit order'],
        'stop': ['stop', 'stop order'],
        'stop_limit': ['stop limit', 'stop-limit']
    }
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def parse(self, user_input: str, input_type: str = "auto") -> Dict[str, Any]:
        """
        Main parsing entry point.
        
        Args:
            user_input: Raw text input from user
            input_type: Type of input - "auto", "numbered", "freetext", "url"
            
        Returns:
            Dictionary with parsed steps and metadata
        """
        if input_type == "auto":
            input_type = self._detect_input_type(user_input)
        
        if input_type == "numbered":
            return self._parse_numbered_steps(user_input)
        elif input_type == "freetext":
            return self._parse_freetext(user_input)
        elif input_type == "url":
            return self._parse_url_reference(user_input)
        else:
            # Default to freetext parsing
            return self._parse_freetext(user_input)
    
    def _detect_input_type(self, text: str) -> str:
        """Detect the type of input format."""
        # Check for URL
        if re.search(r'https?://', text):
            return "url"
        
        # Check for numbered list (1., 2., 1), 2), Step 1:, etc.)
        numbered_patterns = [
            r'^\s*\d+[\.\)]\s+\w+',  # 1. text or 1) text
            r'^\s*step\s+\d+',        # Step 1:
        ]
        
        lines = text.strip().split('\n')
        numbered_count = sum(1 for line in lines 
                           if any(re.match(p, line.strip(), re.IGNORECASE) 
                                 for p in numbered_patterns))
        
        if numbered_count >= 2:  # At least 2 numbered items
            return "numbered"
        
        return "freetext"
    
    def _parse_numbered_steps(self, text: str) -> Dict[str, Any]:
        """Parse numbered list of steps."""
        steps = []
        lines = text.strip().split('\n')
        
        # Patterns for numbered items
        patterns = [
            r'^\s*(\d+)[\.\)]\s+(.*)',           # 1. text or 1) text
            r'^\s*step\s+(\d+)[:\.\-\s]+(.*)',   # Step 1: text
        ]
        
        current_step = None
        step_order = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to match numbered patterns
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous step if exists
                    if current_step:
                        steps.append(current_step)
                    
                    # Start new step
                    step_order += 1
                    step_text = match.group(2).strip()
                    current_step = self._extract_step_components(step_text, step_order)
                    matched = True
                    break
            
            # If not a numbered item, append to current step
            if not matched and current_step:
                # Enhance current step with additional info
                current_step = self._enhance_step_from_text(current_step, line)
        
        # Don't forget the last step
        if current_step:
            steps.append(current_step)
        
        return {
            "input_type": "numbered",
            "raw_input": text,
            "steps": steps,
            "parsed_at": datetime.now().isoformat()
        }
    
    def _parse_freetext(self, text: str) -> Dict[str, Any]:
        """Parse free-form text and extract strategy steps."""
        # Try to identify sentence boundaries with trading actions
        sentences = self._split_into_sentences(text)
        steps = []
        step_order = 0
        
        for sentence in sentences:
            # Check if sentence contains action keywords
            if self._contains_action_keyword(sentence):
                step_order += 1
                step = self._extract_step_components(sentence, step_order)
                steps.append(step)
        
        # If no clear steps found, treat entire text as one step
        if not steps:
            steps = [self._extract_step_components(text, 1)]
        
        return {
            "input_type": "freetext",
            "raw_input": text,
            "steps": steps,
            "parsed_at": datetime.now().isoformat()
        }
    
    def _parse_url_reference(self, text: str) -> Dict[str, Any]:
        """Parse URL references (actual fetching done separately)."""
        urls = re.findall(r'https?://[^\s]+', text)
        
        # Extract any context around URLs
        context = re.sub(r'https?://[^\s]+', '', text).strip()
        
        return {
            "input_type": "url",
            "raw_input": text,
            "urls": urls,
            "context": context,
            "steps": [],  # Will be populated after URL content is fetched
            "parsed_at": datetime.now().isoformat()
        }
    
    def _extract_step_components(self, text: str, order: int) -> Dict[str, Any]:
        """Extract trigger, action, and conditions from a step description."""
        step = {
            "step_id": f"s{order}",
            "order": order,
            "title": self._generate_title(text),
            "trigger": self._extract_trigger(text),
            "action": self._extract_action(text),
            "raw_text": text
        }
        
        # Extract optional components
        condition = self._extract_condition(text)
        if condition:
            step["condition"] = condition
        
        exit_rule = self._extract_exit_rule(text)
        if exit_rule:
            step["exit"] = exit_rule
        
        params = self._extract_parameters(text)
        if params:
            step["params"] = params
        
        return step
    
    def _generate_title(self, text: str) -> str:
        """Generate a short title from step text."""
        # Take first few words, max 50 chars
        words = text.split()[:8]
        title = ' '.join(words)
        if len(title) > 50:
            title = title[:47] + "..."
        return title
    
    def _extract_trigger(self, text: str) -> str:
        """Extract the trigger/condition that starts the step."""
        text_lower = text.lower()
        
        # Look for trigger keywords
        for keyword in self.TRIGGER_KEYWORDS:
            if keyword in text_lower:
                # Extract text after the keyword
                parts = re.split(rf'\b{keyword}\b', text, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) > 1:
                    trigger = parts[1].strip()
                    # Stop at action keyword
                    for action_list in self.ACTION_KEYWORDS.values():
                        for action in action_list:
                            trigger = re.split(rf'\b{action}\b', trigger, maxsplit=1, flags=re.IGNORECASE)[0]
                    return trigger.strip(' .,;')
        
        # If no explicit trigger, use first part of text
        return text.split('.')[0].strip()
    
    def _extract_action(self, text: str) -> Dict[str, Any]:
        """Extract action details."""
        text_lower = text.lower()
        
        # Determine action type
        action_type = "enter"  # default
        for act_type, keywords in self.ACTION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                action_type = act_type
                break
        
        # Determine order type
        order_type = "market"  # default
        for ord_type, keywords in self.ORDER_TYPE_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                order_type = ord_type
                break
        
        action = {
            "type": action_type,
            "order_type": order_type
        }
        
        # Extract size/quantity
        size = self._extract_size(text)
        if size:
            action["size"] = size
        
        # Extract instrument/ticker
        instrument = self._extract_instrument(text)
        if instrument:
            action["instrument"] = instrument
        
        return action
    
    def _extract_size(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract position size information."""
        # Look for number + shares/contracts/units
        shares_match = re.search(r'(\d+)\s*(shares?|contracts?|units?)', text, re.IGNORECASE)
        if shares_match:
            return {"mode": "fixed", "value": int(shares_match.group(1))}
        
        # Look for percentage of equity
        percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:of)?\s*(?:equity|capital|portfolio)', text, re.IGNORECASE)
        if percent_match:
            return {"mode": "percent_of_equity", "value": float(percent_match.group(1))}
        
        # Look for risk per trade
        risk_match = re.search(r'risk\s+(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE)
        if risk_match:
            return {"mode": "risk_per_trade", "value": float(risk_match.group(1))}
        
        return None
    
    def _extract_instrument(self, text: str) -> Optional[str]:
        """Extract instrument/ticker symbol."""
        # Look for common ticker patterns (2-5 uppercase letters)
        ticker_match = re.search(r'\b([A-Z]{2,5})\b', text)
        if ticker_match:
            return ticker_match.group(1)
        
        # Look for "of AAPL" or "on SPY" patterns
        of_match = re.search(r'\b(?:of|on|for)\s+([A-Z]{2,5})\b', text)
        if of_match:
            return of_match.group(1)
        
        return None
    
    def _extract_condition(self, text: str) -> Optional[str]:
        """Extract entry conditions."""
        # Look for condition phrases
        condition_patterns = [
            r'(?:only\s+)?if\s+(.*?)(?:\.|,|$)',
            r'provided\s+(.*?)(?:\.|,|$)',
            r'when\s+(.*?)(?:then|,|\.|$)'
        ]
        
        for pattern in condition_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_exit_rule(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract stop-loss and take-profit rules."""
        exit_rule = {}
        
        # Stop loss patterns
        sl_patterns = [
            r'stop\s*(?:loss)?\s*(?:at|@)?\s*(\d+(?:\.\d+)?)\s*%',
            r'sl\s*(?:at|@)?\s*(\d+(?:\.\d+)?)\s*%',
            r'stop\s+(\d+(?:\.\d+)?)\s*%\s+below'
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                exit_rule["stop_loss"] = f"{match.group(1)}% below entry"
                break
        
        # Take profit patterns
        tp_patterns = [
            r'take\s*profit\s*(?:at|@)?\s*(\d+(?:\.\d+)?)\s*%',
            r'tp\s*(?:at|@)?\s*(\d+(?:\.\d+)?)\s*%',
            r'profit\s+(?:target\s+)?(?:at|@)?\s*(\d+(?:\.\d+)?)\s*%'
        ]
        
        for pattern in tp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                exit_rule["take_profit"] = f"{match.group(1)}% above entry"
                break
        
        return exit_rule if exit_rule else None
    
    def _extract_parameters(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """Extract numerical parameters (like EMA periods, RSI thresholds)."""
        params = []
        
        # EMA/MA patterns
        ema_pattern = r'(\d+)\s*(?:period\s+)?(?:EMA|SMA|MA)'
        for match in re.finditer(ema_pattern, text, re.IGNORECASE):
            params.append({
                "name": f"ema_{match.group(1)}",
                "value": int(match.group(1))
            })
        
        # RSI patterns
        rsi_pattern = r'RSI\s*(?:of|at|>|<|=)?\s*(\d+)'
        for match in re.finditer(rsi_pattern, text, re.IGNORECASE):
            params.append({
                "name": "rsi_threshold",
                "value": int(match.group(1))
            })
        
        return params if params else None
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _contains_action_keyword(self, text: str) -> bool:
        """Check if text contains any action keyword."""
        text_lower = text.lower()
        for action_list in self.ACTION_KEYWORDS.values():
            if any(keyword in text_lower for keyword in action_list):
                return True
        return False
    
    def _enhance_step_from_text(self, step: Dict[str, Any], additional_text: str) -> Dict[str, Any]:
        """Enhance an existing step with additional information."""
        # Add to raw_text
        step["raw_text"] = step.get("raw_text", "") + " " + additional_text
        
        # Try to extract exit rules if not present
        if "exit" not in step:
            exit_rule = self._extract_exit_rule(additional_text)
            if exit_rule:
                step["exit"] = exit_rule
        
        # Try to extract more parameters
        new_params = self._extract_parameters(additional_text)
        if new_params:
            existing_params = step.get("params", [])
            step["params"] = existing_params + new_params
        
        return step


def parse_strategy_input(user_input: str, input_type: str = "auto") -> Dict[str, Any]:
    """
    Convenience function to parse strategy input.
    
    Args:
        user_input: Raw text from user
        input_type: Type of input ("auto", "numbered", "freetext", "url")
        
    Returns:
        Parsed strategy data
    """
    parser = InputParser()
    return parser.parse(user_input, input_type)


if __name__ == "__main__":
    # Test the parser
    test_input = """
    Buy 100 shares when 50 EMA crosses above 200 EMA. 
    Place stop at 1% below entry. Take profit at 2%. 
    No position sizing rule.
    """
    
    result = parse_strategy_input(test_input)
    print("Parsed result:")
    print(f"Input type: {result['input_type']}")
    print(f"Steps found: {len(result['steps'])}")
    for step in result['steps']:
        print(f"\nStep {step['order']}: {step['title']}")
        print(f"  Trigger: {step['trigger']}")
        print(f"  Action: {step['action']}")
        if 'exit' in step:
            print(f"  Exit: {step['exit']}")
