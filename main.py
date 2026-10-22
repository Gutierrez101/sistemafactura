import json
import os
from aplicacion.casoUso.casoUsoCrearFactura import CrearFacturaCasoUso
from infraestructura.adaptadores import AdaptadorBroker, AdaptadorRest
from infraestructura.repositorios import seleccionar_repositorio
from modelo.modelo_reglas import ControlFraude, PoliticaFiscal

#construir el caso de uso
def construir_caso(proveedor:str="memoria")->CrearFacturaCasoUso:
    repositorio=seleccionar_repositorio(proveedor)
    control_fraude=ControlFraude()
    politica_fiscal=PoliticaFiscal()
    return CrearFacturaCasoUso(repositorio=repositorio, control_fraude=control_fraude, politica_fiscal=politica_fiscal)

def main():
    motor_configurado=os.getenv("REPOSITORIO","postgresql")
    print("=" * 70)
    print(f" SISTEMA DE FACTURACIÓN: {motor_configurado.upper()}")
    print("=" * 70)

    #se inyectan las dependencias
    caso_de_uso=construir_caso(motor_configurado)

    #conecatamos los adaptadores
    adaptador_rest=AdaptadorRest(caso_de_uso)
    adaptador_broker=AdaptadorBroker(caso_de_uso)

    #peticion http simulada
    peticion_http = {
        "cliente_id": "CLI-001",
        "lineas": [
            {"descripcion": "Teclado Mecánico", "cantidad": 2, "precio_unitario": "120.50"},
            {"descripcion": "Mouse Gamer", "cantidad": 1, "precio_unitario": "45.00"}
        ]
    }
    respuesta_rest=adaptador_rest.crear_factura_peticion(peticion_http)
    print("Respuesta REST:", json.dumps(respuesta_rest, ensure_ascii=False))

    #prueba de mensajeria
    mensaje_cola=json.dumps({
        "cliente_id": "CLI-002",
        "lineas": [
            {"descripcion": "Monitor 24 pulgadas", "cantidad": 1, "precio_unitario": "250.00"}
        ]
    })
    adaptador_broker.consumir_mensajes(mensaje_cola)

    #aplicacion de reglas de negocio (control de fraude)
    peticion_fraude={
        "cliente_id": "CLI-003",
        "lineas": [
            {"descripcion": "Servidor Empresarial", "cantidad": 2, "precio_unitario": "6000.00"}
        ]
    }
    respuesta_fraude=adaptador_rest.crear_factura_peticion(peticion_fraude)
    print("Respuesta REST (Fraude bloqueado):", json.dumps(respuesta_fraude, ensure_ascii=False))

main()   