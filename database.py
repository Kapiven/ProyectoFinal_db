from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey, 
    DateTime, Boolean, Text, Table, Numeric, CheckConstraint
)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import TypeDecorator
from datetime import datetime
import re

# Configuración de la base de datos
engine = create_engine('postgresql://usuario:contraseña@localhost/proyecto_bd')
Session = sessionmaker(bind=engine)
Base = declarative_base()

# --------------------------------------------
# TIPOS DE DATOS PERSONALIZADOS (5 requeridos)
# --------------------------------------------

class TipoEmail(TypeDecorator):
    """Valida formato de email"""
    impl = String(100)

    def process_bind_param(self, value, dialect):
        if value and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            raise ValueError("Formato de email inválido")
        return value

class TipoDNI(TypeDecorator):
    """Valida DNI (8 dígitos + letra opcional)"""
    impl = String(10)

    def process_bind_param(self, value, dialect):
        if value and not re.match(r'^\d{8}[A-Za-z]?$', value):
            raise ValueError("DNI debe tener 8 dígitos y una letra opcional")
        return value

class TipoTelefono(TypeDecorator):
    """Valida teléfono (+XX XXX XXX XXX)"""
    impl = String(15)

    def process_bind_param(self, value, dialect):
        if value and not re.match(r'^\+\d{2,3} \d{3} \d{3} \d{3}$', value):
            raise ValueError("Formato: +XX XXX XXX XXX")
        return value

class TipoJSON(TypeDecorator):
    """Almacena datos JSON validados"""
    impl = Text

    def process_bind_param(self, value, dialect):
        if value:
            import json
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value:
            import json
            return json.loads(value)
        return value

class TipoMoneda(TypeDecorator):
    """Valida formato $XX.XX"""
    impl = String(10)

    def process_bind_param(self, value, dialect):
        if value and not re.match(r'^\$\d+\.\d{2}$', value):
            raise ValueError("Formato: $XX.XX")
        return value

# --------------------------------------------
# TABLAS DE CRUCE N:M (3 requeridas)
# --------------------------------------------

producto_proveedor = Table(
    'producto_proveedor',
    Base.metadata,
    Column('producto_id', Integer, ForeignKey('productos.id'), primary_key=True),
    Column('proveedor_id', Integer, ForeignKey('proveedores.id'), primary_key=True),
    Column('precio_compra', Numeric(10, 2)),
    Column('fecha_acuerdo', DateTime, default=datetime.now)
)

cliente_servicio = Table(
    'cliente_servicio',
    Base.metadata,
    Column('cliente_id', Integer, ForeignKey('clientes.id'), primary_key=True),
    Column('servicio_id', Integer, ForeignKey('servicios.id'), primary_key=True),
    Column('fecha_contratacion', DateTime, default=datetime.now),
    Column('estado', String(20), default='activo')
)

empleado_departamento = Table(
    'empleado_departamento',
    Base.metadata,
    Column('empleado_id', Integer, ForeignKey('empleados.id'), primary_key=True),
    Column('departamento_id', Integer, ForeignKey('departamentos.id'), primary_key=True),
    Column('fecha_asignacion', DateTime, default=datetime.now),
    Column('cargo', String(50))
)

# --------------------------------------------
# MODELOS PRINCIPALES (20 TABLAS)
# --------------------------------------------

class Categoria(Base):
    __tablename__ = 'categorias'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)
    activa = Column(Boolean, default=True)
    
    # Relaciones
    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=5)
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    fecha_creacion = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    categoria = relationship("Categoria", back_populates="productos")
    proveedores = relationship("Proveedor", secondary=producto_proveedor, back_populates="productos")
    detalles_pedido = relationship("DetallePedido", back_populates="producto")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="producto")

    # Validaciones a nivel de BD
    __table_args__ = (
        CheckConstraint('precio > 0', name='precio_positivo'),
        CheckConstraint('stock >= 0', name='stock_no_negativo'),
        CheckConstraint('stock_minimo >= 0', name='stock_minimo_no_negativo')
    )

