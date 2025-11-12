-- Redis Lua script for atomic TPM (tokens per minute) budget reservation
-- KEYS[1] = "tpm:<key_id>"
-- ARGV[1] = window (current minute timestamp)
-- ARGV[2] = tpm_limit
-- ARGV[3] = tokens_required

local key = KEYS[1]
local window = ARGV[1]
local limit = tonumber(ARGV[2])
local required = tonumber(ARGV[3])

-- Get current window from Redis
local cur_window = redis.call('HGET', key, 'window')

if cur_window == window then
    -- Same window - check if we have budget
    local used = tonumber(redis.call('HGET', key, 'used') or '0')
    if used + required > limit then
        -- Over budget
        return 0
    else
        -- Reserve tokens and allow
        redis.call('HINCRBY', key, 'used', required)
        return 1
    end
else
    -- New window - reset counter
    redis.call('HSET', key, 'window', window, 'used', required)
    -- Set expiry to 2 minutes to auto-cleanup old windows
    redis.call('EXPIRE', key, 120)
    return 1
end
