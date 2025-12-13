from django import template
from urllib.parse import urlencode

register = template.Library()


@register.filter
def build_query_string(query_params):
    """
    Constrói uma string de query a partir de um dicionário ou string de query params.
    Remove o parâmetro 'page' se existir, pois será adicionado separadamente.
    """
    if not query_params:
        return ''
    
    # Se for string, converte para dict
    if isinstance(query_params, str):
        from urllib.parse import parse_qs, urlencode
        params = parse_qs(query_params)
        # Remove 'page' se existir
        if 'page' in params:
            del params['page']
        # Converte de volta para string
        if params:
            # Flatten os valores (parse_qs retorna listas)
            flat_params = {}
            for key, value_list in params.items():
                if value_list:
                    flat_params[key] = value_list[0] if len(value_list) == 1 else value_list
            return urlencode(flat_params, doseq=True)
        return ''
    
    # Se for dict, remove 'page' e retorna string
    if isinstance(query_params, dict):
        filtered_params = {k: v for k, v in query_params.items() if k != 'page'}
        if filtered_params:
            return urlencode(filtered_params, doseq=True)
        return ''
    
    return ''
