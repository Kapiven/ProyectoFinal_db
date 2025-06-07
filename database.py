from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Text, Boolean, CheckConstraint, event, DDL, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.dialects import postgresql
import json
import re # Para validación de RegEx
import psycopg2 # Necesario para las funciones SQL en queries.py
from datetime import datetime, date

# Configuración de la base de datos
DATABASE_URL = "postgresql+psycopg2://postgres:datos2025@localhost/institucion"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def obtener_session():
    """Retorna una nueva instancia de sesión para interactuar con la base de datos."""
    return Session()

# --- TypeDecorators Personalizados ---

class TipoDNI(TypeDecorator):
    """Define un tipo de dato para DNI (8 dígitos + 1 letra)."""
    impl = String(10) # DNI español: 8 números + 1 letra

    cache_ok = True # Optimizacion para SQLAlchemy 1.4+

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not re.fullmatch(r'^\d{8}[TRWAGMYFPDXBNJZSQVHLCKE]$', value.upper()):
                raise ValueError("Formato de DNI inválido. Debe ser 8 números seguidos de una letra (ej. 12345678A).")
            return value.upper()
        return value

    def process_result_value(self, value, dialect):
        return value

class TipoEmail(TypeDecorator):
    """Define un tipo de dato para direcciones de email."""
    impl = String(255)

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not re.fullmatch(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValueError("Formato de email inválido.")
            return value.lower()
        return value

    def process_result_value(self, value, dialect):
        return value

class TipoTelefono(TypeDecorator):
    """Define un tipo de dato para números de teléfono (con código de país)."""
    impl = String(20) # Ej. +XX YYY ZZZ ZZZ

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            # Permite formatos como +XX XXX XXX XXX, XXXXXXXXXX, o con guiones/espacios
            if not re.fullmatch(r'^\+?\d[\d\s-]{7,18}\d$', value):
                raise ValueError("Formato de teléfono inválido. Debe contener solo números, espacios, guiones y opcionalmente un '+' al inicio.")
            return value.replace(" ", "").replace("-", "") # Normalizar para almacenamiento
        return value

    def process_result_value(self, value, dialect):
        return value

class TipoJSON(TypeDecorator):
    """Define un tipo de dato para almacenar JSON en la base de datos."""
    impl = TEXT 

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value

class TipoMoneda(TypeDecorator):
    """Define un tipo de dato para almacenar valores de moneda como string "$XX.XX"."""
    impl = String(20) # Suficiente para "$999,999,999.99"

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, str) or not re.fullmatch(r'^\$\d{1,3}(,\d{3})*(\.\d{2})?$', value):
                raise ValueError("Formato de moneda inválido. Debe ser '$X.XX' (ej. $12.34 o $1,234.56).")
            return value
        return value

    def process_result_value(self, value, dialect):
        return value

# --- Definición de Modelos de Tablas ---

class Categoria(Base):
    __tablename__ = 'categorias'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    activa = Column(Boolean, default=True)

    productos = relationship("Producto", back_populates="categoria")

    def __repr__(self):
        return f"<Categoria(id={self.id}, nombre='{self.nombre}')>"

class Proveedor(Base):
    __tablename__ = 'proveedores'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    contacto = Column(String(100))
    telefono = Column(TipoTelefono)
    email = Column(TipoEmail)
    direccion = Column(TipoJSON) # Almacena como JSON
    fecha_registro = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)

    productos = relationship("Producto", secondary="producto_proveedor", back_populates="proveedores")
    compras = relationship("Compra", back_populates="proveedor")

    def __repr__(self):
        return f"<Proveedor(id={self.id}, nombre='{self.nombre}')>"

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5)
    categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)

    categoria = relationship("Categoria", back_populates="productos")
    proveedores = relationship("Proveedor", secondary="producto_proveedor", back_populates="productos")
    inventarios = relationship("Inventario", back_populates="producto")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="producto")
    detalle_pedidos = relationship("DetallePedido", back_populates="producto")
    detalle_ventas = relationship("DetalleVenta", back_populates="producto")
    detalle_compras = relationship("DetalleCompra", back_populates="producto")

    __table_args__ = (
        CheckConstraint('precio > 0', name='precio_positivo'),
        CheckConstraint('stock >= 0', name='stock_no_negativo'),
        CheckConstraint('stock_minimo >= 0', name='stock_minimo_no_negativo')
    )

    def __repr__(self):
        return f"<Producto(id={self.id}, nombre='{self.nombre}', stock={self.stock})>"

