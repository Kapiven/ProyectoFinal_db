from database import Session, engine
from database import (
   
    Categoria, Producto, Proveedor, Cliente, Pedido, DetallePedido, Servicio,
    Empleado, Departamento, Puesto, Factura, Pago, Venta, DetalleVenta, Sucursal,
    Inventario, MovimientoInventario,
    
    VistaProductoDetalle, VistaClienteResumen, VistaEmpleadoResumen
)
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# --- Funciones de Utilidad ---

def get_session():
    """Retorna una nueva sesión de SQLAlchemy."""
    return Session()

def clear_screen():
    """Limpia la consola."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def press_any_key_to_continue():
    """Pausa la ejecución hasta que el usuario presione una tecla."""
    input("\nPresiona Enter para continuar...")

def print_header(title):
    """Imprime un encabezado formateado."""
    clear_screen()
    print("\n" + "="*80)
    print(f"--- {title.upper()} ---")
    print("="*80)

# --- CRUD para PRODUCTOS ---

def crud_productos():
    while True:
        print_header("GESTIÓN DE PRODUCTOS")
        print("1. Ver todos los Productos (desde VIEW)")
        print("2. Crear nuevo Producto")
        print("3. Actualizar Producto existente")
        print("4. Eliminar Producto")
        print("0. Volver al menú principal")
        print("="*80)

        choice = input("Seleccione una opción: ")
        session = get_session()

        try:
            if choice == '1':
                print_header("LISTADO DE PRODUCTOS")
                productos_detalle = session.query(VistaProductoDetalle).all()
                if not productos_detalle:
                    print("No hay productos registrados.")
                else:
                    print(f"{'ID':<5} {'Código':<10} {'Nombre Producto':<35} {'Categoría':<20} {'Precio':<10} {'Stock':<6} {'Min.':<5}")
                    print("-" * 120)
                    for p in productos_detalle:
                        print(f"{p.id:<5} {p.codigo:<10} {p.nombre_producto:<35} {p.nombre_categoria:<20} {p.precio:,.2f} {p.stock:<6} {p.stock_minimo:<5}")
                    print("-" * 120)
                press_any_key_to_continue()

            elif choice == '2':
                print_header("CREAR NUEVO PRODUCTO")
                codigo = input("Código del producto: ").strip()
                nombre = input("Nombre del producto: ").strip()
                descripcion = input("Descripción: ").strip()
                try:
                    precio = float(input("Precio: "))
                    stock = int(input("Stock inicial: "))
                    stock_minimo = int(input("Stock mínimo: "))
                except ValueError:
                    print("Entrada inválida para precio, stock o stock mínimo.")
                    press_any_key_to_continue()
                    continue

                # Seleccionar Categoría
                categorias = session.query(Categoria).all()
                if not categorias:
                    print("No hay categorías. Crea una antes de añadir productos.")
                    press_any_key_to_continue()
                    continue
                print("\nCategorías disponibles:")
                for cat in categorias:
                    print(f"{cat.id}. {cat.nombre}")
                
                try:
                    categoria_id = int(input("ID de Categoría: "))
                    categoria_obj = session.query(Categoria).filter_by(id=categoria_id).first()
                    if not categoria_obj:
                        print("Categoría no encontrada.")
                        press_any_key_to_continue()
                        continue
                except ValueError:
                    print("ID de Categoría inválido.")
                    press_any_key_to_continue()
                    continue

                nuevo_producto = Producto(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=precio,
                    stock=stock,
                    stock_minimo=stock_minimo,
                    categoria=categoria_obj,
                    fecha_creacion=datetime.now()
                )
                session.add(nuevo_producto)
                session.commit()
                print(f"Producto '{nuevo_producto.nombre}' creado exitosamente.")
                press_any_key_to_continue()

            elif choice == '3':
                print_header("ACTUALIZAR PRODUCTO")
                producto_id_str = input("ID del producto a actualizar: ").strip()
                if not producto_id_str.isdigit():
                    print("ID inválido.")
                    press_any_key_to_continue()
                    continue
                producto_id = int(producto_id_str)
                
                producto_a_actualizar = session.query(Producto).filter_by(id=producto_id).first()
                if not producto_a_actualizar:
                    print("Producto no encontrado.")
                    press_any_key_to_continue()
                    continue
                
                print(f"Editando Producto: {producto_a_actualizar.nombre} (Código: {producto_a_actualizar.codigo})")
                producto_a_actualizar.nombre = input(f"Nuevo nombre ({producto_a_actualizar.nombre}): ").strip() or producto_a_actualizar.nombre
                producto_a_actualizar.descripcion = input(f"Nueva descripción ({producto_a_actualizar.descripcion}): ").strip() or producto_a_actualizar.descripcion
                
                precio_str = input(f"Nuevo precio ({producto_a_actualizar.precio}): ").strip()
                if precio_str:
                    try:
                        producto_a_actualizar.precio = float(precio_str)
                    except ValueError:
                        print("Precio inválido. Se mantendrá el anterior.")

                stock_str = input(f"Nuevo stock ({producto_a_actualizar.stock}): ").strip()
                if stock_str:
                    try:
                        producto_a_actualizar.stock = int(stock_str)
                    except ValueError:
                        print("Stock inválido. Se mantendrá el anterior.")
                
                stock_minimo_str = input(f"Nuevo stock mínimo ({producto_a_actualizar.stock_minimo}): ").strip()
                if stock_minimo_str:
                    try:
                        producto_a_actualizar.stock_minimo = int(stock_minimo_str)
                    except ValueError:
                        print("Stock mínimo inválido. Se mantendrá el anterior.")
                
                # Opcional: Actualizar Categoría
                update_cat = input("¿Desea actualizar la categoría? (s/n): ").lower()
                if update_cat == 's':
                    categorias = session.query(Categoria).all()
                    if categorias:
                        print("\nCategorías disponibles:")
                        for cat in categorias:
                            print(f"{cat.id}. {cat.nombre}")
                        try:
                            nueva_categoria_id = int(input("Nuevo ID de Categoría: "))
                            nueva_categoria_obj = session.query(Categoria).filter_by(id=nueva_categoria_id).first()
                            if nueva_categoria_obj:
                                producto_a_actualizar.categoria = nueva_categoria_obj
                            else:
                                print("Categoría no encontrada. Se mantendrá la anterior.")
                        except ValueError:
                            print("ID de Categoría inválido. Se mantendrá la anterior.")
                    else:
                        print("No hay categorías disponibles para actualizar.")


                session.commit()
                print(f"Producto '{producto_a_actualizar.nombre}' actualizado exitosamente.")
                press_any_key_to_continue()

            elif choice == '4':
                print_header("ELIMINAR PRODUCTO")
                producto_id_str = input("ID del producto a eliminar: ").strip()
                if not producto_id_str.isdigit():
                    print("ID inválido.")
                    press_any_key_to_continue()
                    continue
                producto_id = int(producto_id_str)
                
                producto_a_eliminar = session.query(Producto).filter_by(id=producto_id).first()
                if not producto_a_eliminar:
                    print("Producto no encontrado.")
                else:
                    confirm = input(f"¿Estás seguro de eliminar el producto '{producto_a_eliminar.nombre}' (ID: {producto_a_eliminar.id})? (s/n): ").lower()
                    if confirm == 's':
                        session.delete(producto_a_eliminar)
                        session.commit()
                        print(f"Producto '{producto_a_eliminar.nombre}' eliminado exitosamente.")
                    else:
                        print("Eliminación cancelada.")
                press_any_key_to_continue()

            elif choice == '0':
                break
            else:
                print("Opción no válida. Intente de nuevo.")
                press_any_key_to_continue()

        except IntegrityError as e:
            session.rollback()
            print(f"❌ Error de integridad: Este producto no puede ser eliminado o modificado debido a relaciones con otros registros (ej. pedidos, ventas). Detalles: {e.orig}")
            press_any_key_to_continue()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ Error de base de datos: {e}")
            press_any_key_to_continue()
        except Exception as e:
            session.rollback()
            print(f"❌ Ocurrió un error inesperado: {e}")
            press_any_key_to_continue()
        finally:
            session.close()

# --- CRUD para CLIENTES ---

def crud_clientes():
    while True:
        print_header("GESTIÓN DE CLIENTES")
        print("1. Ver todos los Clientes (desde VIEW)")
        print("2. Crear nuevo Cliente")
        print("3. Actualizar Cliente existente")
        print("4. Eliminar Cliente")
        print("0. Volver al menú principal")
        print("="*80)

        choice = input("Seleccione una opción: ")
        session = get_session()

        try:
            if choice == '1':
                print_header("LISTADO DE CLIENTES")
                clientes_resumen = session.query(VistaClienteResumen).all()
                if not clientes_resumen:
                    print("No hay clientes registrados.")
                else:
                    print(f"{'ID':<5} {'Código':<10} {'Nombre Completo':<30} {'DNI':<15} {'Teléfono':<20} {'Email':<30}")
                    print("-" * 120)
                    for c in clientes_resumen:
                        print(f"{c.id:<5} {c.codigo:<10} {c.nombre_completo:<30} {c.dni:<15} {c.telefono:<20} {c.email:<30}")
                    print("-" * 120)
                press_any_key_to_continue()

            elif choice == '2':
                print_header("CREAR NUEVO CLIENTE")
                codigo = input("Código del cliente: ").strip()
                nombre = input("Nombre: ").strip()
                apellido = input("Apellido: ").strip()
                dni = input("DNI: ").strip()
                telefono = input("Teléfono: ").strip()
                email = input("Email: ").strip()
                
                try:
                    fecha_nac_str = input("Fecha de Nacimiento (YYYY-MM-DD): ").strip()
                    fecha_nacimiento = datetime.strptime(fecha_nac_str, '%Y-%m-%d').date()
                except ValueError:
                    print("Formato de fecha de nacimiento inválido. Debe ser YYYY-MM-DD.")
                    press_any_key_to_continue()
                    continue

                # Dirección JSON
                print("\nIngrese datos de dirección:")
                calle = input("Calle: ").strip()
                numero = input("Número: ").strip()
                zona = input("Zona (opcional): ").strip()
                ciudad = input("Ciudad: ").strip()
                
                direccion_dict = {"calle": calle, "numero": numero, "ciudad": ciudad}
                if zona:
                    direccion_dict["zona"] = zona

                nuevo_cliente = Cliente(
                    codigo=codigo,
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni,
                    telefono=telefono,
                    email=email,
                    direccion=direccion_dict, # El TypeDecorator TipoJSON lo convertirá
                    fecha_nacimiento=fecha_nacimiento,
                    fecha_registro=datetime.now()
                )
                session.add(nuevo_cliente)
                session.commit()
                print(f"Cliente '{nuevo_cliente.nombre} {nuevo_cliente.apellido}' creado exitosamente.")
                press_any_key_to_continue()

            elif choice == '3':
                print_header("ACTUALIZAR CLIENTE")
                cliente_id_str = input("ID del cliente a actualizar: ").strip()
                if not cliente_id_str.isdigit():
                    print("ID inválido.")
                    press_any_key_to_continue()
                    continue
                cliente_id = int(cliente_id_str)
                
                cliente_a_actualizar = session.query(Cliente).filter_by(id=cliente_id).first()
                if not cliente_a_actualizar:
                    print("Cliente no encontrado.")
                else:
                    print(f"Editando Cliente: {cliente_a_actualizar.nombre} {cliente_a_actualizar.apellido}")
                    cliente_a_actualizar.nombre = input(f"Nuevo nombre ({cliente_a_actualizar.nombre}): ").strip() or cliente_a_actualizar.nombre
                    cliente_a_actualizar.apellido = input(f"Nuevo apellido ({cliente_a_actualizar.apellido}): ").strip() or cliente_a_actualizar.apellido
                    cliente_a_actualizar.dni = input(f"Nuevo DNI ({cliente_a_actualizar.dni}): ").strip() or cliente_a_actualizar.dni
                    cliente_a_actualizar.telefono = input(f"Nuevo teléfono ({cliente_a_actualizar.telefono}): ").strip() or cliente_a_actualizar.telefono
                    cliente_a_actualizar.email = input(f"Nuevo email ({cliente_a_actualizar.email}): ").strip() or cliente_a_actualizar.email
                    
                    # Actualizar dirección (opcional)
                    update_address = input("¿Desea actualizar la dirección? (s/n): ").lower()
                    if update_address == 's':
                        print("\nIngrese nueva dirección:")
                        current_dir = cliente_a_actualizar.direccion or {} # Obtener la dirección actual
                        calle = input(f"Nueva calle ({current_dir.get('calle', '')}): ").strip() or current_dir.get('calle', '')
                        numero = input(f"Nuevo número ({current_dir.get('numero', '')}): ").strip() or current_dir.get('numero', '')
                        zona = input(f"Nueva zona ({current_dir.get('zona', '')}): ").strip() or current_dir.get('zona', '')
                        ciudad = input(f"Nueva ciudad ({current_dir.get('ciudad', '')}): ").strip() or current_dir.get('ciudad', '')

                        new_direccion_dict = {"calle": calle, "numero": numero, "ciudad": ciudad}
                        if zona:
                            new_direccion_dict["zona"] = zona
                        cliente_a_actualizar.direccion = new_direccion_dict

                    session.commit()
                    print(f"Cliente '{cliente_a_actualizar.nombre} {cliente_a_actualizar.apellido}' actualizado exitosamente.")
                press_any_key_to_continue()

            elif choice == '4':
                print_header("ELIMINAR CLIENTE")
                cliente_id_str = input("ID del cliente a eliminar: ").strip()
                if not cliente_id_str.isdigit():
                    print("ID inválido.")
                    press_any_key_to_continue()
                    continue
                cliente_id = int(cliente_id_str)

                cliente_a_eliminar = session.query(Cliente).filter_by(id=cliente_id).first()
                if not cliente_a_eliminar:
                    print("Cliente no encontrado.")
                else:
                    confirm = input(f"¿Estás seguro de eliminar el cliente '{cliente_a_eliminar.nombre} {cliente_a_eliminar.apellido}' (ID: {cliente_a_eliminar.id})? (s/n): ").lower()
                    if confirm == 's':
                        session.delete(cliente_a_eliminar)
                        session.commit()
                        print(f"Cliente '{cliente_a_eliminar.nombre} {cliente_a_eliminar.apellido}' eliminado exitosamente.")
                    else:
                        print("Eliminación cancelada.")
                press_any_key_to_continue()

            elif choice == '0':
                break
            else:
                print("Opción no válida. Intente de nuevo.")
                press_any_key_to_continue()

        except IntegrityError as e:
            session.rollback()
            print(f"❌ Error de integridad: Este cliente no puede ser eliminado o modificado debido a relaciones con otros registros (ej. pedidos, facturas). Detalles: {e.orig}")
            press_any_key_to_continue()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ Error de base de datos: {e}")
            press_any_key_to_continue()
        except Exception as e:
            session.rollback()
            print(f"❌ Ocurrió un error inesperado: {e}")
            press_any_key_to_continue()
        finally:
            session.close()

# --- CRUD para EMPLEADOS ---

def crud_empleados():
    while True:
        print_header("GESTIÓN DE EMPLEADOS")
        print("1. Ver todos los Empleados (desde VIEW)")
        print("2. Crear nuevo Empleado")
        print("3. Actualizar Empleado existente")
        print("4. Eliminar Empleado")
        print("0. Volver al menú principal")
        print("="*80)

        choice = input("Seleccione una opción: ")
        session = get_session()

        try:
            if choice == '1':
                print_header("LISTADO DE EMPLEADOS")
                empleados_resumen = session.query(VistaEmpleadoResumen).all()
                if not empleados_resumen:
                    print("No hay empleados registrados.")
                else:
                    print(f"{'ID':<5} {'Código':<10} {'Nombre Completo':<30} {'Puesto':<25} {'Salario':<10} {'Email':<30}")
                    print("-" * 120)
                    for e in empleados_resumen:
                        print(f"{e.id:<5} {e.codigo:<10} {e.nombre_completo:<30} {e.nombre_puesto:<25} {e.salario:,.2f} {e.email:<30}")
                    print("-" * 120)
                press_any_key_to_continue()

            elif choice == '2':
                print_header("CREAR NUEVO EMPLEADO")
                codigo = input("Código del empleado: ").strip()
                nombre = input("Nombre: ").strip()
                apellido = input("Apellido: ").strip()
                dni = input("DNI: ").strip()
                telefono = input("Teléfono: ").strip()
                email = input("Email: ").strip()
                
                try:
                    salario = float(input("Salario: "))
                except ValueError:
                    print("Salario inválido.")
                    press_any_key_to_continue()
                    continue

                # Seleccionar Puesto
                puestos = session.query(Puesto).all()
                if not puestos:
                    print("No hay puestos. Crea uno antes de añadir empleados.")
                    press_any_key_to_continue()
                    continue
                print("\nPuestos disponibles:")
                for p in puestos:
                    print(f"{p.id}. {p.nombre} (Salario: {p.salario_minimo:,.2f}-{p.salario_maximo:,.2f})")
                
                try:
                    puesto_id = int(input("ID de Puesto: "))
                    puesto_obj = session.query(Puesto).filter_by(id=puesto_id).first()
                    if not puesto_obj:
                        print("Puesto no encontrado.")
                        press_any_key_to_continue()
                        continue
                except ValueError:
                    print("ID de Puesto inválido.")
                    press_any_key_to_continue()
                    continue

                nuevo_empleado = Empleado(
                    codigo=codigo,
                    nombre=nombre,
                    apellido=apellido,
                    dni=dni,
                    telefono=telefono,
                    email=email,
                    salario=salario,
                    fecha_ingreso=datetime.now(),
                    puesto=puesto_obj
                )
                session.add(nuevo_empleado)
                session.commit()
                print(f"Empleado '{nuevo_empleado.nombre} {nuevo_empleado.apellido}' creado exitosamente.")
                press_any_key_to_continue()

            elif choice == '3':
                print_header("ACTUALIZAR EMPLEADO")
                empleado_id_str = input("ID del empleado a actualizar: ").strip()
                if not empleado_id_str.isdigit():
                    print("ID inválido.")
                    press_any_key_to_continue()
                    continue
                empleado_id = int(empleado_id_str)
                
                empleado_a_actualizar = session.query(Empleado).filter_by(id=empleado_id).first()
                if not empleado_a_actualizar:
                    print("Empleado no encontrado.")
                else:
                    print(f"Editando Empleado: {empleado_a_actualizar.nombre} {empleado_a_actualizar.apellido}")
                    empleado_a_actualizar.nombre = input(f"Nuevo nombre ({empleado_a_actualizar.nombre}): ").strip() or empleado_a_actualizar.nombre
                    empleado_a_actualizar.apellido = input(f"Nuevo apellido ({empleado_a_actualizar.apellido}): ").strip() or empleado_a_actualizar.apellido
                    empleado_a_actualizar.dni = input(f"Nuevo DNI ({empleado_a_actualizar.dni}): ").strip() or empleado_a_actualizar.dni
                    empleado_a_actualizar.telefono = input(f"Nuevo teléfono ({empleado_a_actualizar.telefono}): ").strip() or empleado_a_actualizar.telefono
                    empleado_a_actualizar.email = input(f"Nuevo email ({empleado_a_actualizar.email}): ").strip() or empleado_a_actualizar.email
                    
                    salario_str = input(f"Nuevo salario ({empleado_a_actualizar.salario:,.2f}): ").strip()
                    if salario_str:
                        try:
                            empleado_a_actualizar.salario = float(salario_str)
                        except ValueError:
                            print("Salario inválido. Se mantendrá el anterior.")
                    
                    # Opcional: Actualizar Puesto
                    update_puesto = input("¿Desea actualizar el puesto? (s/n): ").lower()
                    if update_puesto == 's':
                        puestos = session.query(Puesto).all()
                        if puestos:
                            print("\nPuestos disponibles:")
                            for p in puestos:
                                print(f"{p.id}. {p.nombre}")
                            try:
                                nuevo_puesto_id = int(input("Nuevo ID de Puesto: "))
                                nuevo_puesto_obj = session.query(Puesto).filter_by(id=nuevo_puesto_id).first()
                                if nuevo_puesto_obj:
                                    empleado_a_actualizar.puesto = nuevo_puesto_obj
                                else:
                                    print("Puesto no encontrado. Se mantendrá el anterior.")
                            except ValueError:
                                print("ID de Puesto inválido. Se mantendrá el anterior.")
                        else:
                            print("No hay puestos disponibles para actualizar.")

                    session.commit()
                    print(f"Empleado '{empleado_a_actualizar.nombre} {empleado_a_actualizar.apellido}' actualizado exitosamente.")
                press_any_key_to_continue()

            elif choice == '4':
                print_header("ELIMINAR EMPLEADO")
                empleado_id_str = input("ID del empleado a eliminar: ").strip()
                if not empleado_id_str.isdigit():
                    print("ID inválido.")
                    press_any_key_to_continue()
                    continue
                empleado_id = int(empleado_id_str)

                empleado_a_eliminar = session.query(Empleado).filter_by(id=empleado_id).first()
                if not empleado_a_eliminar:
                    print("Empleado no encontrado.")
                else:
                    confirm = input(f"¿Estás seguro de eliminar el empleado '{empleado_a_eliminar.nombre} {empleado_a_eliminar.apellido}' (ID: {empleado_a_eliminar.id})? (s/n): ").lower()
                    if confirm == 's':
                        session.delete(empleado_a_eliminar)
                        session.commit()
                        print(f"Empleado '{empleado_a_eliminar.nombre} {empleado_a_eliminar.apellido}' eliminado exitosamente.")
                    else:
                        print("Eliminación cancelada.")
                press_any_key_to_continue()

            elif choice == '0':
                break
            else:
                print("Opción no válida. Intente de nuevo.")
                press_any_key_to_continue()

        except IntegrityError as e:
            session.rollback()
            print(f"❌ Error de integridad: Este empleado no puede ser eliminado o modificado debido a relaciones con otros registros (ej. pedidos, ventas, departamentos). Detalles: {e.orig}")
            press_any_key_to_continue()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"❌ Error de base de datos: {e}")
            press_any_key_to_continue()
        except Exception as e:
            session.rollback()
            print(f"❌ Ocurrió un error inesperado: {e}")
            press_any_key_to_continue()
        finally:
            session.close()

# --- Menú Principal de la Aplicación ---

def main_app_menu():
    """Menú principal para seleccionar un CRUD."""
    while True:
        print_header("MENÚ PRINCIPAL DE LA APLICACIÓN")
        print("Seleccione una entidad para gestionar:")
        print("1. Productos")
        print("2. Clientes")
        print("3. Empleados")
        print("0. Salir de la aplicación")
        print("="*80)

        choice = input("Seleccione una opción: ")

        if choice == '1':
            crud_productos()
        elif choice == '2':
            crud_clientes()
        elif choice == '3':
            crud_empleados()
        elif choice == '0':
            print("Saliendo de la aplicación. ¡Hasta luego!")
            break
        else:
            print("Opción no válida. Por favor, intente de nuevo.")
            press_any_key_to_continue()

if __name__ == '__main__':
    print("Iniciando la aplicación de gestión...")
    print("Asegúrese de haber ejecutado database.py, queries.py e inserts.py previamente.")
    main_app_menu()