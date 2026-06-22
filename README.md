# Libelula Cuartiario

Microservicio cuartiario para la pasarela de pagos Libelula. Actua como proxy entre los clientes y la API de Libelula, validando API keys por proyecto y gestionando suscripciones por vencimiento.

## Arquitectura

- **FastAPI** + **Mangum** (adaptador Lambda)
- **PostgreSQL** en Neon (serverless)
- **Serverless Framework** para deploy en AWS Lambda + API Gateway
- Despliegue local con `serverless deploy`

## Endpoints

### GET /health

Health check del servicio. No requiere autenticacion.

**Response:**

```json
{"status":"ok","libelula_appkey_configured":true,"libelula_api_url":"https://api.libelula.bo"}
```

### POST /api/libelula/deuda/registrar

Registra una deuda en Libelula. Requiere `api_key` en el body.

**Request:**

```json
{
  "email_cliente": "cliente@ejemplo.com",
  "identificador": "FACT-001",
  "nombre_cliente": "Juan",
  "apellido_cliente": "Perez",
  "descripcion": "Pago de mensualidad",
  "api_key": "lib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "lineas_detalle_deuda": [
    {
      "concepto": "Mensualidad Junio",
      "cantidad": 1,
      "costo_unitario": 50.00,
      "codigo_producto": "PROD-001"
    }
  ]
}
```

**Validaciones:**

| Condicion | HTTP | detail |
|---|---|---|
| `api_key` no existe o proyecto inactivo | 401 | API Key invalida o proyecto inactivo |
| Proyecto tiene `Pago.fecha_fin` vencido | 403 | Proyecto desactivado por fecha de vencimiento de pago |
| Body incompleto o campo invalido | 422 | Detalle del campo faltante/incorrecto |
| Error interno (BD, timeout, etc.) | 500 | Mensaje del error real |

**Comportamiento:**

- `api_key`, `callback_url` y `url_retorno` del body son ignorados y reemplazados por los valores de la tabla `proyecto`
- El `callback_url` que se envia a Libelula es `{SELF_URL}/callback/{proyecto.id}`
- `costo_unitario` se sobrescribe a **0.10** (limite de Libelula para pruebas)
- Si el proyecto tiene `retorno_url` en BD, se usa como `url_retorno`
- El `identificador` del body se usa para detectar deudas duplicadas via Libelula (campo `existente` en la respuesta)

**Response (200):**

```json
{
  "error": 0,
  "existente": 0,
  "mensaje": "Deuda registrada con exito. Para completar el pago, debe redireccionar al cliente a la pasarela de pagos.",
  "codigo_recaudacion": "720013951628",
  "id_transaccion": "267caff8-f08e-4d89-a7ff-47f85a77fc82",
  "qr_simple_url": "https://pagos.libelula.bo/QrImages/...",
  "url_pasarela_pagos": "https://pagos.libelula.bo/?id=..."
}
```

### GET /callback/{proyecto_id}

Recibe el callback de Libelula cuando un pago se completa. Es invocado automaticamente por Libelula.

**Libelula llama a:**

```
GET {SELF_URL}/callback/1?transaction_id=267caff8-...
```

**El cuartiario reenvia a:**

```
GET {proyecto.callback_url}?transaction_id=267caff8-...
```

Si el forward falla (ej: el servidor del proyecto no responde), el error se ignora y el callback se marca como recibido.

## Flujo completo

```
Cliente                    Cuartiario (Lambda)              Libelula API
  |                              |                              |
  | POST /deuda/registrar        |                              |
  | api_key + identificador +... |                              |
  |----------------------------->|                              |
  |                              | Valida api_key en BD         |
  |                              | Valida fecha_fin no vencido  |
  |                              | Reemplaza callback_url por   |
  |                              |   SELF_URL/callback/{id}     |
  |                              | Override costo_unitario=0.10  |
  |                              | POST /rest/deuda/registrar   |
  |                              |---------------------------->|
  |                              |                              |
  | url_pasarela_pagos <---------| <-- response de Libelula ----|
  |                              |                              |
  | Redirige cliente a           |                              |
  | url_pasarela_pagos           |                              |
  |                              |                              |
  |           ... cliente paga en la pasarela ...              |
  |                              |                              |
  |                              | GET /callback/{id}           |
  |                              | ?transaction_id=xxx          |
  |                              |<-----------------------------|
  |                              |                              |
  |                              | GET proyecto.callback_url    |
  |                              | ?transaction_id=xxx          |
  |                              | (reenvia a tu webhook)       |
  |                              |                              |
```

