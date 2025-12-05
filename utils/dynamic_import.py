import importlib
import os
from dotenv import load_dotenv

load_dotenv()

def get_query_class(class_name: str, env_var: str = "LINEAGE_QUERY_MODULE", default_module: str = "default"):
    """
    Importa dinamicamente uma classe de um módulo baseado em variável de ambiente.
    
    Se o módulo configurado não existir, tenta usar query_default como fallback.

    :param class_name: Nome da classe a ser importada (ex: "LineageStats")
    :param env_var: Nome da variável de ambiente (default: LINEAGE_QUERY_MODULE)
    :param default_module: Módulo fallback se não encontrar o configurado (default: "default")
    :return: Classe importada
    """
    module_suffix = os.getenv(env_var, default_module)
    module_path = f"apps.lineage.server.querys.query_{module_suffix}"

    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls
    except ModuleNotFoundError as e:
        # Se não encontrou o módulo configurado, tentar query_default
        if module_suffix != 'default':
            print(f"AVISO: Modulo query_{module_suffix} nao encontrado, usando query_default")
            fallback_path = f"apps.lineage.server.querys.query_default"
            try:
                mod = importlib.import_module(fallback_path)
                cls = getattr(mod, class_name)
                return cls
            except (ModuleNotFoundError, AttributeError) as fallback_error:
                raise ImportError(f"Não foi possível importar {class_name} de {module_path} nem de {fallback_path}: {fallback_error}")
        else:
            raise ImportError(f"Não foi possível importar {class_name} de {module_path}: {e}")
    except AttributeError as e:
        raise ImportError(f"Classe {class_name} não encontrada em {module_path}: {e}")
