CREATE DATABASE IF NOT EXISTS Document_Classifier;
USE Document_Classifier;

-- USERS TABLE
Drop table if exists users;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL
);