## Modelo de datos

### usuario

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER PK | Autoincremental |
| nombre | VARCHAR(255) | Nombre del usuario/dueno |
| registro | TIMESTAMP | Fecha de registro (automatico) |

### proyecto

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER PK | Autoincremental |
| nombre | VARCHAR(255) | Nombre del proyecto |
| api_key | VARCHAR(255) UNIQUE | API Key para autenticar peticiones |
| callback_url | VARCHAR(500) UNIQUE | URL donde se reenvian los callbacks de pago |
| retorno_url | VARCHAR(500) | URL de redireccion post-pago (opcional) |
| usuario_id | INTEGER FK | Referencia a usuario.id |
| activo | BOOLEAN | Si el proyecto esta activo (default true) |

### pago

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| id | INTEGER PK | Autoincremental |
| fecha_inicio | TIMESTAMP | Inicio del periodo de suscripcion |
| fecha_fin | TIMESTAMP | Fin del periodo (vencimiento de suscripcion) |
| monto | NUMERIC(10,2) | Monto de la suscripcion |
| usuario_id | INTEGER FK | Referencia a usuario.id |
| proyecto_id | INTEGER FK | Referencia a proyecto.id |

**Nota:** La tabla `pago` es para suscripciones del proyecto, no para transacciones de Libelula. Mientras exista al menos un `pago` con `fecha_fin` futuro, el proyecto esta activo.

## Seed inicial

```sql
-- Crear usuario
INSERT INTO usuario (nombre) VALUES ('Admin Universidad');

-- Crear proyecto con api_key y callback
INSERT INTO proyecto (nombre, api_key, callback_url, retorno_url, usuario_id, activo)
VALUES (
    'Proyecto Universitario',
    'lib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    'https://miservicio.com/callback',
    'https://miservicio.com/pago-exitoso',
    1,
    TRUE
);

-- Insertar suscripcion con fecha_fin futuro
INSERT INTO pago (fecha_inicio, fecha_fin, monto, usuario_id, proyecto_id)
VALUES ('2026-01-01', '2027-12-31', 100, 1, 1);
```

## Variables de entorno

| Variable | Default | Descripcion |
|----------|---------|-------------|
| DATABASE_URL | - | Conexion a PostgreSQL (Neon) |
| LIBELULA_APPKEY | - | AppKey de Libelula |
| LIBELULA_API_URL | https://api.libelula.bo | URL base de la API de Libelula |
| SELF_URL | - | URL publica del API Gateway (sin /dev) |

## Deploy local

```bash
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales reales
serverless deploy
```

## Logs

```bash
serverless logs -f api --startTime 1h    # ultima hora
serverless logs -f api -t                # tail en vivo
```

## Probar con curl

```bash
# Health
curl https://tu-api-gateway.execute-api.us-east-1.amazonaws.com/dev/health

# Registrar deuda
curl -s -X POST https://tu-api-gateway.execute-api.us-east-1.amazonaws.com/dev/api/libelula/deuda/registrar \
  -H "Content-Type: application/json" \
  -d '{
    "email_cliente": "test@test.com",
    "identificador": "FACT-001",
    "descripcion": "Prueba",
    "api_key": "lib-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "lineas_detalle_deuda": [
      {"concepto": "Prueba", "cantidad": 1, "costo_unitario": 50}
    ]
  }'

# Simular callback (lo que hace Libelula al pagar)
curl "https://tu-api-gateway.execute-api.us-east-1.amazonaws.com/dev/callback/1?transaction_id=test-123"
```

## Probar con Postman

**Endpoint:** `POST https://tu-api-gateway.execute-api.us-east-1.amazonaws.com/dev/api/libelula/deuda/registrar`
**Headers:** `Content-Type: application/json`
**Body:** raw JSON con `api_key` incluida
