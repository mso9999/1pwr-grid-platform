/**
 * Status Code Mappings per MGD045V03 SOP
 * SC1: Poles construction progress
 * SC2: Poles further progress
 * SC3: Connections status
 * SC4: Lines/Conductors status
 * SC5: Generation elements status
 */

// SC1: Pole Construction Progress (0-9)
export const SC1_DESCRIPTIONS: { [key: number]: string } = {
  0: 'uGridNET output (as designed)',
  1: 'Updated planned location',
  2: 'Marked with label onsite',
  3: 'Consent withheld',
  4: 'Consented',
  5: 'Hard Rock',
  6: 'Excavated',
  7: 'Pole planted',
  8: 'Poletop dressed',
  9: 'Conductor attached'
}

export const SC1_COLORS: { [key: number]: string } = {
  0: '#FFFFFF', // White
  1: '#FFFF00', // Yellow
  2: '#ccffd2', // Light green
  3: '#FF0000', // Red
  4: '#95F985', // Green
  5: '#000000', // Black
  6: '#38fb14', // Bright green
  7: '#26d102', // Green
  8: '#018501', // Dark green
  9: '#014803', // Very dark green
}

// SC2: Pole Further Progress (string codes)
export const SC2_DESCRIPTIONS: { [key: string]: string } = {
  'NA': 'None',
  'SP': 'Stay wires planned',
  'SI': 'Stay wires installed',
  'KP': 'Kicker pole planned',
  'KI': 'Kicker pole installed',
  'TP': 'Transformer planned',
  'TI': 'Transformer installed',
  'TC': 'Transformer commissioned',
  'MP': 'Meter planned',
  'MI': 'Meter installed',
  'MC': 'Meter commissioned',
  'EP': 'Earth planned',
  'EI': 'Earth installed'
}

// SC3: Connection Status (0-10)
export const SC3_DESCRIPTIONS: { [key: number]: string } = {
  0: 'uGridNET Survey',
  1: 'Updated Location',
  2: 'Connection fee paid',
  3: 'Ready board paid',
  4: 'Contract Signed',
  5: 'DB Tested',
  6: 'Ready Board Installed',
  7: 'Cable pulled',
  8: 'Cable connected',
  9: 'Customer Connected',
  10: 'Energized'
}

export const SC3_COLORS: { [key: number]: string } = {
  0: '#adadff', // Light blue
  1: '#FFD700', // Gold
  2: '#DAA520', // Goldenrod
  3: '#D8BFD8', // Thistle
  4: '#DDA0DD', // Plum
  5: '#BA55D3', // Medium orchid
  6: '#9370DB', // Medium purple
  7: '#8B008B', // Dark magenta
  8: '#4B0082', // Indigo
  9: '#000080', // Navy
  10: '#00008B', // Dark blue
}

// SC4: Line/Conductor Status (0-5)
export const SC4_DESCRIPTIONS: { [key: number]: string } = {
  0: 'Planned',
  1: 'Material on site',
  2: 'Stringing in progress',
  3: 'Strung',
  4: 'Sagged and tensioned',
  5: 'Energized'
}

export const SC4_COLORS: { [key: number]: string } = {
  0: '#808080', // Gray
  1: '#FFA500', // Orange
  2: '#FFFF00', // Yellow
  3: '#90EE90', // Light green
  4: '#008000', // Green
  5: '#00FF00', // Lime
}

// SC5: Generation Elements Status (0-6)
export const SC5_DESCRIPTIONS: { [key: number]: string } = {
  0: 'Planned',
  1: 'Site prepared',
  2: 'Foundation completed',
  3: 'Equipment installed',
  4: 'Grid connected',
  5: 'Commissioned',
  6: 'Operational'
}

export const SC5_COLORS: { [key: number]: string } = {
  0: '#C0C0C0', // Silver
  1: '#FFE4B5', // Moccasin
  2: '#F0E68C', // Khaki
  3: '#90EE90', // Light green
  4: '#00FA9A', // Medium spring green
  5: '#00CED1', // Dark turquoise
  6: '#0000FF', // Blue
}

/**
 * Get the installation status based on SC1 value
 */
export function getInstallationStatus(sc1: number): 'as_designed' | 'planned' | 'installed' {
  if (sc1 === 0) return 'as_designed'
  if (sc1 >= 1 && sc1 <= 6) return 'planned'
  if (sc1 >= 7 && sc1 <= 9) return 'installed'
  return 'as_designed'
}

/**
 * Format status code display with description
 */
export function formatStatusCode(
  value: number | string,
  type: 'SC1' | 'SC2' | 'SC3' | 'SC4' | 'SC5'
): string {
  switch (type) {
    case 'SC1':
      return `${value}: ${SC1_DESCRIPTIONS[value as number] || 'Unknown'}`
    case 'SC2':
      return `${value}: ${SC2_DESCRIPTIONS[value as string] || 'Unknown'}`
    case 'SC3':
      return `${value}: ${SC3_DESCRIPTIONS[value as number] || 'Unknown'}`
    case 'SC4':
      return `${value}: ${SC4_DESCRIPTIONS[value as number] || 'Unknown'}`
    case 'SC5':
      return `${value}: ${SC5_DESCRIPTIONS[value as number] || 'Unknown'}`
    default:
      return String(value)
  }
}

/**
 * Determine line type based on voltage level or connection pattern
 */
export function getLineType(conductor: any, poles: any[], connections: any[]): 'mv' | 'lv' | 'drop' {
  const fromNode = conductor.from
  const toNode = conductor.to
  
  // Check if it's a drop line (connects to a connection)
  const isFromConnection = connections.some(c => c.id === fromNode)
  const isToConnection = connections.some(c => c.id === toNode)
  
  if (isFromConnection || isToConnection) {
    return 'drop'
  }
  
  // Check voltage level from poles
  const fromPole = poles.find(p => p.id === fromNode)
  const toPole = poles.find(p => p.id === toNode)
  
  // If either pole is MV type, it's an MV line
  if (fromPole?.type === 'MV' || toPole?.type === 'MV') {
    return 'mv'
  }
  
  // Default to LV for pole-to-pole connections
  return 'lv'
}

// Helper functions to get narrative descriptions
export function getSC1Narrative(code: number): string {
  return SC1_DESCRIPTIONS[code] || 'Unknown status'
}

export function getSC2Narrative(code: string): string {
  return SC2_DESCRIPTIONS[code] || 'Unknown status'
}

export function getSC3Narrative(code: number): string {
  return SC3_DESCRIPTIONS[code] || 'Unknown status'
}

export function getSC4Narrative(code: number): string {
  return SC4_DESCRIPTIONS[code] || 'Unknown status'
}

export function getSC5Narrative(code: number): string {
  return SC5_DESCRIPTIONS[code] || 'Unknown status'
}

// Generic function to get status code narrative
export function getStatusCodeNarrative(code: string, value: number | string): string {
  switch(code) {
    case 'SC1':
      return getSC1Narrative(typeof value === 'number' ? value : parseInt(value as string));
    case 'SC2':
      return getSC2Narrative(value as string);
    case 'SC3':
      return getSC3Narrative(typeof value === 'number' ? value : parseInt(value as string));
    case 'SC4':
      return getSC4Narrative(typeof value === 'number' ? value : parseInt(value as string));
    case 'SC5':
      return getSC5Narrative(typeof value === 'number' ? value : parseInt(value as string));
    default:
      return 'Unknown status';
  }
}
