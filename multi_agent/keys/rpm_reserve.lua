-- Redis Lua script for atomic RPM (requests per minute) slot reservation
-- KEYS[1] = "rpm:<key_id>"
-- ARGV[1] = window (current minute timestamp)
-- ARGV[2] = rpm_limit

local key = KEYS[1]
local window = ARGV[1]
local limit = tonumber(ARGV[2])

-- Get current window from Redis
local cur_window = redis.call('HGET', key, 'window')

if cur_window == window then
    -- Same window - check if we can increment
    local cnt = tonumber(redis.call('HGET', key, 'count') or '0')
    if cnt + 1 > limit then
        -- Over limit
        return 0
    else
        -- Increment and allow
        redis.call('HINCRBY', key, 'count', 1)
        return 1
    end
else
    -- New window - reset counter
    redis.call('HSET', key, 'window', window, 'count', 1)
    -- Set expiry to 2 minutes to auto-cleanup old windows
    redis.call('EXPIRE', key, 120)
    return 1
end
