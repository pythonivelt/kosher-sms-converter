const http = require('http');
const fs = require('fs');
const path = require('path');
const dir = __dirname;
http.createServer((req, res) => {
  let file = req.url.split('?')[0];
  if (file === '/') file = '/fig-to-sms-converter.html';
  const fp = path.join(dir, decodeURIComponent(file));
  const ext = path.extname(fp).toLowerCase();
  const types = {'.html':'text/html','.js':'application/javascript','.css':'text/css','.json':'application/json'};
  fs.readFile(fp, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, {'Content-Type': types[ext] || 'application/octet-stream'});
    res.end(data);
  });
}).listen(3847, () => console.log('Serving on http://localhost:3847'));
