const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

// WebSocket server setup
const wss = new WebSocket.Server({ port: 8080 });

// Path to flag_counter.json
const counterFilePath = path.join(__dirname, 'flag_counter.json');

// Function to read the current flag count
function readFlagCount() {
  try {
    const data = fs.readFileSync(counterFilePath, 'utf8');
    const jsonData = JSON.parse(data);
    return jsonData.count || 0;
  } catch (error) {
    console.error('Error reading flag count:', error);
    return 0;
  }
}

// WebSocket connection handling
wss.on('connection', (ws) => {
  console.log('Client connected');
  
  // Send the initial flag count to the client
  ws.send(JSON.stringify({ count: readFlagCount() }));

  // Send the flag count every 1 second
  const interval = setInterval(() => {
    ws.send(JSON.stringify({ count: readFlagCount() }));
  }, 1000);

  // Clean up when the connection is closed
  ws.on('close', () => {
    clearInterval(interval);
    console.log('Client disconnected');
  });
});

console.log('WebSocket server is running on ws://localhost:8080');
