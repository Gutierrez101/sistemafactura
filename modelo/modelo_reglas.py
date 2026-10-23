from decimal import Decimal

class ControlFraude:
    def __init__(self, limite:Decimal=Decimal("10000.00")):
        self._limite=limite
        self._clientes_bloqueados={"CLI-FRAUDE","CLI-BLOQUEADO"}

    def validar(self, cliente_id:str, subtotal: Decimal)->None:
        if cliente_id in self._clientes_bloqueados:
            raise ValueError(f"Fraude detectado: el cliente '{cliente_id}'")
        if subtotal > self._limite:
            raise ValueError(f"Fraude detectado: el subtotal (${subtotal}) supera el límite permitido (${self._limite}).")


class PoliticaFiscal:
    def __init__(self,tasa_defecto:Decimal=Decimal("0.15")):
        self._tasa_defecto=tasa_defecto

    def aplicar_tasa(self,cliente_id:str)->Decimal:
        #Si es exportador aplica el 0%, caso contrario el 15%
        if cliente_id.startswith("EXP-"):
            return Decimal("0.00")
        return self._tasa_defecto