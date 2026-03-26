-- Senior Care Monitoring System - PostgreSQL Schema
-- Database: seniorcare

-- Create database (run separately as superuser)
-- CREATE DATABASE seniorcare;

-- Connect to database
\c seniorcare;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 65),
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(255),
    address TEXT,
    emergency_contact VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);

-- Guardians table
CREATE TABLE IF NOT EXISTS guardians (
    guardian_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    relationship VARCHAR(50),  -- 자녀, 친척, 사회복지사 등
    permission_level VARCHAR(20) DEFAULT 'standard' CHECK (permission_level IN ('standard', 'admin')),
    notification_enabled BOOLEAN DEFAULT true,
    push_token TEXT,  -- 푸시 알림 토큰
    device_type VARCHAR(20) CHECK (device_type IN ('ios', 'android')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_guardian UNIQUE (user_id, phone)
);

-- Create indexes for guardians table
CREATE INDEX IF NOT EXISTS idx_guardians_user_id ON guardians(user_id);
CREATE INDEX IF NOT EXISTS idx_guardians_phone ON guardians(phone);

-- Guardian limit check function (최대 5명)
CREATE OR REPLACE FUNCTION check_guardian_limit()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM guardians WHERE user_id = NEW.user_id) >= 5 THEN
        RAISE EXCEPTION 'Maximum 5 guardians allowed per user';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for guardian limit
DROP TRIGGER IF EXISTS guardian_limit_check ON guardians;
CREATE TRIGGER guardian_limit_check
    BEFORE INSERT ON guardians
    FOR EACH ROW
    EXECUTE FUNCTION check_guardian_limit();

-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    log_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,  -- sensor_data, voice_response, manual_check
    device_type VARCHAR(20),  -- mobile, iot, ai_speaker
    device_id VARCHAR(100),
    sensor_type VARCHAR(50),
    value NUMERIC,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for activity_log table
CREATE INDEX IF NOT EXISTS idx_activity_log_user_timestamp ON activity_log(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp ON activity_log(timestamp);

-- Function to delete old activity logs (30일 이상)
CREATE OR REPLACE FUNCTION delete_old_activity_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM activity_log WHERE timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_guardians_updated_at ON guardians;
CREATE TRIGGER update_guardians_updated_at
    BEFORE UPDATE ON guardians
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
-- INSERT INTO users (name, age, phone, email, address) VALUES
-- ('김영희', 75, '010-1234-5678', 'kim@example.com', '서울시 강남구'),
-- ('이철수', 80, '010-2345-6789', 'lee@example.com', '서울시 서초구');

-- INSERT INTO guardians (user_id, name, phone, email, relationship) VALUES
-- ((SELECT user_id FROM users WHERE phone = '010-1234-5678'), '김민수', '010-9876-5432', 'minsu@example.com', '자녀'),
-- ((SELECT user_id FROM users WHERE phone = '010-2345-6789'), '이지은', '010-8765-4321', 'jieun@example.com', '자녀');

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO seniorcare_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO seniorcare_admin;

-- Display table information
\dt
\d users
\d guardians
\d activity_log
