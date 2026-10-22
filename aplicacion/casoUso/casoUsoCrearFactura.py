from decimal import Decimal, InvalidOperation

from aplicacion.crearFactura import CrearFactura
from modelo.iRepositorios import RepositorioFacturas
from modelo.modelo import DetalleFactura, Factura
from modelo.modelo_reglas import ControlFraude, PoliticaFiscal


class CrearFacturaCasoUso(CrearFactura):
    def __init__(self, repositorio: RepositorioFacturas, control_fraude: ControlFraude, politica_fiscal: PoliticaFiscal):
        self._repositorio=repositorio
        self._control_fraude=control_fraude
        self._politica_fiscal=politica_fiscal

    def ejecutar(self, solicitud: dict)->dict:
        if not isinstance(solicitud,dict):
            raise ValueError("La solicitud debe estar creada")
        cliente_id = solicitud.get("cliente_id")
        if not isinstance(cliente_id, str) or not cliente_id.strip():
            raise ValueError("El identificador del cliente es obligatorio.")

        lineas_datos = solicitud.get("lineas", [])
        if not isinstance(lineas_datos, list):
            raise ValueError("Las líneas de la factura deben enviarse en una lista.")

        lineas = []
        for indice, item in enumerate(lineas_datos, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"La línea {indice} debe ser un objeto.")

            campos_requeridos = ("descripcion", "cantidad", "precio_unitario")
            campos_faltantes = [campo for campo in campos_requeridos if campo not in item]
            if campos_faltantes:
                raise ValueError(
                    f"Faltan campos en la línea {indice}: {', '.join(campos_faltantes)}."
                )

            descripcion = item["descripcion"]
            if not isinstance(descripcion, str):
                raise ValueError(f"La descripción de la línea {indice} debe ser texto.")

            cantidad_dato = item["cantidad"]
            if isinstance(cantidad_dato, bool) or not isinstance(cantidad_dato, (int, str)):
                raise ValueError(f"La cantidad de la línea {indice} debe ser un entero.")
            try:
                cantidad = int(cantidad_dato)
            except ValueError as error:
                raise ValueError(
                    f"La cantidad de la línea {indice} debe ser un entero."
                ) from error

            precio_dato = item["precio_unitario"]
            if isinstance(precio_dato, bool) or not isinstance(
                precio_dato, (str, int, float, Decimal)
            ):
                raise ValueError(f"El precio de la línea {indice} debe ser numérico.")
            try:
                precio_unitario = Decimal(str(precio_dato))
            except InvalidOperation as error:
                raise ValueError(
                    f"El precio de la línea {indice} debe ser numérico."
                ) from error

            lineas.append(
                DetalleFactura(descripcion=descripcion, cantidad=cantidad, precio_unitario=precio_unitario)
            )

        #calculo de sobtotal y aplicar reglas de negocio
        subtotal_preliminar = sum((linea.subtotal for linea in lineas), Decimal("0.00"))
        self._control_fraude.validar(cliente_id, subtotal_preliminar)
        tasa=self._politica_fiscal.aplicar_tasa(cliente_id)

        #instanciar la factura usando su metodo
        factura = Factura.crear(cliente_id, lineas, tasa)

        #usar la interfaz de persistencia para guardar la informacion
        self._repositorio.guardar(factura)

        return {
            "id": factura.id,
            "cliente_id": factura.cliente_id,
            "subtotal": str(factura.subtotal),
            "impuesto": str(factura.impuesto),
            "total": str(factura.total)
        }

    