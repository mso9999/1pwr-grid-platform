const fs = require('fs');
const path = require('path');

// Read test data
const testDataPath = path.join(__dirname, 'web-app/public/test-map-init.html');
const htmlContent = fs.readFileSync(testDataPath, 'utf8');

// Extract mock data from HTML
const mockDataMatch = htmlContent.match(/const mockData = ({[\s\S]*?});/);
if (!mockDataMatch) {
  console.log('Could not find mock data in test file');
  process.exit(1);
}

// Parse the mock data
const mockDataStr = mockDataMatch[1];
const mockData = eval('(' + mockDataStr + ')');

// Analyze droplines
const connections = mockData.connections || [];
const conductors = mockData.conductors || [];
const poles = mockData.poles || [];

console.log('=== Network Data Analysis ===');
console.log(`Total conductors: ${conductors.length}`);
console.log(`Total connections: ${connections.length}`);
console.log(`Total poles: ${poles.length}`);

// Create connection ID set for fast lookup
const connectionIds = new Set(connections.map(c => c.id));

// Count droplines (conductors that connect to connections)
const droplines = conductors.filter(conductor => {
  const isFromConnection = connectionIds.has(conductor.from);
  const isToConnection = connectionIds.has(conductor.to);
  return isFromConnection || isToConnection;
});

console.log(`\n=== Dropline Analysis ===`);
console.log(`Found ${droplines.length} droplines`);

// Show sample droplines
if (droplines.length > 0) {
  console.log('\nSample droplines:');
  droplines.slice(0, 5).forEach(dl => {
    const fromType = connectionIds.has(dl.from) ? 'connection' : 'pole';
    const toType = connectionIds.has(dl.to) ? 'connection' : 'pole';
    console.log(`  ${dl.id}: ${dl.from} (${fromType}) -> ${dl.to} (${toType})`);
  });
}

// Check if connections have coordinates
const connectionsWithCoords = connections.filter(c => c.lat && c.lng);
console.log(`\n=== Connection Coordinates ===`);
console.log(`Connections with coordinates: ${connectionsWithCoords.length}/${connections.length}`);

if (connectionsWithCoords.length === 0) {
  console.log('WARNING: No connections have coordinates! Droplines cannot be rendered.');
} else {
  console.log('Sample connection coordinates:');
  connectionsWithCoords.slice(0, 3).forEach(c => {
    console.log(`  ${c.id}: [${c.lat}, ${c.lng}]`);
  });
}
