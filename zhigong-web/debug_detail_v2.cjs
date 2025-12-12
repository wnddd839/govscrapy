const axios = require('axios');

console.log('Script started');

const API_BASE_URL = 'http://localhost:8080/api/public-info';

async function testDetail() {
  try {
    // 1. Get category data (MySQL source)
    console.log('Fetching category data...');
    const listRes = await axios.get(`${API_BASE_URL}/category/data`, {
      params: { categoryTag: '人事任免', size: 5, source: 'mysql' }
    });
    
    const items = listRes.data.data.content;
    if (!items || items.length === 0) {
      console.error('No items found in category list!');
      return;
    }

    const firstItem = items[0];
    console.log('First item from list:', {
      id: firstItem.id,
      dataId: firstItem.dataId,
      title: firstItem.title,
      category: firstItem.category
    });

    // 2. Fetch detail using dataId
    const dataId = firstItem.dataId;
    const id = firstItem.id;

    if (dataId) {
        console.log(`\nFetching detail for dataId: ${dataId} (source=mysql)...`);
        try {
            const detailRes = await axios.get(`${API_BASE_URL}/detail/data/${dataId}`, {
                params: { source: 'mysql' }
            });
            const detailData = detailRes.data.data;
            if (detailData) {
              console.log('Detail API Response (by dataId):', {
                  id: detailData.id,
                  dataId: detailData.dataId,
                  title: detailData.title
              });
            } else {
              console.error('Detail API returned empty data (by dataId)!');
            }
        } catch (e) {
            console.error('Error fetching by dataId:', e.message);
        }
    } else {
        console.error('\nItem has no dataId!');
    }

    if (id) {
        console.log(`\nFetching detail for id: ${id} (source=mysql)...`);
        try {
            const detailRes = await axios.get(`${API_BASE_URL}/detail/data/${id}`, {
                params: { source: 'mysql' }
            });
            const detailData = detailRes.data.data;
            if (detailData) {
              console.log('Detail API Response (by id):', {
                  id: detailData.id,
                  dataId: detailData.dataId,
                  title: detailData.title
              });
            } else {
              console.error('Detail API returned empty data (by id)!');
            }
        } catch (e) {
             console.error('Error fetching by id:', e.message);
        }
    }

  } catch (error) {
    console.error('Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
}

testDetail();
