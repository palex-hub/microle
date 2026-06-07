-- Insertar usuario administrador
INSERT INTO usuario (nombre) VALUES ('Admin Universidad');

-- Insertar proyecto de prueba
INSERT INTO proyecto (nombre, api_key, callback_url, retorno_url, usuario_id, activo)
VALUES (
    'Proyecto Universitario',
    'lib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'https://tu-backend.com/callback',
    'https://tu-frontend.com/pago-exitoso',
    1,
    TRUE
);