class Proveedor(Base):
    __tablename__ = 'proveedores'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    contacto = Column(String(100))
    telefono = Column(TipoTelefono)
    email = Column(TipoEmail)
    direccion = Column(TipoJSON)
    fecha_registro = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    productos = relationship("Producto", secondary=producto_proveedor, back_populates="proveedores")
    compras = relationship("Compra", back_populates="proveedor")

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    dni = Column(TipoDNI, unique=True)
    telefono = Column(TipoTelefono)
    email = Column(TipoEmail)
    direccion = Column(TipoJSON)
    fecha_nacimiento = Column(DateTime)
    fecha_registro = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    pedidos = relationship("Pedido", back_populates="cliente")
    facturas = relationship("Factura", back_populates="cliente")
    servicios = relationship("Servicio", secondary=cliente_servicio, back_populates="clientes")

class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
    fecha = Column(DateTime, default=datetime.now)
    estado = Column(String(20), nullable=False, default='pendiente')
    total = Column(Numeric(10, 2), default=0)
    observaciones = Column(Text)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    empleado_id = Column(Integer, ForeignKey('empleados.id'))
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="pedidos")
    empleado = relationship("Empleado", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido")

    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'procesando', 'completado', 'cancelado')", name='estado_valido'),
        CheckConstraint('total >= 0', name='total_no_negativo')
    )

class DetallePedido(Base):
    __tablename__ = 'detalle_pedidos'
    id = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    descuento = Column(Numeric(5, 2), default=0)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_pedido")

    __table_args__ = (
        CheckConstraint('cantidad > 0', name='cantidad_positiva'),
        CheckConstraint('precio_unitario > 0', name='precio_unitario_positivo'),
        CheckConstraint('descuento >= 0 AND descuento <= 100', name='descuento_valido')
    )

class Servicio(Base):
    __tablename__ = 'servicios'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    costo = Column(TipoMoneda)
    duracion = Column(Integer)  # Duración en horas
    activo = Column(Boolean, default=True)
    
    # Relaciones
    clientes = relationship("Cliente", secondary=cliente_servicio, back_populates="servicios")

class Empleado(Base):
    __tablename__ = 'empleados'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    dni = Column(TipoDNI, unique=True)
    telefono = Column(TipoTelefono)
    email = Column(TipoEmail)
    salario = Column(Numeric(10, 2))
    fecha_ingreso = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)
    puesto_id = Column(Integer, ForeignKey('puestos.id'))
    
    # Relaciones
    puesto = relationship("Puesto", back_populates="empleados")
    departamentos = relationship("Departamento", secondary=empleado_departamento, back_populates="empleados")
    pedidos = relationship("Pedido", back_populates="empleado")
    ventas = relationship("Venta", back_populates="empleado")

    __table_args__ = (
        CheckConstraint('salario > 0', name='salario_positivo'),
    )

class Departamento(Base):
    __tablename__ = 'departamentos'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    presupuesto = Column(Numeric(12, 2))
    activo = Column(Boolean, default=True)
    
    # Relaciones
    empleados = relationship("Empleado", secondary=empleado_departamento, back_populates="departamentos")

class Puesto(Base):
    __tablename__ = 'puestos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    salario_minimo = Column(Numeric(10, 2))
    salario_maximo = Column(Numeric(10, 2))
    activo = Column(Boolean, default=True)
    
    # Relaciones
    empleados = relationship("Empleado", back_populates="puesto")

    __table_args__ = (
        CheckConstraint('salario_minimo <= salario_maximo', name='salarios_coherentes'),
    )

class Factura(Base):
    __tablename__ = 'facturas'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
    fecha = Column(DateTime, default=datetime.now)
    subtotal = Column(Numeric(10, 2), nullable=False)
    impuesto = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), default='pendiente')
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="facturas")
    pagos = relationship("Pago", back_populates="factura")

    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'pagada', 'vencida', 'anulada')", name='estado_factura_valido'),
    )

class Pago(Base):
    __tablename__ = 'pagos'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
    fecha = Column(DateTime, default=datetime.now)
    monto = Column(Numeric(10, 2), nullable=False)
    metodo = Column(String(50), nullable=False)
    referencia = Column(String(100))
    factura_id = Column(Integer, ForeignKey('facturas.id'))
    
    # Relaciones
    factura = relationship("Factura", back_populates="pagos")

    __table_args__ = (
        CheckConstraint('monto > 0', name='monto_positivo'),
        CheckConstraint("metodo IN ('efectivo', 'tarjeta', 'transferencia', 'cheque')", name='metodo_valido')
    )

