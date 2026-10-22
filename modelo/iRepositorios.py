from abc import abstractmethod, ABC
from typing import Union
from modelo.modelo import Factura

#Interfaz de persistencia de datos
class RepositorioFacturas(ABC):
    abstractmethod
    def guardar(self,factura:Factura)->None:
        pass
    @abstractmethod
    def obtener_por_id(self,id:str)->Union[Factura,None]:
        pass