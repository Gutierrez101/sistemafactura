from abc import abstractmethod

#entrada de la aplicacion (interfaz)
class CrearFactura:
    @abstractmethod
    def ejecutar(self,solicitud:dict)->dict:
        pass