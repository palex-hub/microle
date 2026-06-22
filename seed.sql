-- Insertar usuario administrador
INSERT INTO usuario (nombre) VALUES ('Admin Universidad');

-- Insertar proyecto de prueba
INSERT INTO proyecto (nombre, api_key, callback_url, retorno_url, usuario_id, activo)
VALUES (
    'Proyecto Universitario',
    'lib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'https://webhook.site/8991d236-be6e-4a91-907a-8574896b7a34',
    'https://tusitio.com/pago-exitoso',
    1,
    TRUE
);

-- Insertar suscripcion (fecha_fin futuro para que el proyecto este activo)
INSERT INTO pago (fecha_inicio, fecha_fin, monto, usuario_id, proyecto_id)
VALUES ('2026-01-01', '2027-12-31', 100, 1, 1);
