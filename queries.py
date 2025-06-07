import psycopg2
from psycopg2 import OperationalError
from database import DATABASE_URL 

def execute_sql_command(sql_command, commit=False):
    """Ejecuta un comando SQL y maneja la conexión."""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="institucion", 
            user="postgres",
            password="datos2025"
        )
        cur = conn.cursor()
        cur.execute(sql_command)
        if commit:
            conn.commit()
        print(f"✅ Comando SQL ejecutado exitosamente:\n{sql_command[:100]}...") # Print de los primeros 100 caracteres
        return cur
    except OperationalError as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        print("Asegúrate de que PostgreSQL está corriendo y los datos de conexión son correctos.")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"❌ Error al ejecutar el comando SQL: {e}")
        if conn: conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def create_sql_functions():
    """Crea funciones SQL en la base de datos."""
    print("\n--- Creando/Actualizando Funciones SQL ---")
    
    # Función para actualizar el total de un Pedido
    execute_sql_command("""
    CREATE OR REPLACE FUNCTION update_pedido_total()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE pedidos
        SET total = (SELECT COALESCE(SUM(subtotal), 0) FROM detalle_pedidos WHERE pedido_id = NEW.pedido_id)
        WHERE id = NEW.pedido_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """, commit=True)

    # Función para actualizar el total de una Compra
    execute_sql_command("""
    CREATE OR REPLACE FUNCTION update_compra_total()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE compras
        SET total = (SELECT COALESCE(SUM(subtotal), 0) FROM detalle_compras WHERE compra_id = NEW.compra_id)
        WHERE id = NEW.compra_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """, commit=True)

    # Función para manejar movimientos de inventario en productos
    execute_sql_command("""
    CREATE OR REPLACE FUNCTION handle_inventario_producto_change()
    RETURNS TRIGGER AS $$
    DECLARE
        v_cantidad INT;
        v_ubicacion VARCHAR;
    BEGIN
        -- Insertar o actualizar en la tabla de inventario por sucursal
        IF TG_OP = 'INSERT' THEN
            -- Se asume que DetalleCompra/DetalleVenta no especifican sucursal directamente.
            -- El stock del producto se actualiza.
            -- Para inventario por sucursal, un movimiento de inventario explícito es necesario.
            NULL; -- El trigger de producto ya maneja el stock total.
        ELSIF TG_OP = 'UPDATE' AND NEW.stock <> OLD.stock THEN
            -- Cuando el stock total del producto cambia, si tenemos inventario por sucursal
            -- podríamos necesitar ajustar o al menos registrar el movimiento.
            -- Esto es más complejo y requiere lógica de dónde viene el cambio (compra, venta, ajuste).
            -- Por ahora, los movimientos de inventario se registran explícitamente o por triggers específicos.
            NULL;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """, commit=True)

    # Función para registrar movimientos de inventario por ventas (salidas)
    execute_sql_command("""
    CREATE OR REPLACE FUNCTION record_venta_inventario_movement()
    RETURNS TRIGGER AS $$
    DECLARE
        v_empleado_id INT;
        v_sucursal_id INT;
        v_producto_id INT;
        v_cantidad_vendida INT;
    BEGIN
        -- Obtener información de la venta
        SELECT empleado_id, sucursal_id INTO v_empleado_id, v_sucursal_id
        FROM ventas
        WHERE id = NEW.venta_id;

        v_producto_id := NEW.producto_id;
        v_cantidad_vendida := NEW.cantidad;

        -- Registrar movimiento de inventario (salida)
        INSERT INTO movimientos_inventario (fecha, tipo, cantidad, motivo, producto_id, empleado_id)
        VALUES (NOW(), 'salida', v_cantidad_vendida, 'Venta (Venta ID: ' || NEW.venta_id || ')', v_producto_id, v_empleado_id);

        -- Ajustar stock en la tabla de inventario por sucursal
        UPDATE inventario
        SET cantidad = cantidad - v_cantidad_vendida
        WHERE producto_id = v_producto_id AND sucursal_id = v_sucursal_id;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """, commit=True)

    # Función para registrar movimientos de inventario por compras (entradas)
    execute_sql_command("""
    CREATE OR REPLACE FUNCTION record_compra_inventario_movement()
    RETURNS TRIGGER AS $$
    DECLARE
        v_empleado_id INT;
        v_proveedor_id INT; -- No se usa directamente en inventario_movimiento, pero es parte de Compra
        v_producto_id INT;
        v_cantidad_comprada INT;
        v_sucursal_destino INT; -- Asumimos una sucursal por defecto para la entrada
    BEGIN
        -- Obtener información de la compra
        SELECT empleado_id INTO v_empleado_id
        FROM compras
        WHERE id = NEW.compra_id;

        v_producto_id := NEW.producto_id;
        v_cantidad_comprada := NEW.cantidad;

        -- **IMPORTANTE: Aquí necesitas una lógica para determinar a qué sucursal entra el inventario.**
        -- Por simplicidad, asumiremos que siempre va a la SUCURSAL_CENTRAL (ID=1).
        -- En un sistema real, la compra tendría un campo para la sucursal de destino o se distribuiría.
        SELECT id INTO v_sucursal_destino FROM sucursales WHERE codigo = 'SUC001' LIMIT 1;
        IF v_sucursal_destino IS NULL THEN
            -- Fallback si no existe SUC001, tomar la primera sucursal
            SELECT id INTO v_sucursal_destino FROM sucursales LIMIT 1;
            IF v_sucursal_destino IS NULL THEN
                RAISE EXCEPTION 'No hay sucursales registradas para registrar la entrada de inventario.';
            END IF;
        END IF;

        -- Registrar movimiento de inventario (entrada)
        INSERT INTO movimientos_inventario (fecha, tipo, cantidad, motivo, producto_id, empleado_id)
        VALUES (NOW(), 'entrada', v_cantidad_comprada, 'Compra (Compra ID: ' || NEW.compra_id || ')', v_producto_id, v_empleado_id);

        -- Ajustar stock en la tabla de inventario por sucursal
        INSERT INTO inventario (producto_id, sucursal_id, cantidad, ubicacion)
        VALUES (v_producto_id, v_sucursal_destino, v_cantidad_comprada, 'AUTOMATICO') -- Ubicación por defecto
        ON CONFLICT (producto_id, sucursal_id) DO UPDATE SET cantidad = inventario.cantidad + EXCLUDED.cantidad;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """, commit=True)

    # Función para manejar el stock total del producto en la tabla de productos (se activa al cambiar inventario)
    execute_sql_command("""
    CREATE OR REPLACE FUNCTION update_producto_total_stock()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE productos
        SET stock = (
            SELECT COALESCE(SUM(cantidad), 0)
            FROM inventario
            WHERE producto_id = NEW.producto_id
        )
        WHERE id = NEW.producto_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """, commit=True)


    print("\n--- Funciones SQL creadas/actualizadas exitosamente. ---")

