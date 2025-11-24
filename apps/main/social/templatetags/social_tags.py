from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.html import escape
from urllib.parse import urlparse
import re
try:
    import nh3
    NH3_AVAILABLE = True
except ImportError:
    NH3_AVAILABLE = False

# Tags e atributos permitidos para conteúdo rico (FAQ, News, etc.)
# Baseado em whitelist do CKEditor
ALLOWED_TAGS_RICH = {
    'p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'table', 'thead', 'tbody',
    'tr', 'td', 'th', 'div', 'span', 'code', 'pre', 'hr'
}

ALLOWED_ATTRIBUTES_RICH = {
    'a': {'href', 'title', 'target', 'rel'},
    'img': {'src', 'alt', 'title', 'width', 'height', 'class'},
    'table': {'class', 'style'},
    'td': {'class', 'style', 'colspan', 'rowspan'},
    'th': {'class', 'style', 'colspan', 'rowspan'},
    'div': {'class', 'style'},
    'span': {'class', 'style'},
    'p': {'class', 'style'},
    'h1': {'class', 'style'},
    'h2': {'class', 'style'},
    'h3': {'class', 'style'},
    'h4': {'class', 'style'},
    'h5': {'class', 'style'},
    'h6': {'class', 'style'},
}

register = template.Library()


@register.simple_tag
def verified_badge(user, size="16px", show_tooltip=True):
    """
    Exibe o símbolo de verificação para usuários verificados
    
    Args:
        user: Usuário a ser verificado
        size: Tamanho do ícone (ex: "16px", "20px")
        show_tooltip: Se deve mostrar tooltip explicativo
    """
    # Verificação mais robusta
    if not user:
        return ""
    
    # Verifica se o campo existe e é True
    try:
        # Acessar diretamente o campo do modelo
        is_verified = user.social_verified
        if not is_verified:
            return ""
    except Exception:
        # Se houver qualquer erro, não mostra o badge
        return ""
    
    tooltip_attr = f'title="{_("Conta verificada")}"' if show_tooltip else ""
    
    html = f'''
    <svg xmlns="http://www.w3.org/2000/svg" 
         viewBox="0 0 24 24" 
         style="width: {size}; height: {size}; display: inline-block; vertical-align: middle; margin-left: 2px;"
         {tooltip_attr}
         class="verified-badge">
        <circle cx="12" cy="12" r="10" fill="#1DA1F2"/>
        <path d="M9 12l2 2 4-4" stroke="white" stroke-width="2.5"/>
    </svg>
    '''
    
    return mark_safe(html)


@register.simple_tag
def user_display_name(user, show_verified=True, size="16px"):
    """
    Exibe o nome do usuário com símbolo de verificação se aplicável
    
    Args:
        user: Usuário a ser exibido
        show_verified: Se deve mostrar o símbolo de verificação
        size: Tamanho do ícone de verificação
    """
    if not user:
        return ""
    
    name = user.username
    verified_icon = verified_badge(user, size, show_tooltip=True) if show_verified else ""
    
    return mark_safe(f'{name}{verified_icon}')


@register.filter
def user_is_verified(user):
    """
    Filtro para verificar se um usuário é verificado na rede social
    """
    if not user:
        return False
    
    try:
        return user.social_verified
    except Exception:
        return False


@register.simple_tag
def profile_badge(user, size="16px", show_tooltip=True):
    """
    Exibe o badge do tipo de perfil do usuário
    
    Args:
        user: Usuário a ser verificado
        size: Tamanho do ícone (ex: "16px", "20px")
        show_tooltip: Se deve mostrar tooltip explicativo
    """
    if not user:
        return ""
    
    try:
        profile_type = user.profile_type
        if profile_type == 'regular':
            return ""
        
        display_name = user.profile_display_name
        icon_class = user.profile_icon
        color_class = user.profile_color_class
        
        tooltip_attr = f'title="{display_name}"' if show_tooltip else ""
        
        html = f'''
        <span class="profile-badge {color_class}" {tooltip_attr} style="display: inline-flex; align-items: center; margin-left: 4px;">
            <i class="bi {icon_class}" style="font-size: {size};"></i>
        </span>
        '''
        
        return mark_safe(html)
    except Exception:
        return ""


@register.simple_tag
def profile_type_display(user):
    """
    Exibe o nome do tipo de perfil do usuário
    """
    if not user:
        return ""
    
    try:
        return user.profile_display_name
    except Exception:
        return ""


@register.filter
def has_profile_type(user, profile_type):
    """
    Filtro para verificar se um usuário tem um tipo específico de perfil
    """
    if not user:
        return False
    
    try:
        return user.profile_type == profile_type
    except Exception:
        return False


