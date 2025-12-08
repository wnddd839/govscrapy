-- ⚠️ DANGER: This script will WIPE ALL DATA from the Public Info system ⚠️
-- ⚠️ 警告: 此脚本将清空公共信息系统的所有数据 ⚠️

-- 1. MySQL Data Cleanup (MySQL 数据清空)
-- Connect to Database: gov_open (Host: 8.138.24.168)
USE gov_open;

-- Disable safe update mode to allow mass deletion
SET SQL_SAFE_UPDATES = 0;

-- Delete all records from public_info table
TRUNCATE TABLE public_info;
-- OR if TRUNCATE is not allowed: DELETE FROM public_info;

-- Reset auto-increment counter (if using DELETE)
ALTER TABLE public_info AUTO_INCREMENT = 1;

SET SQL_SAFE_UPDATES = 1;

-- 2. Redis Data Cleanup (Redis 数据清空)
-- Connect to Redis (Host: 8.138.24.168, Port: 6379, DB: 1)
-- Run the following commands in Redis Console or CLI:

/*
FLUSHDB
*/

-- OR delete specific keys pattern if you don't want to flush the whole DB:
/*
EVAL "return redis.call('del', unpack(redis.call('keys', 'gov:data*')))" 0
EVAL "return redis.call('del', unpack(redis.call('keys', 'crawl:*')))" 0
EVAL "return redis.call('del', unpack(redis.call('keys', 'hot:*')))" 0
EVAL "return redis.call('del', unpack(redis.call('keys', 'detail:*')))" 0
*/
