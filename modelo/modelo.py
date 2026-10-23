from typing import List
from dataclasses import dataclass
from decimal import Decimal, DecimalException
import uuid

@dataclass
class DetalleFactura:
    descripcion:str
    cantidad:int
    precio_unitario:Decimal
    subtotal:Decimal=Decimal("0.00")

    #validaciones de atributos de la clase
    def __post_init__(self):
        if not isinstance(self.descripcion, str) or not self.descripcion.strip():
            raise ValueError("La descripción del producto o servicio es obligatoria.")
        if isinstance(self.cantidad, bool) or not isinstance(self.cantidad, int):
            raise ValueError("La cantidad debe ser un número entero.")
        if self.cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero.")
        if not isinstance(self.precio_unitario, Decimal) or not self.precio_unitario.is_finite():
            raise ValueError("El precio unitario debe ser un numero valido.")
        if self.precio_unitario <= Decimal("0.00"):
            raise ValueError("El precio unitario debe ser mayor a cero.")
        try:
            self.subtotal = (self.precio_unitario * Decimal(self.cantidad)).quantize(Decimal("0.01"))
        except DecimalException as error:
            raise ValueError("El subtotal de la linea esta fuera del rango permitido.") from error


@dataclass
class Factura:
    id: str
    cliente_id: str
    lineas: List[DetalleFactura]
    subtotal: Decimal
    impuesto: Decimal
    total: Decimal

    @staticmethod
    #funcion de crear la factura
    def crear(cliente_id:str, lineas:List[DetalleFactura], tasa:Decimal)->"Factura":
        #validaciones de los atributos
        if not isinstance(cliente_id, str) or not cliente_id.strip():
            raise ValueError("El identificador del cliente es obligatorio.")
        if not isinstance(lineas, list):
            raise ValueError("Las lineas de la factura deben enviarse en una lista.")
        if not lineas:
            raise ValueError("La factura debe tener al menos una línea de detalle.")
        if any(not isinstance(linea, DetalleFactura) for linea in lineas):
            raise ValueError("Todas las líneas deben ser detalles de factura válidos.")
        if not isinstance(tasa, Decimal) or not tasa.is_finite() or tasa < Decimal("0.00"):
            raise ValueError("La tasa fiscal debe ser un numero valido no negativo.")

        #logica de calculo de la factura
        try:
            subtotal = sum((linea.subtotal for linea in lineas), Decimal("0.00")).quantize(Decimal("0.01"))
            impuesto = (subtotal * tasa).quantize(Decimal("0.01"))
            total = (subtotal + impuesto).quantize(Decimal("0.01"))
        except DecimalException as error:
            raise ValueError("Los importes de la factura están fuera del rango permitido.") from error
        nuevo_id = f"FAC-{str(uuid.uuid4())[:8].upper()}" # generacion de id unico para la factura
        return Factura(id=nuevo_id,cliente_id=cliente_id,lineas=lineas,subtotal=subtotal,impuesto=impuesto,total=total
        )