# Tabla de cruce para relación muchos a muchos Producto-Proveedor
class ProductoProveedor(Base):
    __tablename__ = 'producto_proveedor'
    producto_id = Column(Integer, ForeignKey('productos.id'), primary_key=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), primary_key=True)
    __table_args__ = (UniqueConstraint('producto_id', 'proveedor_id', name='uq_producto_proveedor'),)

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50))
    dni = Column(TipoDNI, unique=True, nullable=False) # Usa TipoDNI
    telefono = Column(TipoTelefono) # Usa TipoTelefono
    email = Column(TipoEmail, unique=True) # Usa TipoEmail
    direccion = Column(TipoJSON) # Almacena como JSON
    fecha_nacimiento = Column(Date)
    fecha_registro = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)

    pedidos = relationship("Pedido", back_populates="cliente")
    facturas = relationship("Factura", back_populates="cliente")
    servicios = relationship("Servicio", secondary="cliente_servicio", back_populates="clientes")

    __table_args__ = (
        CheckConstraint("fecha_nacimiento <= CURRENT_DATE", name='fecha_nacimiento_valida'),
    )

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre} {self.apellido}')>"

# Tabla de cruce para relación muchos a muchos Cliente-Servicio
class ClienteServicio(Base):
    __tablename__ = 'cliente_servicio'
    cliente_id = Column(Integer, ForeignKey('clientes.id'), primary_key=True)
    servicio_id = Column(Integer, ForeignKey('servicios.id'), primary_key=True)
    fecha_contratacion = Column(DateTime, default=datetime.now)
    __table_args__ = (UniqueConstraint('cliente_id', 'servicio_id', name='uq_cliente_servicio'),)

class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    total = Column(Numeric(12, 2), default=0.00) # Se actualizará por trigger
    estado = Column(String(20), default='pendiente') # pendiente, procesando, completado, cancelado
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    observaciones = Column(Text)

    cliente = relationship("Cliente", back_populates="pedidos")
    empleado = relationship("Empleado", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total >= 0", name='total_pedido_no_negativo'),
        CheckConstraint("estado IN ('pendiente', 'procesando', 'completado', 'cancelado')", name='estado_pedido_valido')
    )

    def __repr__(self):
        return f"<Pedido(id={self.id}, numero='{self.numero}', total={self.total}, estado='{self.estado}')>"

class DetallePedido(Base):
    __tablename__ = 'detalle_pedidos'
    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False) # Cantidad * PrecioUnitario * (1 - Descuento/100)
    descuento = Column(Numeric(5, 2), default=0.00) # Porcentaje de descuento

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalle_pedidos")

    __table_args__ = (
        CheckConstraint('cantidad > 0', name='cantidad_positiva_dp'),
        CheckConstraint('precio_unitario > 0', name='precio_unitario_positivo_dp'),
        CheckConstraint('subtotal >= 0', name='subtotal_no_negativo_dp'),
        CheckConstraint('descuento >= 0 AND descuento <= 100', name='descuento_valido_dp')
    )

    def __repr__(self):
        return f"<DetallePedido(id={self.id}, pedido_id={self.pedido_id}, producto_id={self.producto_id}, cantidad={self.cantidad})>"

class Servicio(Base):
    __tablename__ = 'servicios'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    costo = Column(TipoMoneda, nullable=False) # Usa TipoMoneda
    duracion = Column(Integer) # En horas, por ejemplo
    activo = Column(Boolean, default=True)

    clientes = relationship("Cliente", secondary="cliente_servicio", back_populates="servicios")

    __table_args__ = (
        CheckConstraint('duracion > 0', name='duracion_positiva'),
    )

    def __repr__(self):
        return f"<Servicio(id={self.id}, nombre='{self.nombre}', costo='{self.costo}')>"

