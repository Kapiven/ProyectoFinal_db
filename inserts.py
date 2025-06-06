from faker import Faker
from database import *
import random
from datetime import datetime, timedelta

# Configurar Faker en español
fake = Faker('es_ES')

def generar_datos_prueba():
    """Genera más de 1000 registros de prueba distribuidos entre todas las tablas"""
    session = obtener_session()
    
    try:
        print("🔄 Generando datos de prueba...")
        
        # 1. CATEGORÍAS (20 registros)
        print("📁 Creando categorías...")
        categorias = []
        nombres_categorias = [
            'Electrónicos', 'Ropa', 'Hogar', 'Deportes', 'Libros',
            'Juguetes', 'Automóviles', 'Jardinería', 'Cocina', 'Belleza',
            'Música', 'Películas', 'Salud', 'Mascotas', 'Oficina',
            'Construcción', 'Arte', 'Viajes', 'Alimentación', 'Tecnología'
        ]
        
        for i, nombre in enumerate(nombres_categorias, 1):
            categoria = Categoria(
                nombre=nombre,
                descripcion=fake.text(max_nb_chars=200),
                activa=random.choice([True, False])
            )
            categorias.append(categoria)
            session.add(categoria)
        
        session.commit()
        print(f"✅ {len(categorias)} categorías creadas")
        
        # 2. PUESTOS DE TRABAJO (15 registros)
        print("💼 Creando puestos...")
        puestos = []
        nombres_puestos = [
            'Gerente General', 'Vendedor', 'Cajero', 'Almacenero', 'Contador',
            'Desarrollador', 'Diseñador', 'Marketing', 'Recursos Humanos', 'Seguridad',
            'Limpieza', 'Mantenimiento', 'Recepcionista', 'Supervisor', 'Analista'
        ]
        
        for nombre in nombres_puestos:
            salario_min = random.randint(800, 2000)
            puesto = Puesto(
                nombre=nombre,
                descripcion=fake.text(max_nb_chars=150),
                salario_minimo=salario_min,
                salario_maximo=salario_min + random.randint(500, 1500),
                activo=True
            )
            puestos.append(puesto)
            session.add(puesto)
        
        session.commit()
        print(f"✅ {len(puestos)} puestos creados")
        
        # 3. DEPARTAMENTOS (10 registros)
        print("🏢 Creando departamentos...")
        departamentos = []
        nombres_departamentos = [
            'Ventas', 'Administración', 'Recursos Humanos', 'Contabilidad', 'Marketing',
            'Sistemas', 'Logística', 'Compras', 'Atención al Cliente', 'Gerencia'
        ]
        
        for i, nombre in enumerate(nombres_departamentos, 1):
            departamento = Departamento(
                codigo=f"DEPT{i:03d}",
                nombre=nombre,
                descripcion=fake.text(max_nb_chars=100),
                presupuesto=random.randint(10000, 50000),
                activo=True
            )
            departamentos.append(departamento)
            session.add(departamento)
        
        session.commit()
        print(f"✅ {len(departamentos)} departamentos creados")
        
        # 4. EMPLEADOS (50 registros)
        print("👥 Creando empleados...")
        empleados = []
        for i in range(50):
            dni = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            empleado = Empleado(
                codigo=f"EMP{i+1:03d}",
                nombre=fake.first_name(),
                apellido=fake.last_name(),
                dni=dni,
                telefono=f"+502 {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}",
                email=fake.email(),
                salario=random.randint(1000, 5000),
                fecha_ingreso=fake.date_between(start_date='-2y', end_date='today'),
                activo=random.choice([True, False]),
                puesto_id=random.choice(puestos).id
            )
            empleados.append(empleado)
            session.add(empleado)
        
        session.commit()
        print(f"✅ {len(empleados)} empleados creados")
        
        # 5. SUCURSALES (8 registros)
        print("🏪 Creando sucursales...")
        sucursales = []
        ciudades = ['Guatemala', 'Quetzaltenango', 'Escuintla', 'Mazatenango', 'Cobán', 'Huehuetenango', 'Zacapa', 'Retalhuleu']
        
        for i, ciudad in enumerate(ciudades, 1):
            sucursal = Sucursal(
                codigo=f"SUC{i:03d}",
                nombre=f"Sucursal {ciudad}",
                direccion=fake.address(),
                telefono=f"+502 {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}",
                email=f"sucursal{ciudad.lower()}@empresa.com",
                activa=True
            )
            sucursales.append(sucursal)
            session.add(sucursal)
        
        session.commit()
        print(f"✅ {len(sucursales)} sucursales creadas")
        
        # 6. PROVEEDORES (30 registros)
        print("🚚 Creando proveedores...")
        proveedores = []
        for i in range(30):
            proveedor = Proveedor(
                codigo=f"PROV{i+1:03d}",
                nombre=fake.company(),
                contacto=fake.name(),
                telefono=f"+502 {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}",
                email=fake.company_email(),
                direccion={
                    "calle": fake.street_address(),
                    "ciudad": fake.city(),
                    "codigo_postal": fake.postcode()
                },
                fecha_registro=fake.date_between(start_date='-1y', end_date='today'),
                activo=True
            )
            proveedores.append(proveedor)
            session.add(proveedor)
        
        session.commit()
        print(f"✅ {len(proveedores)} proveedores creados")
        
        # 7. PRODUCTOS (200 registros)
        print("📦 Creando productos...")
        productos = []
        for i in range(200):
            precio = round(random.uniform(10.0, 500.0), 2)
            producto = Producto(
                codigo=f"PROD{i+1:06d}",
                nombre=fake.catch_phrase(),
                descripcion=fake.text(max_nb_chars=300),
                precio=precio,
                stock=random.randint(0, 100),
                stock_minimo=random.randint(5, 15),
                categoria_id=random.choice(categorias).id,
                fecha_creacion=fake.date_time_between(start_date='-6M', end_date='now'),
                activo=random.choice([True, False])
            )
            productos.append(producto)
            session.add(producto)
        
        session.commit()
        print(f"✅ {len(productos)} productos creados")
        
        # 8. SERVICIOS (25 registros)
        print("🔧 Creando servicios...")
        servicios = []
        tipos_servicios = [
            'Instalación', 'Mantenimiento', 'Reparación', 'Consultoría', 'Capacitación',
            'Soporte Técnico', 'Garantía Extendida', 'Configuración', 'Actualización', 'Limpieza'
        ]
        
        for i in range(25):
            costo = round(random.uniform(50.0, 300.0), 2)
            servicio = Servicio(
                codigo=f"SERV{i+1:03d}",
                nombre=f"{random.choice(tipos_servicios)} {fake.word().title()}",
                descripcion=fake.text(max_nb_chars=200),
                costo=f"${costo}",
                duracion=random.randint(1, 8),
                activo=True
            )
            servicios.append(servicio)
            session.add(servicio)
        
        session.commit()
        print(f"✅ {len(servicios)} servicios creados")
        
        # 9. CLIENTES (100 registros)
        print("👤 Creando clientes...")
        clientes = []
        for i in range(100):
            dni = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            cliente = Cliente(
                codigo=f"CLI{i+1:06d}",
                nombre=fake.first_name(),
                apellido=fake.last_name(),
                dni=dni,
                telefono=f"+502 {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}",
                email=fake.email(),
                direccion={
                    "calle": fake.street_address(),
                    "ciudad": fake.city(),
                    "departamento": fake.state(),
                    "codigo_postal": fake.postcode()
                },
                fecha_nacimiento=fake.date_of_birth(minimum_age=18, maximum_age=80),
                fecha_registro=fake.date_between(start_date='-2y', end_date='today'),
                activo=True
            )
            clientes.append(cliente)
            session.add(cliente)
        
        session.commit()
        print(f"✅ {len(clientes)} clientes creados")
        
        # 10. PEDIDOS (150 registros)
        print("📋 Creando pedidos...")
        pedidos = []
        estados_pedido = ['pendiente', 'procesando', 'completado', 'cancelado']
        
        for i in range(150):
            total = round(random.uniform(50.0, 1000.0), 2)
            pedido = Pedido(
                numero=f"PED{i+1:06d}",
                fecha=fake.date_time_between(start_date='-3M', end_date='now'),
                estado=random.choice(estados_pedido),
                total=total,
                observaciones=fake.text(max_nb_chars=100) if random.choice([True, False]) else None,
                cliente_id=random.choice(clientes).id,
                empleado_id=random.choice(empleados).id
            )
            pedidos.append(pedido)
            session.add(pedido)
        
        session.commit()
        print(f"✅ {len(pedidos)} pedidos creados")
        
        # 11. DETALLES DE PEDIDO (400 registros)
        print("📝 Creando detalles de pedidos...")
        for i in range(400):
            pedido = random.choice(pedidos)
            producto = random.choice(productos)
            cantidad = random.randint(1, 5)
            precio_unitario = float(producto.precio)
            subtotal = cantidad * precio_unitario
            
            detalle = DetallePedido(
                pedido_id=pedido.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal,
                descuento=random.randint(0, 20)
            )
            session.add(detalle)
        
        session.commit()
        print("✅ 400 detalles de pedidos creados")
        
        # 12. FACTURAS (120 registros)
        print("🧾 Creando facturas...")
        facturas = []
        estados_factura = ['pendiente', 'pagada', 'vencida', 'anulada']
        
        for i in range(120):
            subtotal = round(random.uniform(100.0, 2000.0), 2)
            impuesto = round(subtotal * 0.12, 2)  # 12% IVA Guatemala
            total = subtotal + impuesto
            
            factura = Factura(
                numero=f"FAC{i+1:06d}",
                fecha=fake.date_time_between(start_date='-2M', end_date='now'),
                subtotal=subtotal,
                impuesto=impuesto,
                total=total,
                estado=random.choice(estados_factura),
                cliente_id=random.choice(clientes).id
            )
            facturas.append(factura)
            session.add(factura)
        
        session.commit()
        print(f"✅ {len(facturas)} facturas creadas")
        
        # 13. PAGOS (80 registros)
        print("💰 Creando pagos...")
        metodos_pago = ['efectivo', 'tarjeta', 'transferencia', 'cheque']
        
        for i in range(80):
            factura = random.choice(facturas)
            pago = Pago(
                numero=f"PAG{i+1:06d}",
                fecha=fake.date_time_between(start_date=factura.fecha, end_date='now'),
                monto=round(random.uniform(50.0, float(factura.total)), 2),
                metodo=random.choice(metodos_pago),
                referencia=fake.bothify(text='REF-####-????'),
                factura_id=factura.id
            )
            session.add(pago)
        
        session.commit()
        print("✅ 80 pagos creados")
        
        # 14. VENTAS (100 registros)
        print("💼 Creando ventas...")
        ventas = []
        for i in range(100):
            venta = Venta(
                fecha=fake.date_time_between(start_date='-2M', end_date='now'),
                total=round(random.uniform(50.0, 800.0), 2),
                empleado_id=random.choice(empleados).id,
                sucursal_id=random.choice(sucursales).id
            )
            ventas.append(venta)
            session.add(venta)
        
        session.commit()
        print(f"✅ {len(ventas)} ventas creadas")
        
        # 15. DETALLES DE VENTA (250 registros)
        print("📊 Creando detalles de ventas...")
        for i in range(250):
            venta = random.choice(ventas)
            producto = random.choice(productos)
            cantidad = random.randint(1, 3)
            precio_unitario = float(producto.precio)
            subtotal = cantidad * precio_unitario
            
            detalle_venta = DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            session.add(detalle_venta)
        
        session.commit()
        print("✅ 250 detalles de ventas creados")
        
        # 16. COMPRAS (60 registros)
        print("🛒 Creando compras...")
        compras = []
        estados_compra = ['pendiente', 'recibida', 'cancelada']
        
        for i in range(60):
            compra = Compra(
                numero=f"COM{i+1:06d}",
                fecha=fake.date_time_between(start_date='-4M', end_date='now'),
                total=round(random.uniform(200.0, 5000.0), 2),
                estado=random.choice(estados_compra),
                proveedor_id=random.choice(proveedores).id,
                empleado_id=random.choice(empleados).id
            )
            compras.append(compra)
            session.add(compra)
        
        session.commit()
        print(f"✅ {len(compras)} compras creadas")
        
        # 17. DETALLES DE COMPRA (180 registros)
        print("📦 Creando detalles de compras...")
        for i in range(180):
            compra = random.choice(compras)
            producto = random.choice(productos)
            cantidad = random.randint(10, 50)
            precio_unitario = round(float(producto.precio) * 0.7, 2)  # Precio de compra menor
            subtotal = cantidad * precio_unitario
            
            detalle_compra = DetalleCompra(
                compra_id=compra.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            session.add(detalle_compra)
        
        session.commit()
        print("✅ 180 detalles de compras creados")
        
        # 18. INVENTARIO (160 registros)
        print("📋 Creando inventario...")
        inventarios_creados = set()  # Para evitar duplicados
        
        for i in range(160):
            producto = random.choice(productos)
            sucursal = random.choice(sucursales)
            
            # Evitar duplicar producto-sucursal
            clave = (producto.id, sucursal.id)
            if clave in inventarios_creados:
                continue
                
            inventario = Inventario(
                producto_id=producto.id,
                sucursal_id=sucursal.id,
                cantidad=random.randint(0, 50),
                ubicacion=f"Pasillo {random.randint(1, 10)}-Estante {random.randint(1, 5)}",
                fecha_actualizacion=fake.date_time_between(start_date='-1M', end_date='now')
            )
            session.add(inventario)
            inventarios_creados.add(clave)
        
        session.commit()
        print(f"✅ {len(inventarios_creados)} registros de inventario creados")
        
        # 19. MOVIMIENTOS DE INVENTARIO (200 registros)
        print("🔄 Creando movimientos de inventario...")
        tipos_movimiento = ['entrada', 'salida', 'ajuste']
        motivos = ['Venta', 'Compra', 'Devolución', 'Ajuste de inventario', 'Producto dañado', 'Traslado']
        
        for i in range(200):
            movimiento = MovimientoInventario(
                fecha=fake.date_time_between(start_date='-2M', end_date='now'),
                tipo=random.choice(tipos_movimiento),
                cantidad=random.randint(1, 20),
                motivo=random.choice(motivos),
                producto_id=random.choice(productos).id,
                empleado_id=random.choice(empleados).id
            )
            session.add(movimiento)
        
        session.commit()
        print("✅ 200 movimientos de inventario creados")
        
        # 20. RELACIONES N:M
        print("🔗 Creando relaciones N:M...")
        
        # Producto-Proveedor (150 relaciones)
        for i in range(150):
            producto = random.choice(productos)
            proveedor = random.choice(proveedores)
            
            # Verificar si ya existe la relación
            if proveedor not in producto.proveedores:
                producto.proveedores.append(proveedor)
        
        # Cliente-Servicio (100 relaciones)
        for i in range(100):
            cliente = random.choice(clientes)
            servicio = random.choice(servicios)
            
            if servicio not in cliente.servicios:
                cliente.servicios.append(servicio)
        
        # Empleado-Departamento (80 relaciones)
        for i in range(80):
            empleado = random.choice(empleados)
            departamento = random.choice(departamentos)
            
            if departamento not in empleado.departamentos:
                empleado.departamentos.append(departamento)
        
        session.commit()
        print("✅ Relaciones N:M creadas")
        
        # RESUMEN FINAL
        total_registros = (
            len(categorias) + len(puestos) + len(departamentos) + len(empleados) +
            len(sucursales) + len(proveedores) + len(productos) + len(servicios) +
            len(clientes) + len(pedidos) + 400 + len(facturas) + 80 + len(ventas) +
            250 + len(compras) + 180 + len(inventarios_creados) + 200 + 330  # 330 relaciones N:M
        )
        
        print(f"\n🎉 DATOS GENERADOS EXITOSAMENTE!")
        print(f"📊 Total de registros creados: {total_registros}")
        print(f"✅ Objetivo cumplido: {total_registros >= 1000}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error al generar datos: {e}")
        return False
    
    finally:
        session.close()

def limpiar_datos():
    """Elimina todos los datos de prueba (CUIDADO: Borra todo)"""
    session = obtener_session()
    
    try:
        print("🧹 Limpiando datos existentes...")
        
        # Eliminar en orden inverso para respetar las claves foráneas
        tablas_orden = [
            MovimientoInventario, DetalleCompra, Compra, DetalleVenta, Venta,
            Pago, Factura, DetallePedido, Pedido, Inventario, Servicio,
            Cliente, Producto, Proveedor, Sucursal, Empleado, Puesto,
            Departamento, Categoria
        ]
        
        for tabla in tablas_orden:
            session.query(tabla).delete()
            session.commit()
            print(f"✅ Tabla {tabla.__tablename__} limpiada")
        
        print("🎉 Limpieza completada")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error al limpiar datos: {e}")
        return False
    
    finally:
        session.close()

if __name__ == '__main__':
    print("🚀 Iniciando generación de datos de prueba...")
    
    # Opción para limpiar datos existentes
    respuesta = input("¿Deseas limpiar los datos existentes? (s/n): ")
    if respuesta.lower() == 's':
        limpiar_datos()
    
    # Generar nuevos datos
    if generar_datos_prueba():
        print("✅ Proceso completado exitosamente!")
    else:
        print("❌ Error en el proceso de generación")