class Venta(Base):
    __tablename__ = 'ventas'
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    total = Column(Numeric(10, 2), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'))
    sucursal_id = Column(Integer, ForeignKey('sucursales.id'))
    
    # Relaciones
    empleado = relationship("Empleado", back_populates="ventas")
    sucursal = relationship("Sucursal", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = 'detalle_ventas'
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey('ventas.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    
    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto")

class Sucursal(Base):
    __tablename__ = 'sucursales'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(200))
    telefono = Column(TipoTelefono)
    email = Column(TipoEmail)
    activa = Column(Boolean, default=True)
    
    # Relaciones
    ventas = relationship("Venta", back_populates="sucursal")
    inventarios = relationship("Inventario", back_populates="sucursal")

class Inventario(Base):
    __tablename__ = 'inventario'
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('productos.id'))
    sucursal_id = Column(Integer, ForeignKey('sucursales.id'))
    cantidad = Column(Integer, nullable=False, default=0)
    ubicacion = Column(String(50))
    fecha_actualizacion = Column(DateTime, default=datetime.now)
    
    # Relaciones
    producto = relationship("Producto")
    sucursal = relationship("Sucursal", back_populates="inventarios")

    __table_args__ = (
        CheckConstraint('cantidad >= 0', name='cantidad_inventario_no_negativa'),
    )

class MovimientoInventario(Base):
    __tablename__ = 'movimientos_inventario'
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    tipo = Column(String(20), nullable=False)  # entrada, salida, ajuste
    cantidad = Column(Integer, nullable=False)
    motivo = Column(String(100))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    empleado_id = Column(Integer, ForeignKey('empleados.id'))
    
    # Relaciones
    producto = relationship("Producto", back_populates="movimientos_inventario")
    empleado = relationship("Empleado")

    __table_args__ = (
        CheckConstraint("tipo IN ('entrada', 'salida', 'ajuste')", name='tipo_movimiento_valido'),
    )

class Compra(Base):
    __tablename__ = 'compras'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
    fecha = Column(DateTime, default=datetime.now)
    total = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), default='pendiente')
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    empleado_id = Column(Integer, ForeignKey('empleados.id'))
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="compras")
    empleado = relationship("Empleado")
    detalles = relationship("DetalleCompra", back_populates="compra")

    __table_args__ = (
        CheckConstraint("estado IN ('pendiente', 'recibida', 'cancelada')", name='estado_compra_valido'),
    )

class DetalleCompra(Base):
    __tablename__ = 'detalle_compras'
    id = Column(Integer, primary_key=True)
    compra_id = Column(Integer, ForeignKey('compras.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    
    # Relaciones
    compra = relationship("Compra", back_populates="detalles")
    producto = relationship("Producto")

    __table_args__ = (
        CheckConstraint('cantidad > 0', name='cantidad_compra_positiva'),
        CheckConstraint('precio_unitario > 0', name='precio_compra_positivo')
    )

# --------------------------------------------
# FUNCIÓN PARA CREAR LAS TABLAS
# --------------------------------------------

def crear_tablas():
    """Crea todas las tablas en la base de datos"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Tablas creadas exitosamente!")
        return True
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        return False

def obtener_session():
    """Retorna una nueva sesión de SQLAlchemy"""
    return Session()

# --------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------

def listar_tablas():
    """Lista todas las tablas del modelo"""
    tablas = []
    for tabla in Base.metadata.tables.keys():
        tablas.append(tabla)
    return sorted(tablas)

def contar_tablas():
    """Cuenta el número total de tablas"""
    return len(Base.metadata.tables)

if __name__ == '__main__':
    print("🔧 Iniciando creación de base de datos...")
    print(f"📊 Total de tablas a crear: {contar_tablas()}")
    print(f"🏷️  Tablas: {', '.join(listar_tablas())}")
    
    if crear_tablas():
        print("🎉 Base de datos lista para usar!")
    else:
        print("💥 Error en la configuración de la base de datos")