def create_triggers():
    """Crea triggers en la base de datos."""
    print("\n--- Creando/Actualizando Triggers ---")

    # Trigger para actualizar total de Pedido al insertar/actualizar/eliminar DetallePedido
    execute_sql_command("""
    DROP TRIGGER IF EXISTS trg_update_pedido_total ON detalle_pedidos;
    CREATE TRIGGER trg_update_pedido_total
    AFTER INSERT OR UPDATE OR DELETE ON detalle_pedidos
    FOR EACH ROW
    EXECUTE FUNCTION update_pedido_total();
    """, commit=True)

    # Trigger para actualizar total de Compra al insertar/actualizar/eliminar DetalleCompra
    execute_sql_command("""
    DROP TRIGGER IF EXISTS trg_update_compra_total ON detalle_compras;
    CREATE TRIGGER trg_update_compra_total
    AFTER INSERT OR UPDATE OR DELETE ON detalle_compras
    FOR EACH ROW
    EXECUTE FUNCTION update_compra_total();
    """, commit=True)

    # Trigger para ventas: reducir stock en inventario por sucursal y registrar movimiento
    execute_sql_command("""
    DROP TRIGGER IF EXISTS trg_record_venta_inventario_movement ON detalle_ventas;
    CREATE TRIGGER trg_record_venta_inventario_movement
    AFTER INSERT ON detalle_ventas
    FOR EACH ROW
    EXECUTE FUNCTION record_venta_inventario_movement();
    """, commit=True)

    # Trigger para compras: aumentar stock en inventario por sucursal y registrar movimiento
    execute_sql_command("""
    DROP TRIGGER IF EXISTS trg_record_compra_inventario_movement ON detalle_compras;
    CREATE TRIGGER trg_record_compra_inventario_movement
    AFTER INSERT ON detalle_compras
    FOR EACH ROW
    EXECUTE FUNCTION record_compra_inventario_movement();
    """, commit=True)

    # Trigger para mantener el stock total de producto en la tabla `productos` actualizado
    # cada vez que el `inventario` por sucursal cambia.
    execute_sql_command("""
    DROP TRIGGER IF EXISTS trg_update_producto_total_stock ON inventario;
    CREATE TRIGGER trg_update_producto_total_stock
    AFTER INSERT OR UPDATE OR DELETE ON inventario
    FOR EACH ROW
    EXECUTE FUNCTION update_producto_total_stock();
    """, commit=True)

    print("\n--- Triggers creados/actualizados exitosamente. ---")

def create_views():
    """Crea vistas SQL en la base de datos."""
    print("\n--- Creando/Actualizando Vistas SQL ---")
    
    # Vista para Productos con detalle de Categoría
    execute_sql_command("""
    DROP VIEW IF EXISTS vista_productos_detalle;
    CREATE OR REPLACE VIEW vista_productos_detalle AS
    SELECT
        p.id,
        p.codigo,
        p.nombre AS nombre_producto,
        p.precio,
        p.stock,
        p.stock_minimo,
        c.nombre AS nombre_categoria,
        p.fecha_creacion
    FROM
        productos p
    JOIN
        categorias c ON p.categoria_id = c.id;
    """, commit=True)

    # Vista para Clientes con nombre completo y detalles
    execute_sql_command("""
    DROP VIEW IF EXISTS vista_clientes_resumen;
    CREATE OR REPLACE VIEW vista_clientes_resumen AS
    SELECT
        cl.id,
        cl.codigo,
        cl.nombre || ' ' || cl.apellido AS nombre_completo,
        cl.dni,
        cl.telefono,
        cl.email,
        cl.fecha_registro
    FROM
        clientes cl;
    """, commit=True)

    # Vista para Empleados con puesto y nombre completo
    execute_sql_command("""
    DROP VIEW IF EXISTS vista_empleados_resumen;
    CREATE OR REPLACE VIEW vista_empleados_resumen AS
    SELECT
        e.id,
        e.codigo,
        e.nombre || ' ' || e.apellido AS nombre_completo,
        e.email,
        e.telefono,
        e.salario,
        p.nombre AS nombre_puesto,
        e.fecha_ingreso
    FROM
        empleados e
    JOIN
        puestos p ON e.puesto_id = p.id;
    """, commit=True)

    print("\n--- Vistas SQL creadas/actualizadas exitosamente. ---")

def main_queries():
    print("Iniciando creación de funciones, triggers y vistas SQL...")
    create_sql_functions()
    create_triggers()
    create_views()
    print("\nProceso de queries completado.")

if __name__ == '__main__':
    main_queries()