class Puesto(Base):
    __tablename__ = 'puestos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    salario_minimo = Column(Numeric(10, 2))
    salario_maximo = Column(Numeric(10, 2))
    activo = Column(Boolean, default=True)

    empleados = relationship("Empleado", back_populates="puesto")

    __table_args__ = (
        CheckConstraint('salario_minimo >= 0', name='salario_minimo_positivo'),
        CheckConstraint('salario_maximo >= salario_minimo', name='salario_maximo_valido')
    )

    def __repr__(self):
        return f"<Puesto(id={self.id}, nombre='{self.nombre}')>"

class Departamento(Base):
    __tablename__ = 'departamentos'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    presupuesto = Column(Numeric(12, 2), default=0.00)
    activo = Column(Boolean, default=True)

    empleados = relationship("Empleado", secondary="empleado_departamento", back_populates="departamentos")

    __table_args__ = (
        CheckConstraint('presupuesto >= 0', name='presupuesto_no_negativo'),
    )

    def __repr__(self):
        return f"<Departamento(id={self.id}, nombre='{self.nombre}')>"

# Tabla de cruce para relación muchos a muchos Empleado-Departamento
class EmpleadoDepartamento(Base):
    __tablename__ = 'empleado_departamento'
    empleado_id = Column(Integer, ForeignKey('empleados.id'), primary_key=True)
    departamento_id = Column(Integer, ForeignKey('departamentos.id'), primary_key=True)
    __table_args__ = (UniqueConstraint('empleado_id', 'departamento_id', name='uq_empleado_departamento'),)

class Empleado(Base):
    __tablename__ = 'empleados'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50))
    dni = Column(TipoDNI, unique=True, nullable=False) # Usa TipoDNI
    telefono = Column(TipoTelefono) # Usa TipoTelefono
    email = Column(TipoEmail, unique=True) # Usa TipoEmail
    salario = Column(Numeric(10, 2), nullable=False)
    fecha_ingreso = Column(DateTime, default=datetime.now)
    puesto_id = Column(Integer, ForeignKey('puestos.id'), nullable=False)
    activo = Column(Boolean, default=True)

    puesto = relationship("Puesto", back_populates="empleados")
    departamentos = relationship("Departamento", secondary="empleado_departamento", back_populates="empleados")
    pedidos = relationship("Pedido", back_populates="empleado")
    ventas = relationship("Venta", back_populates="empleado")
    compras = relationship("Compra", back_populates="empleado")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="empleado")

    __table_args__ = (
        CheckConstraint('salario >= 0', name='salario_no_negativo_emp'),
        CheckConstraint('fecha_ingreso <= CURRENT_TIMESTAMP', name='fecha_ingreso_valida')
    )

    def __repr__(self):
        return f"<Empleado(id={self.id}, nombre='{self.nombre} {self.apellido}')>"

class Factura(Base):
    __tablename__ = 'facturas'
    id = Column(Integer, primary_key=True)
    numero = Column(String(50), unique=True, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    subtotal = Column(Numeric(12, 2), nullable=False)
    impuesto = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    estado = Column(String(20), default='pendiente') # pendiente, pagada, vencida, anulada
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)

    cliente = relationship("Cliente", back_populates="facturas")
    pagos = relationship("Pago", back_populates="factura", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='subtotal_no_negativo_fact'),
        CheckConstraint('impuesto >= 0', name='impuesto_no_negativo_fact'),
        CheckConstraint('total >= 0', name='total_no_negativo_fact'),
        CheckConstraint("estado IN ('pendiente', 'pagada', 'vencida', 'anulada')", name='estado_factura_valido')
    )

    def __repr__(self):
        return f"<Factura(id={self.id}, numero='{self.numero}', total={self.total}, estado='{self.estado}')>"

