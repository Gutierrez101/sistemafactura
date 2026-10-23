from decimal import Decimal
import json
import unittest

from aplicacion.casoUso.casoUsoCrearFactura import CrearFacturaCasoUso
from infraestructura.adaptadores import AdaptadorBroker, AdaptadorRest
from infraestructura.repositorios import RepositorioEnMemoria, RepositorioOracle, RepositorioPostgreSQL, seleccionar_repositorio
from modelo.modelo_reglas import ControlFraude, PoliticaFiscal


class TestFacturacion(unittest.TestCase):
    
    def setUp(self):
        self.repositorio=RepositorioEnMemoria()
        self.caso_uso=CrearFacturaCasoUso(
            repositorio=self.repositorio,
            control_fraude=ControlFraude(limite=Decimal("10000.00")),
            politica_fiscal=PoliticaFiscal(tasa_defecto=Decimal("0.15"))
        )

    def test_crear_factura(self):
        solicitud={
            "cliente_id": "CLI-001",
            "lineas": [
                {"descripcion": "Servicio de soporte", "cantidad": 2, "precio_unitario": "100.00"}
            ]
        }
        resultado = self.caso_uso.ejecutar(solicitud)
        self.assertEqual(resultado["subtotal"], "200.00")
        self.assertEqual(resultado["impuesto"], "30.00")
        self.assertEqual(resultado["total"], "230.00")
        self.assertIsNotNone(self.repositorio.obtener_por_id(resultado["id"]))

    def test_control_fraude_monto_excesivo(self):
        solicitud={
            "cliente_id": "CLI-001",
            "lineas": [
                {"descripcion": "Equipo costoso", "cantidad": 2, "precio_unitario": "6000.00"}
            ]
        }
        with self.assertRaises(ValueError):
            self.caso_uso.ejecutar(solicitud)

    def test_control_fraude_cliente_bloqueado(self):
        with self.assertRaisesRegex(ValueError, "Fraude detectado"):
            self.caso_uso.ejecutar({
                "cliente_id": "CLI-BLOQUEADO",
                "lineas": [
                    {"descripcion": "Servicio", "cantidad": 1, "precio_unitario": "10.00"}
                ]
            })

    def test_cliente_de_exportacion_no_paga_impuesto(self):
        resultado = self.caso_uso.ejecutar({
            "cliente_id": "EXP-001",
            "lineas": [
                {"descripcion": "Servicio", "cantidad": 1, "precio_unitario": "100.00"}
            ]
        })
        self.assertEqual(resultado["subtotal"], "100.00")
        self.assertEqual(resultado["impuesto"], "0.00")
        self.assertEqual(resultado["total"], "100.00")

    def test_rest_rechaza_solicitudes_invalidas_sin_guardar(self):
        rest=AdaptadorRest(self.caso_uso)
        solicitudes_invalidas = [
            None,
            [],
            {"lineas": [
                {"descripcion": "Servicio", "cantidad": 1, "precio_unitario": "10.00"}
            ]},
            {"cliente_id": "CLI-001", "lineas": [
                {"descripcion": "Servicio", "cantidad": 1}
            ]},
            {"cliente_id": "CLI-001", "lineas": [
                {"descripcion": "Servicio", "cantidad": 1, "precio_unitario": "no-numérico"}
            ]},
            {"cliente_id": "CLI-001", "lineas": [
                {"descripcion": "Servicio", "cantidad": 1.5, "precio_unitario": "10.00"}
            ]},
        ]

        for solicitud in solicitudes_invalidas:
            with self.subTest(solicitud=solicitud):
                respuesta=rest.crear_factura_peticion(solicitud)
                self.assertEqual(respuesta["status"], 422)
                self.assertIn("error", respuesta)

    def test_broker_rechaza_json_invalido_y_objetos_inesperados(self):
        broker=AdaptadorBroker(self.caso_uso)
        for mensaje in ("{", "[]", "null", None):
            with self.subTest(mensaje=mensaje):
                respuesta = broker.consumir_mensajes(mensaje)
                self.assertFalse(respuesta["ack"])
                self.assertIn("error", respuesta)

    def test_simetria_adaptadores_rest_y_broker(self):
        rest=AdaptadorRest(self.caso_uso)
        broker=AdaptadorBroker(self.caso_uso)

        datos={
            "cliente_id": "CLI-100",
            "lineas": [{"descripcion": "Licencia Software", "cantidad": 1, "precio_unitario": "100.00"}]
        }

        resp_rest=rest.crear_factura_peticion(datos)
        resp_broker=broker.consumir_mensajes(json.dumps(datos))

        self.assertEqual(resp_rest["status"], 201)
        self.assertTrue(resp_broker["ack"])
        self.assertEqual(resp_rest["data"]["total"], resp_broker["data"]["total"])

    def test_intercambio_postgresql_y_oracle_sin_tocar_dominio(self):
        for repo in [RepositorioPostgreSQL(), RepositorioOracle()]:
            caso = CrearFacturaCasoUso(repo, ControlFraude(), PoliticaFiscal())
            res = caso.ejecutar({
                "cliente_id": "CLI-200",
                "lineas": [{"descripcion": "Consultoría", "cantidad": 1, "precio_unitario": "50.00"}]
            })
            self.assertEqual(res["total"], "57.50")
            self.assertIsNotNone(repo.obtener_por_id(res["id"]))
    
    def test_selector_de_repositorio_configura_la_infraestructura(self):
        self.assertIsInstance(seleccionar_repositorio("memoria"), RepositorioEnMemoria)
        self.assertIsInstance(seleccionar_repositorio("PostgreSQL"), RepositorioPostgreSQL)
        self.assertIsInstance(seleccionar_repositorio("oracle"), RepositorioOracle)
        with self.assertRaisesRegex(ValueError, "no soportado"):
            seleccionar_repositorio("mysql")

if __name__ == "__main__":
    unittest.main()
    
