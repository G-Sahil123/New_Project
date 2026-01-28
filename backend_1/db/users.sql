-- users_mysql.sql
CREATE DATABASE IF NOT EXISTS documind_ai;
USE documind_ai;

CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

CREATE TABLE user_sessions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_sessions_token (session_token),
    INDEX idx_sessions_expires (expires_at)
);

CREATE TABLE document_folders (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_folders_user (user_id)
);

CREATE TABLE processed_documents (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    folder_id CHAR(36) NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    document_type ENUM('invoice', 'resume', 'form', 'letter', 'news_article', 'email') NOT NULL,
    extracted_data JSON NOT NULL,
    summary TEXT,
    processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (folder_id) REFERENCES document_folders(id) ON DELETE SET NULL,
    INDEX idx_documents_user (user_id),
    INDEX idx_documents_folder (folder_id),
    INDEX idx_documents_type (document_type),
    INDEX idx_documents_created (created_at),
    INDEX idx_documents_status (processing_status)
);

-- Create default folders procedure
DELIMITER //
CREATE PROCEDURE CreateDefaultFolders(IN user_id CHAR(36))
BEGIN
    -- Use single INSERT with multiple VALUES
    INSERT INTO document_folders (user_id, name) 
    VALUES 
        (user_id, 'Emails'),
        (user_id, 'Forms'),
        (user_id, 'Resumes'),
        (user_id, 'Invoices'),
        (user_id, 'Letters'),
        (user_id, 'News_articles');
END//
DELIMITER ;