class Pago(Base):
    __tablename__ = 'pagos'
    id = Column(Integer, primary_key=True)
    numero = Column(String(50), unique=True, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    monto = Column(Numeric(12, 2), nullable=False)
    metodo = Column(String(50), nullable=False)
    referencia = Column(String(100))
    factura_id = Column(Integer, ForeignKey('facturas.id'), nullable=False)

    factura = relationship("Factura", back_populates="pagos")

    __table_args__ = (
        CheckConstraint('monto > 0', name='monto_pago_positivo'),
        CheckConstraint("metodo IN ('efectivo', 'tarjeta', 'transferencia', 'cheque')", name='metodo_pago_valido')
    )

    def __repr__(self):
        return f"<Pago(id={self.id}, numero='{self.numero}', monto={self.monto})>"

class Sucursal(Base):
    __tablename__ = 'sucursales'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(TipoJSON) # Almacena como JSON
    telefono = Column(TipoTelefono) # Usa TipoTelefono
    email = Column(TipoEmail) # Usa TipoEmail
    activa = Column(Boolean, default=True)

    inventarios = relationship("Inventario", back_populates="sucursal")
    ventas = relationship("Venta", back_populates="sucursal")

    def __repr__(self):
        return f"<Sucursal(id={self.id}, nombre='{self.nombre}')>"

class Venta(Base):
    __tablename__ = 'ventas'
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    total = Column(Numeric(12, 2), default=0.00) # Se actualizará por trigger si hay uno
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    sucursal_id = Column(Integer, ForeignKey('sucursales.id'), nullable=False)

    empleado = relationship("Empleado", back_populates="ventas")
    sucursal = relationship("Sucursal", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('total >= 0', name='total_venta_no_negativo'),
    )

    def __repr__(self):
        return f"<Venta(id={self.id}, total={self.total}, fecha='{self.fecha.strftime('%Y-%m-%d')}')>"

class DetalleVenta(Base):
    __tablename__ = 'detalle_ventas'
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey('ventas.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False) # Cantidad * PrecioUnitario

    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalle_ventas")

    __table_args__ = (
        CheckConstraint('cantidad > 0', name='cantidad_positiva_dv'),
        CheckConstraint('precio_unitario > 0', name='precio_unitario_positivo_dv'),
        CheckConstraint('subtotal >= 0', name='subtotal_no_negativo_dv')
    )

    def __repr__(self):
        return f"<DetalleVenta(id={self.id}, venta_id={self.venta_id}, producto_id={self.producto_id}, cantidad={self.cantidad})>"

class Compra(Base):
    __tablename__ = 'compras'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    total = Column(Numeric(12, 2), default=0.00) # Se actualizará por trigger
    estado = Column(String(20), default='pendiente') # pendiente, recibida, cancelada
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)

    proveedor = relationship("Proveedor", back_populates="compras")
    empleado = relationship("Empleado", back_populates="compras")
    detalles = relationship("DetalleCompra", back_populates="compra", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('total >= 0', name='total_compra_no_negativo'),
        CheckConstraint("estado IN ('pendiente', 'recibida', 'cancelada')", name='estado_compra_valido')
    )

    def __repr__(self):
        return f"<Compra(id={self.id}, numero='{self.numero}', total={self.total}, estado='{self.estado}')>"

class DetalleCompra(Base):
    __tablename__ = 'detalle_compras'
    id = Column(Integer, primary_key=True)
    compra_id = Column(Integer, ForeignKey('compras.id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False) # Cantidad * PrecioUnitario

    compra = relationship("Compra", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalle_compras")

    __table_args__ = (
        CheckConstraint('cantidad > 0', name='cantidad_positiva_dc'),
        CheckConstraint('precio_unitario > 0', name='precio_unitario_positivo_dc'),
        CheckConstraint('subtotal >= 0', name='subtotal_no_negativo_dc')
    )

    def __repr__(self):
        return f"<DetalleCompra(id={self.id}, compra_id={self.compra_id}, producto_id={self.producto_id}, cantidad={self.cantidad})>"

class Inventario(Base):
    __tablename__ = 'inventario'
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    sucursal_id = Column(Integer, ForeignKey('sucursales.id'), nullable=False)
    cantidad = Column(Integer, default=0)
    ubicacion = Column(String(50)) # Ej. "Pasillo A, Estante 3"
    fecha_actualizacion = Column(DateTime, default=datetime.now)

    producto = relationship("Producto", back_populates="inventarios")
    sucursal = relationship("Sucursal", back_populates="inventarios")

    __table_args__ = (UniqueConstraint('producto_id', 'sucursal_id', name='uq_producto_sucursal_inventario'),)

    producto = relationship("Producto", backref="inventario_entries")
    sucursal = relationship("Sucursal", backref="inventario_entries")

    def __repr__(self):
        return f"<Inventario(id={self.id}, producto_id={self.producto_id}, sucursal_id={self.sucursal_id}, cantidad={self.cantidad})>"

class MovimientoInventario(Base):
    __tablename__ = 'movimientos_inventario'
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    tipo = Column(String(20), nullable=False) # entrada, salida, ajuste
    cantidad = Column(Integer, nullable=False) # Positivo para entrada, negativo para salida/ajuste negativo
    motivo = Column(Text)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)

    producto = relationship("Producto", back_populates="movimientos_inventario")
    empleado = relationship("Empleado", back_populates="movimientos_inventario")

    __table_args__ = (
        CheckConstraint("tipo IN ('entrada', 'salida', 'ajuste')", name='tipo_movimiento_valido'),
        CheckConstraint('cantidad != 0', name='cantidad_movimiento_no_cero')
    )

    def __repr__(self):
        return f"<MovimientoInventario(id={self.id}, producto_id={self.producto_id}, tipo='{self.tipo}', cantidad={self.cantidad})>"


# --- Vistas SQL Mapeadas para ORM ---

# Creamos una base separada para las vistas que no deben ser creadas por Base.metadata.create_all
BaseView = declarative_base() # <--- NUEVA BASE SOLO PARA VISTAS

# Vista para Productos (usada en CRUD de Productos)
class VistaProductoDetalle(BaseView):
    __tablename__ = 'vista_productos_detalle' 
    
    __table_args__ = ({'extend_existing': True})

    id = Column(Integer, primary_key=True) # La VIEW debe retornar el ID de Producto
    codigo = Column(String)
    nombre_producto = Column(String)
    precio = Column(Numeric)
    stock = Column(Integer)
    stock_minimo = Column(Integer)
    nombre_categoria = Column(String)
    fecha_creacion = Column(DateTime)
    

# Vista para Clientes (usada en CRUD de Clientes)
class VistaClienteResumen(BaseView):
    __tablename__ = 'vista_clientes_resumen' 
    
    __table_args__ = ({'extend_existing': True})

    id = Column(Integer, primary_key=True) # La VIEW debe retornar el ID de Cliente
    codigo = Column(String)
    nombre_completo = Column(String)
    dni = Column(TipoDNI) 
    telefono = Column(TipoTelefono)
    email = Column(TipoEmail)
    fecha_registro = Column(DateTime)
    

# Vista para Empleados (usada en CRUD de Empleados)
class VistaEmpleadoResumen(BaseView):
    __tablename__ = 'vista_empleados_resumen'
    
    __table_args__ = ({'extend_existing': True})

    id = Column(Integer, primary_key=True) # La VIEW debe retornar el ID de Empleado
    codigo = Column(String)
    nombre_completo = Column(String)
    email = Column(TipoEmail)
    telefono = Column(TipoTelefono)
    salario = Column(Numeric)
    nombre_puesto = Column(String)
    fecha_ingreso = Column(DateTime)

# --- Función para crear todas las tablas ---
def crear_tablas():
    print("Creando tablas en la base de datos...")
    try:
        Base.metadata.create_all(engine)
        print("Tablas creadas exitosamente.")
        return True
    except Exception as e:
        print(f"Error al crear tablas: {e}")
        return False

# Ejecutar la creación de tablas si el script se ejecuta directamente
if __name__ == '__main__':
    crear_tablas()