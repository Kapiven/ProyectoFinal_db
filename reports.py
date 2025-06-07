import csv
from database import Session, engine, Categoria, Producto, Proveedor, Cliente, Pedido, DetallePedido, Servicio, Empleado, Departamento, Puesto, Factura, Pago, Venta, DetalleVenta, Sucursal, Inventario, MovimientoInventario, Compra, DetalleCompra
from sqlalchemy import func, extract, distinct, cast, String
from datetime import datetime, date, timedelta

# --- Configuración y Utilidades ---

def get_session():
    """Retorna una nueva sesión de SQLAlchemy."""
    return Session()

def print_header(title):
    """Imprime un encabezado formateado para los reportes."""
    print("\n" + "="*80)
    print(f"--- {title.upper()} ---")
    print("="*80)

def export_to_csv(filename, header, data):
    """
    Exporta una lista de diccionarios (o tuplas con el mismo orden que el header) a un archivo CSV.
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for row in data:
                # Asegurarse de que cada elemento de la fila sea una cadena para evitar errores de escritura
                writer.writerow([str(item) if item is not None else '' for item in row])
        print(f"\n✅ Reporte exportado exitosamente a '{filename}'")
    except Exception as e:
        print(f"❌ Error al exportar a CSV '{filename}': {e}")

# --- REPORTES CON FILTROS Y EXPORTACIÓN CSV ---

def report_ventas_detalladas(
    start_date=None,
    end_date=None,
    empleado_id=None,
    cliente_id=None,
    sucursal_id=None,
    min_total_venta=None,
    max_total_venta=None,
    export_csv=False
):
    """
    Reporte 1: Ventas Detalladas con múltiples filtros.
    Muestra información de cada venta y los detalles de sus productos.
    """
    session = get_session()
    report_title = "REPORTE DE VENTAS DETALLADAS"
    print_header(report_title)

    try:
        # Construir la consulta base para Ventas y sus Detalles
        query = session.query(
            Venta.id.label('VentaID'),
            Venta.fecha.label('FechaVenta'),
            Venta.total.label('TotalVenta'),
            Sucursal.nombre.label('Sucursal'),
            Empleado.nombre.label('EmpleadoNombre'),
            Empleado.apellido.label('EmpleadoApellido'),
            Producto.nombre.label('Producto'),
            DetalleVenta.cantidad.label('Cantidad'),
            DetalleVenta.precio_unitario.label('PrecioUnitario'),
            DetalleVenta.subtotal.label('SubtotalDetalle')
        ).join(Empleado, Venta.empleado_id == Empleado.id)\
         .join(Sucursal, Venta.sucursal_id == Sucursal.id)\
         .join(DetalleVenta, Venta.id == DetalleVenta.venta_id)\
         .join(Producto, DetalleVenta.producto_id == Producto.id)

        # Aplicar filtros
        if start_date:
            query = query.filter(Venta.fecha >= start_date)
            print(f"Filtro: Fecha de inicio >= {start_date}")
        if end_date:
            query = query.filter(Venta.fecha <= end_date)
            print(f"Filtro: Fecha de fin <= {end_date}")
        if empleado_id:
            query = query.filter(Venta.empleado_id == empleado_id)
            emp = session.query(Empleado).filter_by(id=empleado_id).first()
            if emp: print(f"Filtro: Empleado = {emp.nombre} {emp.apellido}")
        # Aunque Cliente no está directamente en Venta, podríamos filtrar por Cliente a través de Pedidos si la Venta viene de un Pedido.
        # Por simplicidad aquí, si la Venta es directa, no hay Cliente directo. Si necesitas esto, deberías modelar Venta a Cliente.
        # Para este reporte, no hay un `cliente_id` directo en `Venta`. Si la `Venta` es una `VentaDirecta`, el `cliente_id`
        # no aplica. Si la `Venta` proviene de un `Pedido`, el filtro debería ir a `Pedido` y luego `Cliente`.
        # Para cumplir con 5 filtros sin asumir una relación directa Venta-Cliente, usaré `min_total_venta` y `max_total_venta`.
        # Si tu Venta puede tener Cliente, lo añadirías así:
        # if cliente_id:
        #    query = query.join(Pedido, Venta.pedido_id == Pedido.id).filter(Pedido.cliente_id == cliente_id)
        #    cli = session.query(Cliente).filter_by(id=cliente_id).first()
        #    if cli: print(f"Filtro: Cliente = {cli.nombre} {cli.apellido}")

        if sucursal_id:
            query = query.filter(Venta.sucursal_id == sucursal_id)
            suc = session.query(Sucursal).filter_by(id=sucursal_id).first()
            if suc: print(f"Filtro: Sucursal = {suc.nombre}")
        if min_total_venta is not None:
            query = query.filter(Venta.total >= min_total_venta)
            print(f"Filtro: Total de Venta >= {min_total_venta}")
        if max_total_venta is not None:
            query = query.filter(Venta.total <= max_total_venta)
            print(f"Filtro: Total de Venta <= {max_total_venta}")


        results = query.order_by(Venta.fecha.desc()).all()

        if not results:
            print("No se encontraron ventas con los filtros aplicados.")
            return

        # Preparar datos para visualización y exportación
        header = ['Venta ID', 'Fecha Venta', 'Total Venta', 'Sucursal', 'Empleado', 'Producto', 'Cantidad', 'Precio Unitario', 'Subtotal Detalle']
        data = []
        for row in results:
            data.append((
                row.VentaID,
                row.FechaVenta.strftime('%Y-%m-%d %H:%M:%S'),
                f"{row.TotalVenta:,.2f}",
                row.Sucursal,
                f"{row.EmpleadoNombre} {row.EmpleadoApellido}",
                row.Producto,
                row.Cantidad,
                f"{row.PrecioUnitario:,.2f}",
                f"{row.SubtotalDetalle:,.2f}"
            ))

        # Visualización
        print("-" * 120)
        print(f"{'Venta ID':<10} {'Fecha':<19} {'Total Venta':<15} {'Sucursal':<20} {'Empleado':<20} {'Producto':<25} {'Cant':<7} {'Precio Unit.':<15} {'Subtotal':<15}")
        print("-" * 180) # Ajustado para la cantidad de columnas
        for row in data:
            print(f"{row[0]:<10} {row[1]:<19} {row[2]:<15} {row[3]:<20} {row[4]:<20} {row[5]:<25} {row[6]:<7} {row[7]:<15} {row[8]:<15}")
        print("-" * 180)


        # Exportación a CSV
        if export_csv:
            csv_filename = f"reporte_ventas_detalladas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            export_to_csv(csv_filename, header, data)

    except Exception as e:
        print(f"❌ Error al generar el reporte de ventas detalladas: {e}")
    finally:
        session.close()


def report_inventario_general(
    categoria_id=None,
    min_stock=None,
    max_stock=None,
    min_stock_minimo=None, # Nuevo filtro: stock mínimo
    max_stock_minimo=None, # Nuevo filtro: stock máximo
    en_sucursal_id=None, # Nuevo filtro: inventario en una sucursal específica
    export_csv=False
):
    """
    Reporte 2: Inventario General con múltiples filtros.
    Muestra el estado actual del inventario por producto y sucursal.
    """
    session = get_session()
    report_title = "REPORTE DE INVENTARIO GENERAL"
    print_header(report_title)

    try:
        query = session.query(
            Producto.codigo.label('CodigoProducto'),
            Producto.nombre.label('NombreProducto'),
            Categoria.nombre.label('Categoria'),
            Inventario.cantidad.label('CantidadInventario'),
            Producto.stock.label('StockTotalProducto'),
            Producto.stock_minimo.label('StockMinimoProducto'),
            Sucursal.nombre.label('Sucursal'),
            Inventario.ubicacion.label('Ubicacion')
        ).join(Categoria, Producto.categoria_id == Categoria.id)\
         .outerjoin(Inventario, Producto.id == Inventario.producto_id)\
         .outerjoin(Sucursal, Inventario.sucursal_id == Sucursal.id)
        
        # Aplicar filtros
        if categoria_id:
            query = query.filter(Producto.categoria_id == categoria_id)
            cat = session.query(Categoria).filter_by(id=categoria_id).first()
            if cat: print(f"Filtro: Categoría = {cat.nombre}")
        if min_stock is not None:
            query = query.filter(Producto.stock >= min_stock)
            print(f"Filtro: Stock Total >= {min_stock}")
        if max_stock is not None:
            query = query.filter(Producto.stock <= max_stock)
            print(f"Filtro: Stock Total <= {max_stock}")
        if min_stock_minimo is not None:
            query = query.filter(Producto.stock_minimo >= min_stock_minimo)
            print(f"Filtro: Stock Mínimo Producto >= {min_stock_minimo}")
        if max_stock_minimo is not None:
            query = query.filter(Producto.stock_minimo <= max_stock_minimo)
            print(f"Filtro: Stock Mínimo Producto <= {max_stock_minimo}")
        if en_sucursal_id:
            query = query.filter(Inventario.sucursal_id == en_sucursal_id)
            suc = session.query(Sucursal).filter_by(id=en_sucursal_id).first()
            if suc: print(f"Filtro: En Sucursal = {suc.nombre}")

        results = query.order_by(Producto.nombre, Sucursal.nombre).all()

        if not results:
            print("No se encontraron productos en inventario con los filtros aplicados.")
            return

        # Preparar datos para visualización y exportación
        header = ['Código Producto', 'Nombre Producto', 'Categoría', 'Cantidad en Inventario', 'Stock Total Producto', 'Stock Mínimo', 'Sucursal', 'Ubicación']
        data = []
        for row in results:
            data.append((
                row.CodigoProducto,
                row.NombreProducto,
                row.Categoria,
                row.CantidadInventario if row.CantidadInventario is not None else 0,
                row.StockTotalProducto,
                row.StockMinimoProducto,
                row.Sucursal if row.Sucursal is not None else 'N/A', # Si un producto no está en inventario en ninguna sucursal
                row.Ubicacion if row.Ubicacion is not None else 'N/A'
            ))

        # Visualización
        print("-" * 120)
        print(f"{'Cod. Prod':<12} {'Producto':<35} {'Categoría':<20} {'Cant. Inv.':<12} {'Stock Total':<12} {'Stock Mín.':<12} {'Sucursal':<20} {'Ubicación':<15}")
        print("-" * 180)
        for row in data:
            print(f"{row[0]:<12} {row[1]:<35} {row[2]:<20} {row[3]:<12} {row[4]:<12} {row[5]:<12} {row[6]:<20} {row[7]:<15}")
        print("-" * 180)

        # Exportación a CSV
        if export_csv:
            csv_filename = f"reporte_inventario_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            export_to_csv(csv_filename, header, data)

    except Exception as e:
        print(f"❌ Error al generar el reporte de inventario general: {e}")
    finally:
        session.close()


def report_pedidos_por_cliente(
    cliente_id=None,
    empleado_id=None,
    estado_pedido=None,
    min_total_pedido=None,
    max_total_pedido=None,
    start_date=None,
    end_date=None,
    export_csv=False
):
    """
    Reporte 3: Pedidos por Cliente con múltiples filtros.
    Muestra un resumen de los pedidos realizados, filtrando por cliente, empleado, estado y rango de fechas/montos.
    """
    session = get_session()
    report_title = "REPORTE DE PEDIDOS POR CLIENTE"
    print_header(report_title)

    try:
        query = session.query(
            Pedido.numero.label('NumeroPedido'),
            Pedido.fecha.label('FechaPedido'),
            Pedido.total.label('TotalPedido'),
            Pedido.estado.label('EstadoPedido'),
            Cliente.nombre.label('NombreCliente'),
            Cliente.apellido.label('ApellidoCliente'),
            Cliente.email.label('EmailCliente'),
            Empleado.nombre.label('NombreEmpleado'),
            Empleado.apellido.label('ApellidoEmpleado')
        ).join(Cliente, Pedido.cliente_id == Cliente.id)\
         .join(Empleado, Pedido.empleado_id == Empleado.id)

        # Aplicar filtros
        if cliente_id:
            query = query.filter(Pedido.cliente_id == cliente_id)
            cli = session.query(Cliente).filter_by(id=cliente_id).first()
            if cli: print(f"Filtro: Cliente = {cli.nombre} {cli.apellido}")
        if empleado_id:
            query = query.filter(Pedido.empleado_id == empleado_id)
            emp = session.query(Empleado).filter_by(id=empleado_id).first()
            if emp: print(f"Filtro: Empleado = {emp.nombre} {emp.apellido}")
        if estado_pedido:
            query = query.filter(Pedido.estado == estado_pedido)
            print(f"Filtro: Estado = {estado_pedido}")
        if min_total_pedido is not None:
            query = query.filter(Pedido.total >= min_total_pedido)
            print(f"Filtro: Total de Pedido >= {min_total_pedido}")
        if max_total_pedido is not None:
            query = query.filter(Pedido.total <= max_total_pedido)
            print(f"Filtro: Total de Pedido <= {max_total_pedido}")
        if start_date:
            query = query.filter(Pedido.fecha >= start_date)
            print(f"Filtro: Fecha de inicio >= {start_date}")
        if end_date:
            query = query.filter(Pedido.fecha <= end_date)
            print(f"Filtro: Fecha de fin <= {end_date}")


        results = query.order_by(Pedido.fecha.desc()).all()

        if not results:
            print("No se encontraron pedidos con los filtros aplicados.")
            return

        # Preparar datos para visualización y exportación
        header = ['Número Pedido', 'Fecha Pedido', 'Total Pedido', 'Estado', 'Cliente', 'Email Cliente', 'Empleado Responsable']
        data = []
        for row in results:
            data.append((
                row.NumeroPedido,
                row.FechaPedido.strftime('%Y-%m-%d %H:%M:%S'),
                f"{row.TotalPedido:,.2f}",
                row.EstadoPedido,
                f"{row.NombreCliente} {row.ApellidoCliente}",
                row.EmailCliente,
                f"{row.NombreEmpleado} {row.ApellidoEmpleado}"
            ))

        # Visualización
        print("-" * 120)
        print(f"{'No. Pedido':<15} {'Fecha':<19} {'Total':<15} {'Estado':<12} {'Cliente':<30} {'Email Cliente':<30} {'Empleado':<25}")
        print("-" * 180)
        for row in data:
            print(f"{row[0]:<15} {row[1]:<19} {row[2]:<15} {row[3]:<12} {row[4]:<30} {row[5]:<30} {row[6]:<25}")
        print("-" * 180)

        # Exportación a CSV
        if export_csv:
            csv_filename = f"reporte_pedidos_cliente_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            export_to_csv(csv_filename, header, data)

    except Exception as e:
        print(f"❌ Error al generar el reporte de pedidos por cliente: {e}")
    finally:
        session.close()


# --- Función Principal para Ejecutar Reportes ---

def main_menu():
    """Menú principal para seleccionar y ejecutar reportes."""
    while True:
        print("\n" + "="*80)
        print("                 MENÚ DE REPORTES")
        print("="*80)
        print("1. Reporte de Ventas Detalladas")
        print("2. Reporte de Inventario General")
        print("3. Reporte de Pedidos por Cliente")
        print("0. Salir")
        print("="*80)

        choice = input("Seleccione una opción: ")

        if choice == '1':
            print("\n--- Configuración Reporte de Ventas Detalladas ---")
            start_date_str = input("Fecha de inicio (YYYY-MM-DD, dejar vacío para omitir): ")
            end_date_str = input("Fecha de fin (YYYY-MM-DD, dejar vacío para omitir): ")
            empleado_id_str = input("ID de Empleado (dejar vacío para omitir): ")
            sucursal_id_str = input("ID de Sucursal (dejar vacío para omitir): ")
            min_total_venta_str = input("Monto mínimo de venta (dejar vacío para omitir): ")
            max_total_venta_str = input("Monto máximo de venta (dejar vacío para omitir): ")
            export = input("¿Exportar a CSV? (s/n): ").lower() == 's'

            # Convertir inputs
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
            empleado_id = int(empleado_id_str) if empleado_id_str.isdigit() else None
            sucursal_id = int(sucursal_id_str) if sucursal_id_str.isdigit() else None
            min_total_venta = float(min_total_venta_str) if min_total_venta_str else None
            max_total_venta = float(max_total_venta_str) if max_total_venta_str else None
            
            report_ventas_detalladas(
                start_date=start_date,
                end_date=end_date,
                empleado_id=empleado_id,
                sucursal_id=sucursal_id,
                min_total_venta=min_total_venta,
                max_total_venta=max_total_venta,
                export_csv=export
            )
        elif choice == '2':
            print("\n--- Configuración Reporte de Inventario General ---")
            categoria_id_str = input("ID de Categoría (dejar vacío para omitir): ")
            min_stock_str = input("Stock mínimo de producto (dejar vacío para omitir): ")
            max_stock_str = input("Stock máximo de producto (dejar vacío para omitir): ")
            min_stock_minimo_str = input("Stock mínimo (umbral) de producto (dejar vacío para omitir): ")
            max_stock_minimo_str = input("Stock máximo (umbral) de producto (dejar vacío para omitir): ")
            en_sucursal_id_str = input("ID de Sucursal (para ver inventario en esa sucursal, dejar vacío para omitir): ")
            export = input("¿Exportar a CSV? (s/n): ").lower() == 's'

            # Convertir inputs
            categoria_id = int(categoria_id_str) if categoria_id_str.isdigit() else None
            min_stock = int(min_stock_str) if min_stock_str.isdigit() else None
            max_stock = int(max_stock_str) if max_stock_str.isdigit() else None
            min_stock_minimo = int(min_stock_minimo_str) if min_stock_minimo_str.isdigit() else None
            max_stock_minimo = int(max_stock_minimo_str) if max_stock_minimo_str.isdigit() else None
            en_sucursal_id = int(en_sucursal_id_str) if en_sucursal_id_str.isdigit() else None

            report_inventario_general(
                categoria_id=categoria_id,
                min_stock=min_stock,
                max_stock=max_stock,
                min_stock_minimo=min_stock_minimo,
                max_stock_minimo=max_stock_minimo,
                en_sucursal_id=en_sucursal_id,
                export_csv=export
            )
        elif choice == '3':
            print("\n--- Configuración Reporte de Pedidos por Cliente ---")
            cliente_id_str = input("ID de Cliente (dejar vacío para omitir): ")
            empleado_id_str = input("ID de Empleado que gestionó el pedido (dejar vacío para omitir): ")
            estado_pedido_str = input("Estado del pedido (ej. 'completado', 'pendiente', 'procesando', dejar vacío para omitir): ")
            min_total_pedido_str = input("Monto mínimo del pedido (dejar vacío para omitir): ")
            max_total_pedido_str = input("Monto máximo del pedido (dejar vacío para omitir): ")
            start_date_str = input("Fecha de inicio del pedido (YYYY-MM-DD, dejar vacío para omitir): ")
            end_date_str = input("Fecha de fin del pedido (YYYY-MM-DD, dejar vacío para omitir): ")
            export = input("¿Exportar a CSV? (s/n): ").lower() == 's'

            # Convertir inputs
            cliente_id = int(cliente_id_str) if cliente_id_str.isdigit() else None
            empleado_id = int(empleado_id_str) if empleado_id_str.isdigit() else None
            estado_pedido = estado_pedido_str if estado_pedido_str else None
            min_total_pedido = float(min_total_pedido_str) if min_total_pedido_str else None
            max_total_pedido = float(max_total_pedido_str) if max_total_pedido_str else None
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

            report_pedidos_por_cliente(
                cliente_id=cliente_id,
                empleado_id=empleado_id,
                estado_pedido=estado_pedido,
                min_total_pedido=min_total_pedido,
                max_total_pedido=max_total_pedido,
                start_date=start_date,
                end_date=end_date,
                export_csv=export
            )
        elif choice == '0':
            print("Saliendo del programa de reportes. ¡Hasta luego!")
            break
        else:
            print("Opción no válida. Por favor, intente de nuevo.")

if __name__ == '__main__':
    print("Asegúrese de haber ejecutado 'database.py', 'queries.py' e 'inserts.py' para tener la base de datos y los datos listos.")
    main_menu()