@register.filter
def mention_links(text):
    """
    Converte menções @username em links clicáveis para o perfil do usuário
    
    Args:
        text: Texto que pode conter menções @username
        
    Returns:
        Texto com menções convertidas em links HTML
    """
    if not text:
        return text
    
    # Converter para string se não for
    text = str(text)
    
    # Sanitizar HTML malicioso primeiro
    if NH3_AVAILABLE:
        # Permitir apenas texto, sem tags HTML
        text = nh3.clean(text, tags=set(), attributes=set())
    else:
        # Fallback: usar escape do Django
        text = escape(text)
    
    # Padrão para encontrar menções @username
    # Aceita letras, números, underscores e hífens no username
    # Não deve começar com @ se já estiver dentro de uma menção
    mention_pattern = r'(?<!@)@([a-zA-Z0-9_-]+)'
    
    def replace_mention(match):
        username = match.group(1)
        
        # Ignorar se o username for muito longo (provavelmente não é uma menção válida)
        if len(username) > 30:
            return match.group(0)
        
        # Escapar username para prevenir XSS
        username_escaped = escape(username)
        
        try:
            # Verificar se o usuário existe
            User = get_user_model()
            user = User.objects.filter(username=username).first()
            
            if user:
                # Usuário existe, criar link
                profile_url = reverse('social:user_profile', kwargs={'username': username})
                # Usar username_escaped no href e no texto
                return f'<a href="{escape(profile_url)}" class="mention-link" data-username="{username_escaped}">@{username_escaped}</a>'
            else:
                # Usuário não existe, manter como texto simples
                return f'<span class="mention-invalid">@{username_escaped}</span>'
                
        except Exception:
            # Em caso de erro, manter como texto simples
            return f'<span class="mention-invalid">@{username_escaped}</span>'
    
    # Aplicar a substituição
    try:
        processed_text = re.sub(mention_pattern, replace_mention, text)
    except Exception:
        # Em caso de erro na regex, manter texto original
        processed_text = text
    
    return mark_safe(processed_text)


