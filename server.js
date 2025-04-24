const WebSocket = require('ws');
const PORT = process.env.PORT || 8080;

const wss = new WebSocket.Server({ port: PORT }, () => {
  console.log(`WebSocket server started on port ${PORT}`);
});

wss.on('connection', (ws) => {
  console.log('Client connected');

  ws.on('message', (message) => {
    console.log('Received:', message);

    try {
      const data = JSON.parse(message);
      // فرضاً می‌خوایم Mock کنیم که اگر userId اومد، یه عدد تصادفی به عنوان newBalance ارسال بشه
      if (data.userId) {
        const fakeBalance = Math.floor(Math.random() * 1000);
        const response = JSON.stringify({
          userId: data.userId,
          newBalance: fakeBalance
        });
        ws.send(response);
      }
    } catch (err) {
      console.error('Invalid JSON received');
    }
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});
