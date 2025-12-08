from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from apps.main.social.models import ContentFilter


class Command(BaseCommand):
    help = 'Configura filtros de moderação menos restritivos e mais precisos'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Configurando filtros de moderação menos restritivos...')
        )

        # ============================================================================
        # FILTROS DE SPAM E MARKETING - APENAS PADRÕES CLAROS DE SPAM
        # ============================================================================
        spam_filters = [
            {
                'name': 'Spam - Ofertas Comerciais Múltiplas',
                'filter_type': 'regex',
                'pattern': r'\b(ganhe|ganhar|dinheiro\s*fácil|renda\s*extra|trabalhe\s*em\s*casa|oportunidade\s*única)\b.*\b(clique|click|agora|urgente|grátis|free)\b',
                'action': 'flag',
                'description': 'Detecta apenas combinações claras de spam comercial (múltiplas palavras-chave juntas)',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            },
            {
                'name': 'Spam - Medicamentos Prescritos (Apenas URLs)',
                'filter_type': 'regex',
                'pattern': r'http[s]?://[^\s]*(viagra|cialis|levitra|pharmacy|prescription)[^\s]*',
                'action': 'auto_hide',
                'description': 'Detecta apenas links para medicamentos prescritos (não palavras isoladas)',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            },
            {
                'name': 'Spam - Esquemas Financeiros Explícitos',
                'filter_type': 'regex',
                'pattern': r'\b(pyramid\s*scheme|ponzi\s*scheme|get\s*rich\s*quick|passive\s*income\s*guaranteed)\b',
                'action': 'flag',
                'description': 'Detecta apenas esquemas financeiros explícitos',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            }
        ]

        # ============================================================================
        # FILTROS DE LINGUAGEM INADEQUADA - APENAS OFENSAS GRAVES
        # ============================================================================
        profanity_filters = [
            {
                'name': 'Palavrões - Português (Severo e Ofensivo)',
                'filter_type': 'regex',
                'pattern': r'\b(viado\s*nojento|gay\s*de\s*merda|filho\s*da\s*puta|fdp|arrombado|cuzão)\b',
                'action': 'auto_hide',
                'description': 'Detecta apenas palavrões ofensivos e discriminatórios graves',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': True
            },
            {
                'name': 'Palavrões com Símbolos (Tentativa de Bypass)',
                'filter_type': 'regex',
                'pattern': r'\b(p\*rra|m\*rda|c\*ralho|f\*ck|sh\*t|b\*tch|a\*shole)\b',
                'action': 'flag',
                'description': 'Detecta palavrões com asteriscos (tentativa de burlar filtros)',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': True
            }
        ]

        # ============================================================================
        # FILTROS CONTRA PORNOGRAFIA - APENAS LINKS E CONTEÚDO EXPLÍCITO
        # ============================================================================
        adult_content_filters = [
            {
                'name': 'Sites Pornográficos (Apenas URLs)',
                'filter_type': 'regex',
                'pattern': r'http[s]?://[^\s]*(pornhub|xvideos|redtube|youporn|xhamster|xnxx|brazzers)[^\s]*',
                'action': 'auto_delete',
                'description': 'Detecta apenas links diretos para sites pornográficos conhecidos',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            },
            {
                'name': 'Conteúdo Pornográfico Explícito (Múltiplas Palavras)',
                'filter_type': 'regex',
                'pattern': r'\b(porn|porno|pornografia)\b.*\b(grátis|free|download|assistir|ver)\b',
                'action': 'auto_hide',
                'description': 'Detecta apenas combinações explícitas de conteúdo pornográfico com ações',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            }
        ]

        # ============================================================================
        # FILTROS DE URLS SUSPEITAS - APENAS PADRÕES CLAROS
        # ============================================================================
        suspicious_urls_filters = [
            {
                'name': 'Múltiplas URLs (Spam - 4 ou mais)',
                'filter_type': 'regex',
                'pattern': r'(http[s]?://[^\s]+.*){4,}',
                'action': 'flag',
                'description': 'Detecta posts com 4 ou mais URLs (spam claro)',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            },
            {
                'name': 'Domínios Suspeitos de Phishing',
                'filter_type': 'regex',
                'pattern': r'(\.tk|\.ml|\.ga|\.cf|tempmail|guerrillamail|10minutemail)',
                'action': 'auto_hide',
                'description': 'Detecta domínios suspeitos frequentemente usados para phishing',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            }
        ]

        # ============================================================================
        # FILTROS CONTRA DISCRIMINAÇÃO - APENAS OFENSAS GRAVES
        # ============================================================================
        hate_speech_filters = [
            {
                'name': 'Discurso de Ódio Racial Grave',
                'filter_type': 'regex',
                'pattern': r'\b(nigger|negro\s*de\s*merda|macaco|preto\s*fedorento)\b',
                'action': 'auto_delete',
                'description': 'Detecta linguagem racista grave e discriminatória',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': True
            },
            {
                'name': 'Discurso de Ódio Homofóbico Grave',
                'filter_type': 'regex',
                'pattern': r'\b(viado\s*nojento|gay\s*de\s*merda|sapatão|traveco)\b',
                'action': 'auto_delete',
                'description': 'Detecta linguagem homofóbica e transfóbica grave',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': True
            }
        ]

        # ============================================================================
        # FILTROS DE COMPORTAMENTO - APENAS PADRÕES CLAROS DE SPAM
        # ============================================================================
        behavior_filters = [
            {
                'name': 'Conteúdo Repetitivo Extremo (Spam)',
                'filter_type': 'regex',
                'pattern': r'(.{15,})\1{4,}',
                'action': 'flag',
                'description': 'Detecta apenas conteúdo extremamente repetitivo (5+ repetições)',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            },
            {
                'name': 'CAPS Excessivo (30+ caracteres)',
                'filter_type': 'regex',
                'pattern': r'[A-Z]{30,}',
                'action': 'flag',
                'description': 'Detecta apenas texto em maiúsculas muito excessivo (30+ caracteres)',
                'case_sensitive': True,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            }
        ]

        # ============================================================================
        # FILTROS ESPECÍFICOS PARA BRASIL - APENAS GOLPES CLAROS
        # ============================================================================
        brazil_specific_filters = [
            {
                'name': 'Golpes Brasileiros - PIX (Padrões Explícitos)',
                'filter_type': 'regex',
                'pattern': r'\b(pix\s*gratis|pix\s*grátis|ganhe\s*pix|dinheiro\s*no\s*pix|cpf\s*liberado|fgts\s*saque\s*agora)\b',
                'action': 'flag',
                'description': 'Detecta apenas padrões explícitos de golpes relacionados a PIX',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            },
            {
                'name': 'Sites de Apostas (Apenas com Links)',
                'filter_type': 'regex',
                'pattern': r'http[s]?://[^\s]*(blaze|crash|mines|aviator|fortune\s*tiger)[^\s]*',
                'action': 'flag',
                'description': 'Detecta apenas links para sites de apostas (não menções)',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False
            }
        ]

        # Combinar todos os filtros
        all_filters = (spam_filters + profanity_filters + adult_content_filters + 
                      suspicious_urls_filters + hate_speech_filters + 
                      behavior_filters + brazil_specific_filters)

        created_count = 0
        updated_count = 0

        for filter_data in all_filters:
            filter_obj, created = ContentFilter.objects.get_or_create(
                name=filter_data['name'],
                defaults=filter_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Criado filtro: {filter_data["name"]}')
                )
            else:
                # Atualizar filtro existente
                for key, value in filter_data.items():
                    setattr(filter_obj, key, value)
                filter_obj.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Atualizado filtro: {filter_data["name"]}')
                )

        # Desativar o filtro de padrão de spam automático (muito restritivo)
        spam_pattern_filter, created = ContentFilter.objects.get_or_create(
            name='Padrão de Spam Automático',
            defaults={
                'filter_type': 'spam_pattern',
                'pattern': 'auto',
                'action': 'flag',
                'description': 'Detecta automaticamente padrões comuns de spam usando algoritmos internos - DESATIVADO por padrão',
                'case_sensitive': False,
                'apply_to_posts': True,
                'apply_to_comments': True,
                'apply_to_usernames': False,
                'is_active': False  # DESATIVADO por padrão
            }
        )
        
        if not created:
            # Se já existe, desativar
            spam_pattern_filter.is_active = False
            spam_pattern_filter.save()
            updated_count += 1
            self.stdout.write(
                self.style.WARNING('↻ Filtro de spam automático foi DESATIVADO (muito restritivo)')
            )
        else:
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS('✓ Criado filtro de padrão de spam automático (DESATIVADO)')
            )

        # Mensagem final com estatísticas
        total_active = ContentFilter.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}\n'
                f'🛡️  SISTEMA DE MODERAÇÃO MENOS RESTRITIVO!\n'
                f'{"="*60}\n'
                f'📊 Estatísticas:\n'
                f'   • Filtros criados: {created_count}\n'
                f'   • Filtros atualizados: {updated_count}\n'
                f'   • Total de filtros ativos: {total_active}\n\n'
                f'🎯 Categorias otimizadas:\n'
                f'   • Spam e Marketing (3 filtros - apenas padrões claros)\n'
                f'   • Palavrões (2 filtros - apenas ofensas graves)\n'
                f'   • Conteúdo Pornográfico (2 filtros - apenas links e combinações explícitas)\n'
                f'   • URLs Suspeitas (2 filtros - apenas padrões claros)\n'
                f'   • Discurso de Ódio (2 filtros - apenas ofensas graves)\n'
                f'   • Comportamentos Suspeitos (2 filtros - apenas extremos)\n'
                f'   • Golpes Brasileiros (2 filtros - apenas padrões explícitos)\n\n'
                f'✨ Melhorias implementadas:\n'
                f'   • Filtros muito menos restritivos\n'
                f'   • Foco apenas em padrões claros de spam/abuso\n'
                f'   • Remoção de bloqueios de palavras isoladas\n'
                f'   • Exigência de combinações de palavras para spam\n'
                f'   • Filtro automático de spam DESATIVADO por padrão\n'
                f'   • Redução significativa de falsos positivos\n\n'
                f'🔧 Próximos passos:\n'
                f'   1. Monitore a eficácia dos filtros\n'
                f'   2. Ajuste ações conforme necessário\n'
                f'   3. Ative filtros adicionais apenas se necessário\n\n'
                f'📋 Acesse: /social/moderation/filters/ para gerenciar\n'
                f'{"="*60}'
            )
        )