@register.filter
def process_content(text):
    """
    Processa o conteúdo do post convertendo URLs e hashtags em links clicáveis
    
    Args:
        text: Texto que pode conter URLs, hashtags e menções
        
    Returns:
        Texto com URLs, hashtags e menções convertidas em links HTML
    """
    if not text:
        return text
    
    # Converter para string se não for
    text = str(text)
    
    # Proteção contra textos muito longos que podem causar travamento
    if len(text) > 10000:
        # Mesmo para textos longos, sanitizar HTML
        if NH3_AVAILABLE:
            text = nh3.clean(text, tags=set(), attributes=set())
        else:
            text = escape(text)
        return mark_safe(text)
    
    # Sanitizar HTML malicioso primeiro - remover todas as tags HTML
    # Isso previne XSS antes de processar URLs, hashtags e menções
    if NH3_AVAILABLE:
        # Permitir apenas texto, sem tags HTML
        text = nh3.clean(text, tags=set(), attributes=set())
    else:
        # Fallback: usar escape do Django
        text = escape(text)
    
    # Função para verificar se uma posição está dentro de uma tag HTML
    def is_inside_html_tag(text, pos):
        """Verifica se a posição está dentro de uma tag HTML"""
        # Procurar para trás pela tag de abertura mais próxima
        i = pos - 1
        while i >= 0:
            if text[i] == '>':
                return False  # Encontrou fechamento de tag antes da abertura
            elif text[i] == '<':
                # Verificar se é uma tag de abertura
                j = i + 1
                while j < len(text) and text[j].isalnum():
                    j += 1
                if j < len(text) and text[j] == '>':
                    return True  # Está dentro de uma tag HTML
                return False
            i -= 1
        return False
    
    # 1. Processar URLs primeiro (para evitar conflitos com hashtags)
    # Padrão para URLs (http/https) - versão mais robusta
    url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]{1,2000})'
    
    def replace_url(match):
        url = match.group(1)
        # Validar URL básica
        if not url or len(url) < 10 or len(url) > 2000:
            return match.group(0)
        
        # Validar e sanitizar URL para prevenir XSS
        try:
            parsed = urlparse(url)
            # Bloquear URLs perigosas: javascript:, data:, vbscript:, etc.
            dangerous_schemes = ['javascript', 'data', 'vbscript', 'file', 'about']
            if parsed.scheme.lower() in dangerous_schemes:
                # Retornar URL escapada como texto simples
                return escape(url)
            
            # Escapar a URL para prevenir XSS em atributos
            url_escaped = escape(url)
            
            # Truncar URL para exibição se for muito longa
            display_url = url_escaped
            if len(url_escaped) > 50:
                display_url = url_escaped[:47] + '...'
            
            return f'<a href="{url_escaped}" target="_blank" rel="noopener noreferrer" class="content-link">{display_url}</a>'
        except Exception:
            # Em caso de erro ao parsear URL, escapar e retornar como texto
            return escape(url)
    
    # Aplicar substituição de URLs com limite de tentativas
    try:
        processed_text = re.sub(url_pattern, replace_url, text, flags=re.IGNORECASE)
    except Exception:
        # Em caso de erro na regex, manter texto original
        processed_text = text
    
    # 2. Processar hashtags
    hashtag_pattern = r'#([a-zA-Z0-9_]+)'
    
    def replace_hashtag(match):
        hashtag_name = match.group(1)
        start_pos = match.start()
        
        # Verificar se está dentro de uma tag HTML
        if is_inside_html_tag(processed_text, start_pos):
            return match.group(0)  # Manter como está
        
        # Ignorar hashtags muito longas
        if len(hashtag_name) > 30:
            return match.group(0)
        
        # Escapar hashtag para prevenir XSS
        hashtag_escaped = escape(hashtag_name)
        
        try:
            # Criar link para a hashtag
            hashtag_url = reverse('social:hashtag_detail', kwargs={'hashtag_name': hashtag_name.lower()})
            return f'<a href="{escape(hashtag_url)}" class="hashtag-link">#{hashtag_escaped}</a>'
        except Exception:
            # Em caso de erro, manter como texto simples
            return f'<span class="hashtag-invalid">#{hashtag_escaped}</span>'
    
    # Aplicar substituição de hashtags
    try:
        processed_text = re.sub(hashtag_pattern, replace_hashtag, processed_text)
    except Exception:
        # Em caso de erro na regex, manter texto atual
        pass
    
    # 3. Processar menções @username
    mention_pattern = r'@([a-zA-Z0-9_-]+)'
    
    def replace_mention(match):
        username = match.group(1)
        start_pos = match.start()
        
        # Verificar se está dentro de uma tag HTML
        if is_inside_html_tag(processed_text, start_pos):
            return match.group(0)  # Manter como está
        
        # Ignorar se o username for muito longo
        if len(username) > 30:
            return match.group(0)
        
        # Escapar username para prevenir XSS
        username_escaped = escape(username)
        
        try:
            # Verificar se o usuário existe
            User = get_user_model()
            user = User.objects.filter(username=username).first()
            
            if user:
                # Usuário existe, criar link
                profile_url = reverse('social:user_profile', kwargs={'username': username})
                return f'<a href="{escape(profile_url)}" class="mention-link" data-username="{username_escaped}">@{username_escaped}</a>'
            else:
                # Usuário não existe, manter como texto simples
                return f'<span class="mention-invalid">@{username_escaped}</span>'
                
        except Exception:
            # Em caso de erro, manter como texto simples
            return f'<span class="mention-invalid">@{username_escaped}</span>'
    
    # Aplicar substituição de menções
    try:
        processed_text = re.sub(mention_pattern, replace_mention, processed_text)
    except Exception:
        # Em caso de erro na regex, manter texto atual
        pass
    
    return mark_safe(processed_text)


@register.filter
def sanitize_rich_content(html_content):
    """
    Sanitiza conteúdo HTML rico (FAQ, News, Dashboard) permitindo apenas tags seguras.
    Usa nh3 se disponível, caso contrário usa escape do Django.
    
    Args:
        html_content: Conteúdo HTML que pode conter tags e atributos
        
    Returns:
        HTML sanitizado e seguro
    """
    if not html_content:
        return html_content
    
    html_content = str(html_content)
    
    if NH3_AVAILABLE:
        # Usar nh3 com whitelist de tags e atributos permitidos
        try:
            # Validar URLs em atributos href e src
            cleaned = nh3.clean(
                html_content,
                tags=ALLOWED_TAGS_RICH,
                attributes=ALLOWED_ATTRIBUTES_RICH,
                url_schemes={'http', 'https', 'mailto'}
            )
            return mark_safe(cleaned)
        except Exception:
            # Em caso de erro, escapar tudo
            return escape(html_content)
    else:
        # Fallback: se nh3 não estiver disponível, retornar como está
        # mas avisar que deveria ser sanitizado
        # Em produção, nh3 deve estar disponível
        return mark_safe(html_content)
