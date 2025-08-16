from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime
import tempfile


class ReportExporter:
    """Export network reports to Excel format"""
    
    def export_network_report(self,
                            network_data: Dict[str, Any],
                            voltage_results: Optional[Dict] = None,
                            validation_results: Optional[Dict] = None,
                            site_name: str = "default") -> str:
        """
        Export comprehensive network report to Excel
        
        Args:
            network_data: Network data dictionary
            voltage_results: Voltage calculation results
            validation_results: Validation results
            site_name: Name of the site
            
        Returns:
            Path to generated Excel file
        """
        # Create temporary Excel file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            # Export poles
            if network_data.get('poles'):
                df_poles = pd.DataFrame(network_data['poles'])
                df_poles.to_excel(writer, sheet_name='Poles', index=False)
            
            # Export conductors
            if network_data.get('conductors'):
                df_conductors = pd.DataFrame(network_data['conductors'])
                df_conductors.to_excel(writer, sheet_name='Conductors', index=False)
            
            # Export connections
            if network_data.get('connections'):
                df_connections = pd.DataFrame(network_data['connections'])
                df_connections.to_excel(writer, sheet_name='Connections', index=False)
            
            # Export voltage results
            if voltage_results and voltage_results.get('conductor_voltages'):
                voltage_data = []
                for conductor_id, voltage_info in voltage_results['conductor_voltages'].items():
                    voltage_data.append({
                        'conductor_id': conductor_id,
                        'voltage_drop_percent': voltage_info.get('voltage_drop_percent'),
                        'voltage_drop_volts': voltage_info.get('voltage_drop_volts'),
                        'end_voltage': voltage_info.get('end_voltage')
                    })
                df_voltage = pd.DataFrame(voltage_data)
                df_voltage.to_excel(writer, sheet_name='Voltage Analysis', index=False)
            
            # Export validation results
            if validation_results:
                validation_summary = {
                    'Metric': [],
                    'Value': []
                }
                
                if validation_results.get('statistics'):
                    stats = validation_results['statistics']
                    validation_summary['Metric'].append('Total Poles')
                    validation_summary['Value'].append(stats.get('total_poles', 0))
                    validation_summary['Metric'].append('Total Conductors')
                    validation_summary['Value'].append(stats.get('total_conductors', 0))
                    validation_summary['Metric'].append('Validation Rate')
                    validation_summary['Value'].append(f"{stats.get('validation_rate', 0):.1f}%")
                
                validation_summary['Metric'].append('Orphaned Poles')
                validation_summary['Value'].append(len(validation_results.get('orphaned_poles', [])))
                validation_summary['Metric'].append('Invalid Conductors')
                validation_summary['Value'].append(len(validation_results.get('invalid_conductors', [])))
                validation_summary['Metric'].append('Duplicate Pole IDs')
                validation_summary['Value'].append(len(validation_results.get('duplicate_pole_ids', [])))
                
                df_validation = pd.DataFrame(validation_summary)
                df_validation.to_excel(writer, sheet_name='Validation Summary', index=False)
                
                # Export detailed validation issues
                if validation_results.get('invalid_conductors'):
                    df_invalid = pd.DataFrame(validation_results['invalid_conductors'])
                    df_invalid.to_excel(writer, sheet_name='Invalid Conductors', index=False)
            
            # Add metadata sheet
            metadata = {
                'Field': ['Site Name', 'Export Date', 'Total Elements'],
                'Value': [
                    site_name,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    len(network_data.get('poles', [])) + len(network_data.get('conductors', []))
                ]
            }
            df_metadata = pd.DataFrame(metadata)
            df_metadata.to_excel(writer, sheet_name='Metadata', index=False)
        
        return temp_path
