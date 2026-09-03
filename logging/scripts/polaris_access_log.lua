-- polaris_access_log.lua — Fluent Bit Lua filter
--
-- Splits the Quarkus HTTP access-log line out of _msg into typed fields, and only
-- for records whose loggerName is io.quarkus.http.access-log. Every other Polaris
-- record passes through untouched.
--
-- Input _msg, as emitted by the pattern %h %l %u %t "%r" %s %b :
--   192.168.194.1 - root [03/Sep/2026:06:37:47 +0000] "DELETE /api/... HTTP/1.1" 404 133
--   \________/   ^  \__/  \____________________/       \____/ \_____/ \______/   \_/ \_/
--    client_ip   |  user      timestamp (dropped)      method  path   version    |   |
--                |                                                    (dropped)  |   |
--         %l, always "-", dropped                               http_status ------+   |
--                                                              response_size ---------+
--
-- Field names match §7 of logging/polaris-logging-architecture-spec.md so the
-- LogsQL recipes there work unchanged.
--
-- _msg is left in place: it is the raw line, and it is what you read when the
-- parse is wrong.

local ACCESS_LOGGER = "io.quarkus.http.access-log"

-- Lua patterns, not regex. %S non-space, %u uppercase, %d digit, %[ a literal [.
-- The version token inside the quotes is consumed by [^"]* without capturing.
local PATTERN = '^(%S+) %S+ (%S+) %[[^%]]*%] "(%u+) (%S+)[^"]*" (%d+) (%S+)'

function polaris_access_log(tag, timestamp, record)
    if record["loggerName"] ~= ACCESS_LOGGER then
        return 0, timestamp, record          -- 0 = untouched, keep
    end

    local msg = record["_msg"]
    if type(msg) ~= "string" then
        record["access_log_parse_error"] = true
        return 1, timestamp, record
    end

    local ip, user, method, path, status, size = string.match(msg, PATTERN)

    if ip == nil then
        -- Never fail silently: a line from this logger that does not parse is a
        -- pattern change, and it should be findable with
        --   access_log_parse_error:true
        record["access_log_parse_error"] = true
        return 1, timestamp, record
    end

    record["client_ip"]            = ip
    record["user_principal_name"]  = user
    record["http_method"]          = method
    record["api_path"]             = path
    record["http_status"]          = tonumber(status)

    -- %b writes "-" for a zero-byte body, which is CLF for 0, not for unknown.
    record["response_size"]        = tonumber(size) or 0

    return 1, timestamp, record          -- 1 = record modified
end
