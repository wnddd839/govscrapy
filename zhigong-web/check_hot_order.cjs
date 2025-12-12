const axios = require('axios');

const API_BASE_URL = 'http://localhost:8080/api';

async function checkHotListOrder() {
  console.log('--- Checking Hot List Order ---');
  try {
    const res = await axios.get(`${API_BASE_URL}/public-info/hot/list`);
    
    let list = [];
    if (res.data && res.data.code === 200) {
        list = res.data.data || [];
    } else if (Array.isArray(res.data)) {
        list = res.data;
    }

    console.log(`Received ${list.length} items.`);
    
    if (list.length === 0) {
        console.log('List is empty.');
        return;
    }

    console.log('First Item Structure:', JSON.stringify(list[0], null, 2));

    list.forEach((item, index) => {
        // Try to find any date field
        const date = item.publishTime || item.publish_time || item.publishDate || item.publish_date || item.create_time || item.date;
        console.log(`[${index}] Date: ${date} | Title: ${item.title}`);
    });

    // Check if sorted
    let isSorted = true;
    for (let i = 0; i < list.length - 1; i++) {
        const date1 = list[i].publishTime || list[i].publish_time || list[i].publishDate || list[i].publish_date || list[i].create_time || list[i].date;
        const date2 = list[i+1].publishTime || list[i+1].publish_time || list[i+1].publishDate || list[i+1].publish_date || list[i+1].create_time || list[i+1].date;
        
        if (date1 && date2) {
            if (new Date(date1) < new Date(date2)) {
                isSorted = false;
                console.log(`Order Violation at index ${i}: ${date1} is older than ${date2}`);
            }
        }
    }

    if (isSorted) {
        console.log('\nData IS sorted correctly (Newest First).');
    } else {
        console.log('\nData is NOT sorted correctly.');
    }

  } catch (error) {
    console.error('Request Failed:', error.message);
  }
}

checkHotListOrder();
