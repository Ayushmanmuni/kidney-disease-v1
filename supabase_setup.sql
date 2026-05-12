-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  password VARCHAR(200) NOT NULL,
  profile_pic VARCHAR(200),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Prediction history
CREATE TABLE IF NOT EXISTS prediction_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  patient_name VARCHAR(100),
  result VARCHAR(50) NOT NULL,
  probability_ckd FLOAT NOT NULL,
  input_data TEXT,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Feedback reports
CREATE TABLE IF NOT EXISTS feedback_reports (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  name VARCHAR(100),
  email VARCHAR(120),
  category VARCHAR(30) NOT NULL DEFAULT 'bug',
  message TEXT NOT NULL,
  page_url VARCHAR(500),
  user_agent VARCHAR(300),
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
