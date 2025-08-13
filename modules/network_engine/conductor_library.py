"""
Conductor Library
=================
Library of conductor specifications and electrical properties.
Configurable via UI in the new system (not hardcoded like uGridPLAN).
"""

from dataclasses import dataclass
from typing import Dict, Optional
import json


@dataclass
class ConductorSpec:
    """Conductor electrical specifications"""
    name: str
    resistance_ohm_per_km: float  # Resistance in Ohms/km
    reactance_ohm_per_km: float  # Reactance in Ohms/km  
    current_rating_amps: float  # Current carrying capacity
    cross_section_mm2: float  # Cross-sectional area in mm²
    material: str  # AAC, ACSR, ABC, etc.
    
    def impedance_per_km(self) -> complex:
        """Return complex impedance per km"""
        return complex(self.resistance_ohm_per_km, self.reactance_ohm_per_km)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'resistance_ohm_per_km': self.resistance_ohm_per_km,
            'reactance_ohm_per_km': self.reactance_ohm_per_km,
            'current_rating_amps': self.current_rating_amps,
            'cross_section_mm2': self.cross_section_mm2,
            'material': self.material
        }


class ConductorLibrary:
    """
    Conductor specifications library.
    In MVP, uses default values. In production, loaded from database.
    """
    
    def __init__(self):
        """Initialize with default conductor library"""
        self.conductors = self._load_defaults()
    
    def _load_defaults(self) -> Dict[str, ConductorSpec]:
        """Load default conductor specifications"""
        return {
            # All Aluminium Conductor (AAC)
            'AAC_50': ConductorSpec(
                name='AAC 50mm²',
                resistance_ohm_per_km=0.641,
                reactance_ohm_per_km=0.38,
                current_rating_amps=184,
                cross_section_mm2=50,
                material='AAC'
            ),
            'AAC_35': ConductorSpec(
                name='AAC 35mm²',
                resistance_ohm_per_km=0.917,
                reactance_ohm_per_km=0.39,
                current_rating_amps=148,
                cross_section_mm2=35,
                material='AAC'
            ),
            'AAC_25': ConductorSpec(
                name='AAC 25mm²',
                resistance_ohm_per_km=1.283,
                reactance_ohm_per_km=0.40,
                current_rating_amps=122,
                cross_section_mm2=25,
                material='AAC'
            ),
            'AAC_16': ConductorSpec(
                name='AAC 16mm²',
                resistance_ohm_per_km=2.004,
                reactance_ohm_per_km=0.41,
                current_rating_amps=96,
                cross_section_mm2=16,
                material='AAC'
            ),
            
            # Aerial Bundled Cable (ABC)
            'ABC_50': ConductorSpec(
                name='ABC 50mm²',
                resistance_ohm_per_km=0.641,
                reactance_ohm_per_km=0.08,
                current_rating_amps=150,
                cross_section_mm2=50,
                material='ABC'
            ),
            'ABC_35': ConductorSpec(
                name='ABC 35mm²',
                resistance_ohm_per_km=0.917,
                reactance_ohm_per_km=0.09,
                current_rating_amps=120,
                cross_section_mm2=35,
                material='ABC'
            ),
            'ABC_25': ConductorSpec(
                name='ABC 25mm²',
                resistance_ohm_per_km=1.283,
                reactance_ohm_per_km=0.09,
                current_rating_amps=95,
                cross_section_mm2=25,
                material='ABC'
            ),
            'ABC_16': ConductorSpec(
                name='ABC 16mm²',
                resistance_ohm_per_km=2.004,
                reactance_ohm_per_km=0.10,
                current_rating_amps=75,
                cross_section_mm2=16,
                material='ABC'
            ),
            
            # ACSR (Aluminium Conductor Steel Reinforced) - for longer spans
            'ACSR_50': ConductorSpec(
                name='ACSR 50/8',
                resistance_ohm_per_km=0.592,
                reactance_ohm_per_km=0.37,
                current_rating_amps=198,
                cross_section_mm2=50,
                material='ACSR'
            ),
            'ACSR_35': ConductorSpec(
                name='ACSR 35/6',
                resistance_ohm_per_km=0.849,
                reactance_ohm_per_km=0.38,
                current_rating_amps=159,
                cross_section_mm2=35,
                material='ACSR'
            ),
        }
    
    def get_conductor(self, conductor_type: str) -> Optional[ConductorSpec]:
        """
        Get conductor specification by type
        
        Args:
            conductor_type: Conductor type identifier
            
        Returns:
            ConductorSpec or None if not found
        """
        return self.conductors.get(conductor_type)
    
    def add_conductor(self, conductor_type: str, spec: ConductorSpec) -> None:
        """
        Add or update conductor specification
        
        Args:
            conductor_type: Conductor type identifier
            spec: Conductor specification
        """
        self.conductors[conductor_type] = spec
    
    def list_conductors(self) -> Dict[str, Dict]:
        """
        List all available conductors
        
        Returns:
            Dictionary of conductor types and their specifications
        """
        return {
            key: spec.to_dict() 
            for key, spec in self.conductors.items()
        }
    
    def get_by_material(self, material: str) -> Dict[str, ConductorSpec]:
        """
        Get all conductors of a specific material type
        
        Args:
            material: Material type (AAC, ABC, ACSR)
            
        Returns:
            Dictionary of matching conductors
        """
        return {
            key: spec 
            for key, spec in self.conductors.items()
            if spec.material == material
        }
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """
        Export library to JSON
        
        Args:
            filepath: Optional file path to save JSON
            
        Returns:
            JSON string
        """
        data = self.list_conductors()
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def from_json(self, json_str: str) -> None:
        """
        Load library from JSON
        
        Args:
            json_str: JSON string or filepath
        """
        try:
            # Try to load as file first
            with open(json_str, 'r') as f:
                data = json.load(f)
        except:
            # Load as string
            data = json.loads(json_str)
        
        self.conductors = {}
        for key, spec_dict in data.items():
            self.conductors[key] = ConductorSpec(
                name=spec_dict['name'],
                resistance_ohm_per_km=spec_dict['resistance_ohm_per_km'],
                reactance_ohm_per_km=spec_dict['reactance_ohm_per_km'],
                current_rating_amps=spec_dict['current_rating_amps'],
                cross_section_mm2=spec_dict['cross_section_mm2'],
                material=spec_dict['material']
            )
