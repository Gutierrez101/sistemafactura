import json
from aplicacion.crearFactura import CrearFactura


class AdaptadorRest:
    def __init__(self, caso_uso:CrearFactura):
        self._caso_uso=caso_uso

    #Simulacion de peticion HTTP POST /facturas
    def crear_factura_peticion(self, peticion_http:dict)->dict:
        print("\nPetición HTTP POST /facturas recibida (Síncrona)")
        try:
            if not isinstance(peticion_http, dict):
                raise ValueError("El cuerpo de la petición debe ser un objeto JSON.")

            solicitud={
                "cliente_id": peticion_http.get("cliente_id"),
                "lineas": peticion_http.get("lineas", [])
            }

            resultado=self._caso_uso.ejecutar(solicitud)
            return {"status": 201, "data": resultado}
        except ValueError as error:
            return {"status": 422, "error": str(error)}


class AdaptadorBroker:
    def __init__(self, caso_uso:CrearFactura):
        self._caso_uso=caso_uso

    #Simulacion de consumo de mensajes
    def consumir_mensajes(self, mensaje:str)->dict:
        print("\nMensaje recibido desde cola RabbitMQ (Asíncrono)")
        try:
            if not isinstance(mensaje, str):
                raise ValueError("El mensaje debe ser texto JSON.")

            evento=json.loads(mensaje)
            if not isinstance(evento, dict):
                raise ValueError("El mensaje debe contener un objeto JSON.")

            solicitud = {
                "cliente_id": evento.get("cliente_id"),
                "lineas": evento.get("lineas", [])
            }

            resultado=self._caso_uso.ejecutar(solicitud)
            print(f"ACK enviado. Factura procesada: {resultado['id']}")
            return {"ack": True, "data": resultado}
        except ValueError as error:
            print(f"NACK enviado. Rechazado por negocio: {error}")
            return {"ack": False, "error": str(error)}