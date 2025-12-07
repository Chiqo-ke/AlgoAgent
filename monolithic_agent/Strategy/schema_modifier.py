"""
Strategy Schema Modifier
========================

Applies user edits to canonical strategy schemas intelligently.

Handles:
- Risk management changes (stop loss, take profit, position sizing)
- Indicator parameter updates (EMA periods, RSI levels, etc.)
- Entry/exit condition modifications
- New indicator additions
- Timeframe changes

Usage:
    modifier = StrategySchemaModifier(use_gemini=True)
    updated_schema = modifier.modify_schema(
        current_schema=existing_schema,
        user_message="Set stop loss to 10 pips",
        extracted_entities={'parameters': {'stop_loss': '10 pips'}}
    )
"""

import os
import json
import re
import copy
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class StrategySchemaModifier:
    """Applies edits to canonical trading strategy schemas"""
    
    def __init__(self, use_gemini: bool = True):
        """
        Initialize schema modifier
        
        Args:
            use_gemini: Whether to use Gemini AI for intelligent modifications
                       If False, uses rule-based modifications
        """
        self.use_gemini = use_gemini
        
        if use_gemini:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.warning("GEMINI_API_KEY not found, falling back to rule-based modification")
                self.use_gemini = False
            else:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("Initialized StrategySchemaModifier with Gemini")
        
        if not self.use_gemini:
            logger.info("Initialized StrategySchemaModifier with rule-based modification")
    
    def modify_schema(self, 
                     current_schema: Dict, 
                     user_message: str,
                     extracted_entities: Optional[Dict] = None) -> Dict:
        """
        Apply user modifications to strategy schema
        
        Args:
            current_schema: The existing canonical schema (ChronicQL format)
            user_message: What the user said (for context)
            extracted_entities: Parameters/indicators extracted by intent classifier
        
        Returns:
            Updated canonical schema with modifications applied
        """
        if self.use_gemini:
            return self._modify_with_gemini(current_schema, user_message, extracted_entities)
        else:
            return self._modify_rule_based(current_schema, user_message, extracted_entities)
    
    def _modify_with_gemini(self, 
                           current_schema: Dict,
                           user_message: str,
                           extracted_entities: Optional[Dict]) -> Dict:
        """Use Gemini AI for intelligent schema modification"""
        
        prompt = f"""
You are an expert trading strategy schema editor.

CURRENT STRATEGY SCHEMA (ChronicQL format):
```json
{json.dumps(current_schema, indent=2)}
```

USER'S MODIFICATION REQUEST:
"{user_message}"

EXTRACTED PARAMETERS:
```json
{json.dumps(extracted_entities or {}, indent=2)}
```

TASK:
Apply the user's modifications to the schema and return the COMPLETE updated schema.

RULES:
1. Preserve ALL existing fields that weren't mentioned by the user
2. Update ONLY the specific fields the user wants to change
3. Maintain valid ChronicQL format
4. If adding new indicators, use proper format with parameters
5. If modifying risk management, update the risk_management section
6. If modifying indicators, update the indicators array
7. If adding conditions, update entry_conditions or exit_conditions

ChronicQL Schema Structure Reference:
{{
    "strategy_name": "...",
    "strategy_description": "...",
    "classification": "...",
    "timeframe": "1h",
    "indicators": [
        {{
            "indicator_name": "EMA",
            "parameters": {{"period": 30}},
            "output_name": "ema_short"
        }}
    ],
    "entry_conditions": [
        {{
            "condition": "ema_short > ema_long",
            "description": "..."
        }}
    ],
    "exit_conditions": [...],
    "risk_management": {{
        "stop_loss": {{"type": "fixed", "value": 10, "unit": "pips"}},
        "take_profit": {{"type": "fixed", "value": 50, "unit": "pips"}},
        "position_size": {{"type": "risk_percentage", "value": 1}}
    }},
    "metadata": {{
        "confidence": 0.85,
        "warnings": [],
        "recommendations": []
    }}
}}

IMPORTANT:
- Return ONLY valid JSON (no markdown, no code blocks, no explanations)
- Return the COMPLETE schema with ALL fields
- DO NOT remove or omit existing fields
- Make minimal changes - only what user requested

Return the complete updated schema now:
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            updated_schema = json.loads(response_text)
            
            logger.info("Successfully modified schema with Gemini")
            logger.debug(f"Modified fields: {self._get_diff_summary(current_schema, updated_schema)}")
            
            return updated_schema
            
        except Exception as e:
            logger.error(f"Error modifying schema with Gemini: {e}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
            # Fallback to rule-based
            logger.info("Falling back to rule-based modification")
            return self._modify_rule_based(current_schema, user_message, extracted_entities)
    
    def _modify_rule_based(self,
                          current_schema: Dict,
                          user_message: str,
                          extracted_entities: Optional[Dict]) -> Dict:
        """Rule-based schema modification as fallback"""
        
        # Create a deep copy to avoid modifying original
        updated_schema = copy.deepcopy(current_schema)
        
        if not extracted_entities:
            logger.warning("No extracted entities provided, returning original schema")
            return updated_schema
        
        parameters = extracted_entities.get('parameters', {})
        indicators = extracted_entities.get('indicators', {})
        conditions = extracted_entities.get('conditions', [])
        
        # Initialize risk_management if not exists
        if 'risk_management' not in updated_schema:
            updated_schema['risk_management'] = {}
        
        # Apply parameter modifications
        for param_name, param_value in parameters.items():
            if param_name == 'stop_loss':
                self._set_stop_loss(updated_schema, param_value)
            elif param_name == 'take_profit':
                self._set_take_profit(updated_schema, param_value)
            elif param_name == 'risk_per_trade':
                self._set_position_size(updated_schema, param_value)
        
        # Apply indicator modifications
        if indicators:
            self._update_indicators(updated_schema, indicators)
        
        # Add new conditions
        if conditions:
            self._add_conditions(updated_schema, conditions)
        
        logger.info("Applied rule-based modifications to schema")
        return updated_schema
    
    def _set_stop_loss(self, schema: Dict, value_str: str):
        """Set stop loss in risk management"""
        
        # Parse value string (e.g., "10 pips", "2%", "50 points")
        match = re.search(r'(\d+\.?\d*)\s*(pips?|%|percent|points?)', value_str.lower())
        
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            # Normalize unit
            if unit in ['%', 'percent']:
                unit = 'percentage'
            elif unit in ['pip', 'pips']:
                unit = 'pips'
            elif unit in ['point', 'points']:
                unit = 'points'
            
            schema['risk_management']['stop_loss'] = {
                'type': 'fixed',
                'value': value,
                'unit': unit
            }
            
            logger.info(f"Set stop loss to {value} {unit}")
    
    def _set_take_profit(self, schema: Dict, value_str: str):
        """Set take profit in risk management"""
        
        match = re.search(r'(\d+\.?\d*)\s*(pips?|%|percent|points?)', value_str.lower())
        
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            
            if unit in ['%', 'percent']:
                unit = 'percentage'
            elif unit in ['pip', 'pips']:
                unit = 'pips'
            elif unit in ['point', 'points']:
                unit = 'points'
            
            schema['risk_management']['take_profit'] = {
                'type': 'fixed',
                'value': value,
                'unit': unit
            }
            
            logger.info(f"Set take profit to {value} {unit}")
    
    def _set_position_size(self, schema: Dict, value_str: str):
        """Set position sizing"""
        
        match = re.search(r'(\d+\.?\d*)\s*%', value_str.lower())
        
        if match:
            value = float(match.group(1))
            
            schema['risk_management']['position_size'] = {
                'type': 'risk_percentage',
                'value': value
            }
            
            logger.info(f"Set position size to {value}% risk per trade")
    
    def _update_indicators(self, schema: Dict, indicator_updates: Dict):
        """Update indicator parameters"""
        
        if 'indicators' not in schema:
            schema['indicators'] = []
        
        # Handle EMA updates
        if 'ema_short' in indicator_updates or 'ema_long' in indicator_updates:
            # Find or create EMA indicators
            ema_short_found = False
            ema_long_found = False
            
            for indicator in schema['indicators']:
                if indicator.get('output_name') == 'ema_short':
                    indicator['parameters']['period'] = indicator_updates.get('ema_short', 
                                                                             indicator['parameters'].get('period', 30))
                    ema_short_found = True
                elif indicator.get('output_name') == 'ema_long':
                    indicator['parameters']['period'] = indicator_updates.get('ema_long',
                                                                              indicator['parameters'].get('period', 60))
                    ema_long_found = True
            
            # Add new EMA indicators if not found
            if not ema_short_found and 'ema_short' in indicator_updates:
                schema['indicators'].append({
                    'indicator_name': 'EMA',
                    'parameters': {'period': indicator_updates['ema_short']},
                    'output_name': 'ema_short'
                })
            
            if not ema_long_found and 'ema_long' in indicator_updates:
                schema['indicators'].append({
                    'indicator_name': 'EMA',
                    'parameters': {'period': indicator_updates['ema_long']},
                    'output_name': 'ema_long'
                })
            
            logger.info(f"Updated EMA indicators: {indicator_updates}")
        
        # Handle RSI updates
        if 'rsi_level' in indicator_updates:
            # This would typically go in entry_conditions, but for now just log
            logger.info(f"RSI level set to: {indicator_updates['rsi_level']}")
    
    def _add_conditions(self, schema: Dict, new_conditions: List[str]):
        """Add new entry or exit conditions"""
        
        if 'entry_conditions' not in schema:
            schema['entry_conditions'] = []
        
        for condition in new_conditions:
            schema['entry_conditions'].append({
                'condition': condition,
                'description': f"User added: {condition}"
            })
        
        logger.info(f"Added {len(new_conditions)} new conditions")
    
    def _get_diff_summary(self, old_schema: Dict, new_schema: Dict) -> List[str]:
        """Get a summary of what changed between schemas"""
        
        changes = []
        
        # Check risk management changes
        old_rm = old_schema.get('risk_management', {})
        new_rm = new_schema.get('risk_management', {})
        
        if old_rm.get('stop_loss') != new_rm.get('stop_loss'):
            changes.append('stop_loss')
        
        if old_rm.get('take_profit') != new_rm.get('take_profit'):
            changes.append('take_profit')
        
        if old_rm.get('position_size') != new_rm.get('position_size'):
            changes.append('position_size')
        
        # Check indicator changes
        old_indicators = old_schema.get('indicators', [])
        new_indicators = new_schema.get('indicators', [])
        
        if len(old_indicators) != len(new_indicators):
            changes.append('indicators_count')
        
        # Check condition changes
        old_entry = old_schema.get('entry_conditions', [])
        new_entry = new_schema.get('entry_conditions', [])
        
        if len(old_entry) != len(new_entry):
            changes.append('entry_conditions_count')
        
        return changes


# Convenience function
def modify_strategy_schema(current_schema: Dict, 
                          user_message: str,
                          extracted_entities: Optional[Dict] = None,
                          use_gemini: bool = True) -> Dict:
    """
    Convenience function to modify schema without instantiating class
    
    Args:
        current_schema: Existing strategy schema
        user_message: User's modification request
        extracted_entities: Parameters extracted by intent classifier
        use_gemini: Use Gemini AI (default: True)
    
    Returns:
        Updated strategy schema
    """
    modifier = StrategySchemaModifier(use_gemini=use_gemini)
    return modifier.modify_schema(current_schema, user_message, extracted_entities)


if __name__ == "__main__":
    # Test cases
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Testing Schema Modifier")
    print("=" * 60)
    
    # Sample schema
    test_schema = {
        "strategy_name": "EMA Crossover",
        "strategy_description": "30/60 EMA crossover strategy",
        "classification": "trend_following",
        "timeframe": "1h",
        "indicators": [
            {
                "indicator_name": "EMA",
                "parameters": {"period": 30},
                "output_name": "ema_short"
            },
            {
                "indicator_name": "EMA",
                "parameters": {"period": 60},
                "output_name": "ema_long"
            }
        ],
        "entry_conditions": [
            {
                "condition": "ema_short > ema_long",
                "description": "Short EMA crosses above long EMA"
            }
        ],
        "risk_management": {}
    }
    
    # Test modification
    print("\nOriginal schema:")
    print(json.dumps(test_schema, indent=2))
    
    print("\nApplying modification: 'Set stop loss to 10 pips and take profit to 50 pips'")
    
    updated = modify_strategy_schema(
        current_schema=test_schema,
        user_message="Set stop loss to 10 pips and take profit to 50 pips",
        extracted_entities={
            'parameters': {
                'stop_loss': '10 pips',
                'take_profit': '50 pips'
            }
        },
        use_gemini=True
    )
    
    print("\nUpdated schema:")
    print(json.dumps(updated, indent=2))
    
    print("\n" + "=" * 60)
