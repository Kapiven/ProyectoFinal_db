# ProyectoFinal_db
## Autores
**Karen Pineda y Pablo Méndez**

# Sistema de Gestión de Inventario y Ventas

Este proyecto es un sistema de gestión básico desarrollado en Python utilizando SQLAlchemy para la interacción con una base de datos PostgreSQL. Incluye la definición de un esquema de base de datos relacional, TypeDecorators personalizados, funciones y triggers SQL, generación de reportes y una aplicación de consola con operaciones CRUD completas para entidades clave.

## Características Principales

* **Modelado de Datos:** Definición de tablas como `Productos`, `Clientes`, `Empleados`, `Pedidos`, `Ventas`, `Inventario`, etc., utilizando SQLAlchemy ORM.
* **TypeDecorators Personalizados:** Implementación de tipos de datos personalizados para DNI, Email, Teléfono, JSON y Moneda, para una mejor validación y normalización de datos.
* **Funciones y Triggers SQL:** Automatización de cálculos (ej. totales de pedidos/compras) y gestión de inventario a través de triggers y funciones de PostgreSQL.
* **Vistas SQL:** Creación de vistas personalizadas en la base de datos para una recuperación de datos simplificada y optimizada en ciertas operaciones.
* **Reportes:** Generación de 3 tipos de reportes con múltiples filtros y exportación a CSV.
* **CRUD Completo:** Aplicación de consola interactiva con operaciones de Crear, Leer, Actualizar y Eliminar para `Productos`, `Clientes` y `Empleados`. Las vistas de índice (listado) se basan en Vistas SQL.

## Requisitos

Para ejecutar este proyecto, necesitas tener instalado:

* **Python 3.x**
* **PostgreSQL** (Servidor de Base de Datos)

### Dependencias de Python

Puedes instalar las dependencias de Python usando `pip`:

```bash
pip install sqlalchemy psycopg2-binary faker
```

## Estructura del Proyecto

**database.py:** Define el esquema de la base de datos (modelos ORM), los TypeDecorators personalizados y la conexión a la base de datos.

**queries.py:** Contiene las definiciones de las funciones SQL, triggers y vistas SQL que interactúan con la base de datos.

**inserts.py:** Script para generar e insertar datos de prueba en la base de datos.

**reports.py:** Contiene la lógica para generar los 3 reportes, aplicar filtros y exportar a CSV.

**app.py:** La aplicación principal de consola que proporciona las interfaces CRUD.