CREATE TABLE IF NOT EXISTS spp_elements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id INT REFERENCES spp_elements(id),
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE NOT NULL,
    valid_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);


CREATE TABLE IF NOT EXISTS department_spp_links (
    id SERIAL PRIMARY KEY,
    department_id INT REFERENCES departments(id),
    spp_element_id INT REFERENCES spp_elements(id)
);


CREATE TABLE IF NOT EXISTS calculations (
    id SERIAL PRIMARY KEY,
    calc_id UUID,
    session_id UUID,
    status TEXT,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO spp_elements (code, name, parent_id, is_active, valid_from, valid_to)
VALUES
('ROOT', 'Компания', NULL, TRUE, '2024-01-01', '2025-12-31'),

('BUR', 'Бурение', 1, TRUE, '2024-01-01', '2025-12-31'),
('DOB', 'Добыча', 1, TRUE, '2024-01-01', '2025-12-31'),

('BUR-1', 'Участок 1', 2, TRUE, '2024-01-01', '2025-12-31'),
('BUR-2', 'Участок 2', 2, TRUE, '2024-01-01', '2025-12-31'),

('DOB-1', 'Скважина 1', 3, TRUE, '2024-01-01', '2025-12-31'),
('DOB-2', 'Скважина 2', 3, TRUE, '2024-01-01', '2025-12-31');


INSERT INTO spp_elements (code, name, parent_id, is_active, valid_from, valid_to)
VALUES
('NEW_ROOT', 'Компания', NULL, TRUE, '2025-01-01', '2026-12-31'),

('NEW_BUR', 'Бурение', 8, TRUE, '2025-01-01', '2026-12-31'),
('NEW_DOB', 'Добыча', 8, TRUE, '2025-01-01', '2026-12-31'),

('NEW_UCH', 'Новый участок', 9, TRUE, '2025-01-01', '2026-12-31');


INSERT INTO departments (name)
VALUES
('IT'),
('Finance'),
('Operations');


INSERT INTO department_spp_links (department_id, spp_element_id)
VALUES
(1, 2),
(1, 4),
(2, 3),
(3, 6);