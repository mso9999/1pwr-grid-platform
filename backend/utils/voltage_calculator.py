from typing import Dict, List, Any
import math


class VoltageCalculator:
    """Calculate voltage drop across network"""
    
    def calculate_voltage_drop(self, 
                              poles: List[Dict], 
                              conductors: List[Dict],
                              source_voltage: float = 11000,
                              source_pole: str = None) -> Dict[str, Any]:
        """
        Calculate voltage drop for all conductors
        
        Args:
            poles: List of pole dictionaries
            conductors: List of conductor dictionaries
            source_voltage: Source voltage in volts
            source_pole: ID of source pole (if None, uses first pole)
            
        Returns:
            Dictionary with voltage calculation results
        """
        results = {
            'source_voltage': source_voltage,
            'source_pole': source_pole or (poles[0]['pole_id'] if poles else None),
            'conductor_voltages': {},
            'pole_voltages': {}
        }
        
        # Simple voltage drop calculation (placeholder)
        # In reality, this would use power flow analysis
        for conductor in conductors:
            conductor_id = conductor.get('conductor_id')
            length = conductor.get('length', 100)  # Default 100m if not specified
            
            # Simple voltage drop formula: 2% per 100m for MV, 3% for LV, 4% for Drop
            conductor_type = conductor.get('conductor_type', 'MV')
            if conductor_type == 'MV':
                drop_percent = (length / 100) * 2
            elif conductor_type == 'LV':
                drop_percent = (length / 100) * 3
            else:  # DROP
                drop_percent = (length / 100) * 4
            
            results['conductor_voltages'][conductor_id] = {
                'voltage_drop_percent': drop_percent,
                'voltage_drop_volts': source_voltage * (drop_percent / 100),
                'end_voltage': source_voltage * (1 - drop_percent / 100)
            }
        
        # Calculate pole voltages (simplified)
        for pole in poles:
            pole_id = pole.get('pole_id')
            # For now, just use source voltage
            results['pole_voltages'][pole_id] = source_voltage
        
        return results
