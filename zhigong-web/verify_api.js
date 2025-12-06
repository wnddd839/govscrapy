import http from 'http';

const options = {
  hostname: 'localhost',
  port: 8080,
  path: '/api/public-info/hot?size=1',
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
};

const req = http.request(options, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    try {
      const parsedData = JSON.parse(data);
      // console.log('Response structure:', JSON.stringify(parsedData, null, 2));
      if (parsedData.items && parsedData.items.length > 0) {
        const item = parsedData.items[0];
        console.log('First item keys:', Object.keys(item));
        console.log('Date fields:', {
            publishDateTime: item.publishDateTime,
            publishDate: item.publishDate,
            publish_date: item.publish_date,
            createTime: item.createTime,
            crawlTime: item.crawlTime,
            createdAt: item.createdAt,
            updatedAt: item.updatedAt
        });
      } else if (Array.isArray(parsedData) && parsedData.length > 0) {
          const item = parsedData[0];
          console.log('First item keys:', Object.keys(item));
          console.log('Date fields:', {
              publishDateTime: item.publishDateTime,
              publishDate: item.publishDate,
              publish_date: item.publish_date,
              createTime: item.createTime,
              crawlTime: item.crawlTime,
              createdAt: item.createdAt,
              updatedAt: item.updatedAt
          });
      } else {
          console.log('Structure unknown:', Object.keys(parsedData));
      }
    } catch (e) {
      console.error('Error parsing JSON:', e);
      console.log('Raw data:', data);
    }
  });
});

req.on('error', (e) => {
  console.error(`Problem with request: ${e.message}`);
});

req.end();
