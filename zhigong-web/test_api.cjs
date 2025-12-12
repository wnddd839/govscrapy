const http = require('http');

const options1 = {
  hostname: 'localhost',
  port: 8080,
  path: '/public-info/category/data?categoryTag=%E4%BA%BA%E4%BA%8B%E4%BB%BB%E5%85%8D&page=1&size=20',
  method: 'GET',
};

const options2 = {
  hostname: 'localhost',
  port: 8080,
  path: '/api/public-info/category/data?categoryTag=%E4%BA%BA%E4%BA%8B%E4%BB%BB%E5%85%8D&page=1&size=20',
  method: 'GET',
};

function makeRequest(label, options) {
  const req = http.request(options, (res) => {
    console.log(`${label} Status Code: ${res.statusCode}`);
    res.on('data', (d) => {
        // consume data
    });
  });

  req.on('error', (e) => {
    console.error(`${label} Error: ${e.message}`);
  });

  req.end();
}

makeRequest('Without /api', options1);
makeRequest('With /api', options2);
