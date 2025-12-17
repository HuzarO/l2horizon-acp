"""
Comando para popular o banco de dados com FAQs sobre o PDL (Painel Definitivo Lineage).
Este comando cria FAQs formatadas que ensinam a usar o sistema PDL.
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from apps.main.faq.models import FAQ, FAQTranslation


class Command(BaseCommand):
    help = 'Popula o banco de dados com FAQs sobre o PDL (Painel Definitivo Lineage)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Remove todas as FAQs existentes antes de criar novas',
        )
        parser.add_argument(
            '--language',
            choices=['pt', 'en', 'es', 'all'],
            default='pt',
            help='Idioma das FAQs a criar (padrão: pt)',
        )

    def handle(self, *args, **options):
        clear_existing = options['clear']
        language = options['language']

        if clear_existing:
            self.stdout.write(self.style.WARNING('🗑️  Removendo FAQs existentes...'))
            FAQ.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ FAQs removidas com sucesso!'))

        self.stdout.write(self.style.SUCCESS('📚 Criando FAQs sobre o PDL...'))

        # Lista de FAQs sobre o PDL
        faqs_data = self.get_faqs_data()

        created_count = 0
        updated_count = 0

        for order, faq_data in enumerate(faqs_data, start=1):
            # Cria ou atualiza a FAQ
            faq, created = FAQ.objects.get_or_create(
                order=order,
                defaults={
                    'is_public': faq_data.get('is_public', True),
                    'show_in_internal': faq_data.get('show_in_internal', True),
                }
            )

            if not created:
                # Atualiza campos se necessário
                faq.is_public = faq_data.get('is_public', True)
                faq.show_in_internal = faq_data.get('show_in_internal', True)
                faq.save()

            # Cria ou atualiza as traduções
            languages_to_create = ['pt', 'en', 'es'] if language == 'all' else [language]
            
            for lang in languages_to_create:
                if lang in faq_data.get('translations', {}):
                    translation_data = faq_data['translations'][lang]
                    
                    translation, trans_created = FAQTranslation.objects.get_or_create(
                        faq=faq,
                        language=lang,
                        defaults={
                            'question': translation_data['question'],
                            'answer': translation_data['answer'],
                        }
                    )

                    if not trans_created:
                        # Atualiza se necessário
                        translation.question = translation_data['question']
                        translation.answer = translation_data['answer']
                        translation.save()

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Criada: {faq_data["translations"].get("pt", {}).get("question", "FAQ")}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Atualizada: {faq_data["translations"].get("pt", {}).get("question", "FAQ")}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Concluído! {created_count} FAQs criadas, {updated_count} atualizadas.'
            )
        )

    def get_faqs_data(self):
        """Retorna a lista de FAQs formatadas sobre o PDL"""
        return [
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'O que é o PDL (Painel Definitivo Lineage)?',
                        'answer': '''
                        <h3>O que é o PDL?</h3>
                        <p>O <strong>PDL (Painel Definitivo Lineage)</strong> é um painel completo para jogadores de servidores privados de Lineage 2. Ele oferece diversas funcionalidades para melhorar sua experiência de jogo.</p>
                        
                        <h4>O que você pode fazer no PDL:</h4>
                        <ul>
                            <li><strong>Loja Virtual:</strong> Compre itens e pacotes diretamente do painel, com entrega automática para seus personagens</li>
                            <li><strong>Carteira Digital:</strong> Gerencie seu saldo, faça transferências para outros jogadores e para seus personagens no jogo</li>
                            <li><strong>Leilões:</strong> Participe de leilões e compre itens de outros jogadores</li>
                            <li><strong>Marketplace:</strong> Compre e venda personagens diretamente com outros jogadores</li>
                            <li><strong>Minigames:</strong> Divirta-se com roleta, caixas, dados, pesca e muito mais</li>
                            <li><strong>Perfil e Conquistas:</strong> Personalize seu perfil e ganhe conquistas enquanto joga</li>
                        </ul>
                        
                        <h4>Interface Moderna e Segura:</h4>
                        <ul>
                            <li>Design responsivo que funciona perfeitamente em desktop, tablet e mobile</li>
                            <li>Sistema de segurança com autenticação em duas etapas (2FA)</li>
                            <li>Histórico completo de todas as suas transações</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What is PDL (Definitive Lineage Panel)?',
                        'answer': '''
                        <h3>What is PDL?</h3>
                        <p>The <strong>PDL (Definitive Lineage Panel)</strong> is a complete panel for players of private Lineage 2 servers. It offers various features to enhance your gaming experience.</p>
                        
                        <h4>What you can do in PDL:</h4>
                        <ul>
                            <li><strong>Virtual Store:</strong> Buy items and packages directly from the panel, with automatic delivery to your characters</li>
                            <li><strong>Digital Wallet:</strong> Manage your balance, make transfers to other players and to your in-game characters</li>
                            <li><strong>Auctions:</strong> Participate in auctions and buy items from other players</li>
                            <li><strong>Marketplace:</strong> Buy and sell characters directly with other players</li>
                            <li><strong>Minigames:</strong> Have fun with roulette, boxes, dice, fishing and much more</li>
                            <li><strong>Profile and Achievements:</strong> Customize your profile and earn achievements while playing</li>
                        </ul>
                        
                        <h4>Modern and Secure Interface:</h4>
                        <ul>
                            <li>Responsive design that works perfectly on desktop, tablet and mobile</li>
                            <li>Security system with two-factor authentication (2FA)</li>
                            <li>Complete history of all your transactions</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Qué es el PDL (Panel Definitivo de Lineage)?',
                        'answer': '''
                        <h3>¿Qué es el PDL?</h3>
                        <p>El <strong>PDL (Panel Definitivo de Lineage)</strong> es un panel completo para jugadores de servidores privados de Lineage 2. Ofrece diversas funcionalidades para mejorar tu experiencia de juego.</p>
                        
                        <h4>Lo que puedes hacer en el PDL:</h4>
                        <ul>
                            <li><strong>Tienda Virtual:</strong> Compra ítems y paquetes directamente desde el panel, con entrega automática a tus personajes</li>
                            <li><strong>Billetera Digital:</strong> Gestiona tu saldo, realiza transferencias a otros jugadores y a tus personajes en el juego</li>
                            <li><strong>Subastas:</strong> Participa en subastas y compra ítems de otros jugadores</li>
                            <li><strong>Marketplace:</strong> Compra y vende personajes directamente con otros jugadores</li>
                            <li><strong>Minijuegos:</strong> Diviértete con ruleta, cajas, dados, pesca y mucho más</li>
                            <li><strong>Perfil y Logros:</strong> Personaliza tu perfil y gana logros mientras juegas</li>
                        </ul>
                        
                        <h4>Interfaz Moderna y Segura:</h4>
                        <ul>
                            <li>Diseño responsivo que funciona perfectamente en escritorio, tablet y móvil</li>
                            <li>Sistema de seguridad con autenticación en dos pasos (2FA)</li>
                            <li>Historial completo de todas tus transacciones</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Quais são as principais funcionalidades do PDL?',
                        'answer': '''
                        <h3>Funcionalidades Principais do PDL</h3>
                        
                        <h4>🎮 Sistema de Conta e Perfil</h4>
                        <ul>
                            <li>Cadastro seguro com autenticação em duas etapas (2FA)</li>
                            <li>Perfil personalizável com foto e informações</li>
                            <li>Sistema de conquistas e XP</li>
                            <li>Histórico completo de atividades</li>
                        </ul>
                        
                        <h4>💰 Carteira Digital (Wallet)</h4>
                        <ul>
                            <li>Saldo em tempo real atualizado instantaneamente</li>
                            <li>Histórico completo de todas as transações</li>
                            <li>Transferências entre jogadores</li>
                            <li>Transferências para personagens no jogo</li>
                            <li>Limites de segurança configuráveis</li>
                        </ul>
                        
                        <h4>🛒 Loja Virtual</h4>
                        <ul>
                            <li>Catálogo completo de itens e pacotes</li>
                            <li>Carrinho de compras intuitivo</li>
                            <li>Promoções e ofertas especiais</li>
                            <li>Entrega automática de itens para seus personagens</li>
                            <li>Histórico de compras</li>
                        </ul>
                        
                        <h4>💳 Sistema de Pagamentos</h4>
                        <ul>
                            <li>Múltiplos métodos de pagamento: Mercado Pago, Stripe e PayPal</li>
                            <li>Pagamentos seguros e criptografados</li>
                            <li>Confirmação automática de pagamentos</li>
                            <li>Recibo digital de todas as transações</li>
                        </ul>
                        
                        <h4>🔨 Leilões</h4>
                        <ul>
                            <li>Sistema completo de leilões entre jogadores</li>
                            <li>Lance em itens raros e exclusivos</li>
                            <li>Acompanhe leilões em tempo real</li>
                            <li>Notificações de lances e encerramento</li>
                        </ul>
                        
                        <h4>🏪 Marketplace</h4>
                        <ul>
                            <li>Compra e venda de personagens diretamente com outros jogadores</li>
                            <li>Negociação segura entre jogadores</li>
                            <li>Sistema de avaliações e reputação</li>
                        </ul>
                        
                        <h4>🎲 Minigames</h4>
                        <ul>
                            <li>Roleta com prêmios variados</li>
                            <li>Caixas misteriosas</li>
                            <li>Dados e jogos de azar</li>
                            <li>Pesca com recompensas</li>
                            <li>E muito mais diversão!</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What are the main features of PDL?',
                        'answer': '''
                        <h3>Main PDL Features</h3>
                        
                        <h4>🎮 Account and Profile System</h4>
                        <ul>
                            <li>Secure registration with two-factor authentication (2FA)</li>
                            <li>Customizable profile with photo and information</li>
                            <li>Achievements and XP system</li>
                            <li>Complete activity history</li>
                        </ul>
                        
                        <h4>💰 Digital Wallet</h4>
                        <ul>
                            <li>Real-time balance updated instantly</li>
                            <li>Complete history of all transactions</li>
                            <li>Transfers between players</li>
                            <li>Transfers to in-game characters</li>
                            <li>Configurable security limits</li>
                        </ul>
                        
                        <h4>🛒 Virtual Store</h4>
                        <ul>
                            <li>Complete catalog of items and packages</li>
                            <li>Intuitive shopping cart</li>
                            <li>Promotions and special offers</li>
                            <li>Automatic item delivery to your characters</li>
                            <li>Purchase history</li>
                        </ul>
                        
                        <h4>💳 Payment System</h4>
                        <ul>
                            <li>Multiple payment methods: Mercado Pago, Stripe and PayPal</li>
                            <li>Secure and encrypted payments</li>
                            <li>Automatic payment confirmation</li>
                            <li>Digital receipt for all transactions</li>
                        </ul>
                        
                        <h4>🔨 Auctions</h4>
                        <ul>
                            <li>Complete auction system between players</li>
                            <li>Bid on rare and exclusive items</li>
                            <li>Track auctions in real time</li>
                            <li>Bid and closing notifications</li>
                        </ul>
                        
                        <h4>🏪 Marketplace</h4>
                        <ul>
                            <li>Buy and sell characters directly with other players</li>
                            <li>Secure negotiation between players</li>
                            <li>Rating and reputation system</li>
                        </ul>
                        
                        <h4>🎲 Minigames</h4>
                        <ul>
                            <li>Roulette with various prizes</li>
                            <li>Mystery boxes</li>
                            <li>Dice and gambling games</li>
                            <li>Fishing with rewards</li>
                            <li>And much more fun!</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cuáles son las principales funcionalidades del PDL?',
                        'answer': '''
                        <h3>Funcionalidades Principales del PDL</h3>
                        
                        <h4>🎮 Sistema de Cuenta y Perfil</h4>
                        <ul>
                            <li>Registro seguro con autenticación en dos pasos (2FA)</li>
                            <li>Perfil personalizable con foto e información</li>
                            <li>Sistema de logros y XP</li>
                            <li>Historial completo de actividades</li>
                        </ul>
                        
                        <h4>💰 Billetera Digital</h4>
                        <ul>
                            <li>Saldo en tiempo real actualizado instantáneamente</li>
                            <li>Historial completo de todas las transacciones</li>
                            <li>Transferencias entre jugadores</li>
                            <li>Transferencias a personajes en el juego</li>
                            <li>Límites de seguridad configurables</li>
                        </ul>
                        
                        <h4>🛒 Tienda Virtual</h4>
                        <ul>
                            <li>Catálogo completo de ítems y paquetes</li>
                            <li>Carrito de compras intuitivo</li>
                            <li>Promociones y ofertas especiales</li>
                            <li>Entrega automática de ítems a tus personajes</li>
                            <li>Historial de compras</li>
                        </ul>
                        
                        <h4>💳 Sistema de Pagos</h4>
                        <ul>
                            <li>Múltiples métodos de pago: Mercado Pago, Stripe y PayPal</li>
                            <li>Pagos seguros y cifrados</li>
                            <li>Confirmación automática de pagos</li>
                            <li>Recibo digital de todas las transacciones</li>
                        </ul>
                        
                        <h4>🔨 Subastas</h4>
                        <ul>
                            <li>Sistema completo de subastas entre jugadores</li>
                            <li>Puja por ítems raros y exclusivos</li>
                            <li>Sigue subastas en tiempo real</li>
                            <li>Notificaciones de pujas y cierre</li>
                        </ul>
                        
                        <h4>🏪 Marketplace</h4>
                        <ul>
                            <li>Compra y vende personajes directamente con otros jugadores</li>
                            <li>Negociación segura entre jugadores</li>
                            <li>Sistema de evaluaciones y reputación</li>
                        </ul>
                        
                        <h4>🎲 Minijuegos</h4>
                        <ul>
                            <li>Ruleta con premios variados</li>
                            <li>Cajas misteriosas</li>
                            <li>Dados y juegos de azar</li>
                            <li>Pesca con recompensas</li>
                            <li>¡Y mucho más diversión!</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar a Loja Virtual do PDL?',
                        'answer': '''
                        <h3>Loja Virtual do PDL</h3>
                        <p>A loja virtual permite que você compre itens e serviços diretamente do painel, com entrega automática para seus personagens no jogo.</p>
                        
                        <h4>Como Navegar pela Loja:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Loja"</strong> no menu principal</li>
                            <li>Explore as categorias disponíveis (Armas, Armaduras, Consumíveis, etc.)</li>
                            <li>Use a barra de busca para encontrar itens específicos</li>
                            <li>Filtre por preço, categoria ou disponibilidade</li>
                        </ol>
                        
                        <h4>Como Comprar Itens:</h4>
                        <ol>
                            <li><strong>Visualizar Item:</strong>
                                <ul>
                                    <li>Clique no item que deseja comprar</li>
                                    <li>Veja detalhes, descrição e preço</li>
                                    <li>Verifique se o item está disponível</li>
                                </ul>
                            </li>
                            <li><strong>Adicionar ao Carrinho:</strong>
                                <ul>
                                    <li>Selecione a quantidade desejada</li>
                                    <li>Clique em <strong>"Adicionar ao Carrinho"</strong></li>
                                    <li>Continue comprando ou vá para o carrinho</li>
                                </ul>
                            </li>
                            <li><strong>Finalizar Compra:</strong>
                                <ul>
                                    <li>Vá para o carrinho clicando no ícone no menu</li>
                                    <li>Revise todos os itens selecionados</li>
                                    <li>Verifique o total da compra</li>
                                    <li>Escolha o método de pagamento (Carteira Digital, Mercado Pago, Stripe ou PayPal)</li>
                                    <li>Confirme a compra</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Entrega de Itens:</h4>
                        <ul>
                            <li>Os itens são entregues <strong>automaticamente</strong> quando o pagamento é confirmado</li>
                            <li>Os itens aparecem no inventário do personagem selecionado</li>
                            <li>Se o personagem estiver online, receberá os itens imediatamente</li>
                            <li>Se estiver offline, os itens serão entregues no próximo login</li>
                        </ul>
                        
                        <h4>Pacotes e Promoções:</h4>
                        <ul>
                            <li>Explore os pacotes especiais com múltiplos itens com desconto</li>
                            <li>Aproveite as promoções e ofertas limitadas</li>
                            <li>Fique atento às novidades e lançamentos</li>
                        </ul>
                        
                        <h4>Histórico de Compras:</h4>
                        <ul>
                            <li>Acesse <strong>"Minhas Compras"</strong> para ver todo o histórico</li>
                            <li>Visualize detalhes de cada compra realizada</li>
                            <li>Baixe recibos digitais das suas compras</li>
                        </ul>
                        
                        <h4>Dicas Importantes:</h4>
                        <ul>
                            <li>Verifique sempre se tem saldo suficiente ou método de pagamento configurado</li>
                            <li>Selecione o personagem correto antes de finalizar a compra</li>
                            <li>Mantenha espaço no inventário do personagem para receber os itens</li>
                            <li>Em caso de problemas, entre em contato com o suporte</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the PDL Virtual Store?',
                        'answer': '''
                        <h3>PDL Virtual Store</h3>
                        <p>The virtual store allows you to purchase items and services directly from the panel, with automatic delivery to your in-game characters.</p>
                        
                        <h4>How to Browse the Store:</h4>
                        <ol>
                            <li>Access the <strong>"Store"</strong> section in the main menu</li>
                            <li>Explore available categories (Weapons, Armor, Consumables, etc.)</li>
                            <li>Use the search bar to find specific items</li>
                            <li>Filter by price, category or availability</li>
                        </ol>
                        
                        <h4>How to Buy Items:</h4>
                        <ol>
                            <li><strong>View Item:</strong>
                                <ul>
                                    <li>Click on the item you want to buy</li>
                                    <li>See details, description and price</li>
                                    <li>Check if the item is available</li>
                                </ul>
                            </li>
                            <li><strong>Add to Cart:</strong>
                                <ul>
                                    <li>Select the desired quantity</li>
                                    <li>Click <strong>"Add to Cart"</strong></li>
                                    <li>Continue shopping or go to cart</li>
                                </ul>
                            </li>
                            <li><strong>Complete Purchase:</strong>
                                <ul>
                                    <li>Go to cart by clicking the icon in the menu</li>
                                    <li>Review all selected items</li>
                                    <li>Check the total purchase amount</li>
                                    <li>Choose payment method (Digital Wallet, Mercado Pago, Stripe or PayPal)</li>
                                    <li>Confirm purchase</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Item Delivery:</h4>
                        <ul>
                            <li>Items are delivered <strong>automatically</strong> when payment is confirmed</li>
                            <li>Items appear in the selected character's inventory</li>
                            <li>If the character is online, they will receive items immediately</li>
                            <li>If offline, items will be delivered on next login</li>
                        </ul>
                        
                        <h4>Packages and Promotions:</h4>
                        <ul>
                            <li>Explore special packages with multiple items at a discount</li>
                            <li>Take advantage of limited-time promotions and offers</li>
                            <li>Stay tuned for news and releases</li>
                        </ul>
                        
                        <h4>Purchase History:</h4>
                        <ul>
                            <li>Access <strong>"My Purchases"</strong> to see full history</li>
                            <li>View details of each purchase made</li>
                            <li>Download digital receipts of your purchases</li>
                        </ul>
                        
                        <h4>Important Tips:</h4>
                        <ul>
                            <li>Always check if you have sufficient balance or payment method configured</li>
                            <li>Select the correct character before completing purchase</li>
                            <li>Keep space in character inventory to receive items</li>
                            <li>If you have problems, contact support</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar la Tienda Virtual del PDL?',
                        'answer': '''
                        <h3>Tienda Virtual del PDL</h3>
                        <p>La tienda virtual te permite comprar ítems y servicios directamente desde el panel, con entrega automática a tus personajes en el juego.</p>
                        
                        <h4>Cómo Navegar por la Tienda:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Tienda"</strong> en el menú principal</li>
                            <li>Explora las categorías disponibles (Armas, Armaduras, Consumibles, etc.)</li>
                            <li>Usa la barra de búsqueda para encontrar ítems específicos</li>
                            <li>Filtra por precio, categoría o disponibilidad</li>
                        </ol>
                        
                        <h4>Cómo Comprar Ítems:</h4>
                        <ol>
                            <li><strong>Ver Ítem:</strong>
                                <ul>
                                    <li>Haz clic en el ítem que deseas comprar</li>
                                    <li>Ve detalles, descripción y precio</li>
                                    <li>Verifica si el ítem está disponible</li>
                                </ul>
                            </li>
                            <li><strong>Agregar al Carrito:</strong>
                                <ul>
                                    <li>Selecciona la cantidad deseada</li>
                                    <li>Haz clic en <strong>"Agregar al Carrito"</strong></li>
                                    <li>Continúa comprando o ve al carrito</li>
                                </ul>
                            </li>
                            <li><strong>Finalizar Compra:</strong>
                                <ul>
                                    <li>Ve al carrito haciendo clic en el ícono en el menú</li>
                                    <li>Revisa todos los ítems seleccionados</li>
                                    <li>Verifica el total de la compra</li>
                                    <li>Elige el método de pago (Billetera Digital, Mercado Pago, Stripe o PayPal)</li>
                                    <li>Confirma la compra</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Entrega de Ítems:</h4>
                        <ul>
                            <li>Los ítems se entregan <strong>automáticamente</strong> cuando se confirma el pago</li>
                            <li>Los ítems aparecen en el inventario del personaje seleccionado</li>
                            <li>Si el personaje está en línea, recibirá los ítems inmediatamente</li>
                            <li>Si está fuera de línea, los ítems se entregarán en el próximo inicio de sesión</li>
                        </ul>
                        
                        <h4>Paquetes y Promociones:</h4>
                        <ul>
                            <li>Explora los paquetes especiales con múltiples ítems con descuento</li>
                            <li>Aprovecha las promociones y ofertas limitadas</li>
                            <li>Mantente atento a las novedades y lanzamientos</li>
                        </ul>
                        
                        <h4>Historial de Compras:</h4>
                        <ul>
                            <li>Accede a <strong>"Mis Compras"</strong> para ver todo el historial</li>
                            <li>Visualiza detalles de cada compra realizada</li>
                            <li>Descarga recibos digitales de tus compras</li>
                        </ul>
                        
                        <h4>Consejos Importantes:</h4>
                        <ul>
                            <li>Verifica siempre si tienes saldo suficiente o método de pago configurado</li>
                            <li>Selecciona el personaje correcto antes de finalizar la compra</li>
                            <li>Mantén espacio en el inventario del personaje para recibir los ítems</li>
                            <li>En caso de problemas, contacta con el soporte</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar a Carteira Digital (Wallet)?',
                        'answer': '''
                        <h3>Carteira Digital do PDL</h3>
                        <p>A carteira digital permite que os jogadores gerenciem seu saldo e façam transações dentro do sistema.</p>
                        
                        <h4>Funcionalidades da Carteira:</h4>
                        <ul>
                            <li><strong>Saldo em Tempo Real:</strong> Visualize seu saldo atualizado instantaneamente</li>
                            <li><strong>Histórico de Transações:</strong> Acompanhe todas as movimentações financeiras</li>
                            <li><strong>Transferências entre Jogadores:</strong> Envie dinheiro para outros jogadores</li>
                            <li><strong>Transferências para Personagens:</strong> Envie dinheiro diretamente para seus personagens no jogo</li>
                            <li><strong>Limites de Segurança:</strong> Configure limites para proteger sua conta</li>
                        </ul>
                        
                        <h4>Como Adicionar Saldo:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Carteira"</strong> no menu</li>
                            <li>Clique em <strong>"Adicionar Saldo"</strong></li>
                            <li>Escolha o valor desejado</li>
                            <li>Selecione o método de pagamento (Mercado Pago, Stripe ou PayPal)</li>
                            <li>Complete o pagamento</li>
                            <li>O saldo será creditado automaticamente após a confirmação</li>
                        </ol>
                        
                        <h4>Como Fazer Transferências:</h4>
                        <ol>
                            <li><strong>Para outro jogador:</strong>
                                <ul>
                                    <li>Vá em <strong>"Carteira → Transferir"</strong></li>
                                    <li>Digite o nome do usuário ou e-mail do destinatário</li>
                                    <li>Informe o valor</li>
                                    <li>Confirme a transferência</li>
                                </ul>
                            </li>
                            <li><strong>Para personagem no jogo:</strong>
                                <ul>
                                    <li>Selecione o personagem na lista</li>
                                    <li>Informe o valor</li>
                                    <li>Confirme a transferência</li>
                                    <li>O dinheiro será enviado diretamente para o inventário do personagem</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Segurança:</h4>
                        <ul>
                            <li>Todas as transações são registradas e auditadas</li>
                            <li>Configure limites de transferência para maior segurança</li>
                            <li>Ative a autenticação em duas etapas (2FA) para proteção extra</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the Digital Wallet?',
                        'answer': '''
                        <h3>PDL Digital Wallet</h3>
                        <p>The digital wallet allows players to manage their balance and make transactions within the system.</p>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar la Billetera Digital?',
                        'answer': '''
                        <h3>Billetera Digital del PDL</h3>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como fazer pagamentos no PDL?',
                        'answer': '''
                        <h3>Métodos de Pagamento no PDL</h3>
                        <p>O PDL oferece várias formas seguras de fazer pagamentos para adicionar saldo à sua carteira ou comprar itens diretamente.</p>
                        
                        <h4>Métodos de Pagamento Disponíveis:</h4>
                        <ul>
                            <li><strong>Carteira Digital:</strong> Use o saldo já disponível na sua conta</li>
                            <li><strong>Mercado Pago:</strong> Pagamento via cartão de crédito, débito ou boleto</li>
                            <li><strong>Stripe:</strong> Pagamento internacional via cartão de crédito</li>
                            <li><strong>PayPal:</strong> Pagamento via conta PayPal</li>
                        </ul>
                        
                        <h4>Como Adicionar Saldo à Carteira:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Carteira"</strong> no menu</li>
                            <li>Clique em <strong>"Adicionar Saldo"</strong></li>
                            <li>Escolha o valor desejado ou digite um valor personalizado</li>
                            <li>Selecione o método de pagamento</li>
                            <li>Siga as instruções na tela para completar o pagamento</li>
                            <li>O saldo será creditado automaticamente após a confirmação</li>
                        </ol>
                        
                        <h4>Como Pagar uma Compra:</h4>
                        <ol>
                            <li>Adicione itens ao carrinho na loja virtual</li>
                            <li>Vá para o carrinho e revise os itens</li>
                            <li>Na finalização, escolha o método de pagamento:
                                <ul>
                                    <li><strong>Carteira Digital:</strong> Se você já tem saldo suficiente</li>
                                    <li><strong>Mercado Pago/Stripe/PayPal:</strong> Para pagamento direto</li>
                                </ul>
                            </li>
                            <li>Complete o pagamento conforme o método escolhido</li>
                            <li>Os itens serão entregues automaticamente após confirmação</li>
                        </ol>
                        
                        <h4>Segurança dos Pagamentos:</h4>
                        <ul>
                            <li>Todos os pagamentos são processados de forma segura e criptografada</li>
                            <li>Nunca compartilhe suas informações de pagamento</li>
                            <li>Verifique sempre o site antes de inserir dados sensíveis</li>
                            <li>Todas as transações são registradas e você recebe um recibo digital</li>
                        </ul>
                        
                        <h4>Problemas com Pagamentos:</h4>
                        <ul>
                            <li>Se o pagamento não foi confirmado, verifique seu e-mail para instruções</li>
                            <li>Em caso de pagamento duplicado, entre em contato com o suporte</li>
                            <li>Verifique se há saldo suficiente no cartão/conta</li>
                            <li>Confirme se o método de pagamento está ativo e válido</li>
                        </ul>
                        
                        <h4>Histórico de Pagamentos:</h4>
                        <ul>
                            <li>Acesse <strong>"Carteira → Histórico"</strong> para ver todas as transações</li>
                            <li>Visualize pagamentos, recebimentos e transferências</li>
                            <li>Baixe recibos digitais de todas as transações</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to make payments in PDL?',
                        'answer': '''
                        <h3>Payment Methods in PDL</h3>
                        <p>PDL offers several secure ways to make payments to add balance to your wallet or buy items directly.</p>
                        
                        <h4>Available Payment Methods:</h4>
                        <ul>
                            <li><strong>Digital Wallet:</strong> Use the balance already available in your account</li>
                            <li><strong>Mercado Pago:</strong> Payment via credit card, debit card or bank slip</li>
                            <li><strong>Stripe:</strong> International payment via credit card</li>
                            <li><strong>PayPal:</strong> Payment via PayPal account</li>
                        </ul>
                        
                        <h4>How to Add Balance to Wallet:</h4>
                        <ol>
                            <li>Access the <strong>"Wallet"</strong> section in the menu</li>
                            <li>Click <strong>"Add Balance"</strong></li>
                            <li>Choose the desired amount or enter a custom amount</li>
                            <li>Select payment method</li>
                            <li>Follow on-screen instructions to complete payment</li>
                            <li>Balance will be credited automatically after confirmation</li>
                        </ol>
                        
                        <h4>How to Pay for a Purchase:</h4>
                        <ol>
                            <li>Add items to cart in virtual store</li>
                            <li>Go to cart and review items</li>
                            <li>At checkout, choose payment method:
                                <ul>
                                    <li><strong>Digital Wallet:</strong> If you already have sufficient balance</li>
                                    <li><strong>Mercado Pago/Stripe/PayPal:</strong> For direct payment</li>
                                </ul>
                            </li>
                            <li>Complete payment according to chosen method</li>
                            <li>Items will be delivered automatically after confirmation</li>
                        </ol>
                        
                        <h4>Payment Security:</h4>
                        <ul>
                            <li>All payments are processed securely and encrypted</li>
                            <li>Never share your payment information</li>
                            <li>Always verify the site before entering sensitive data</li>
                            <li>All transactions are recorded and you receive a digital receipt</li>
                        </ul>
                        
                        <h4>Payment Issues:</h4>
                        <ul>
                            <li>If payment was not confirmed, check your email for instructions</li>
                            <li>In case of duplicate payment, contact support</li>
                            <li>Check if there is sufficient balance on card/account</li>
                            <li>Confirm if payment method is active and valid</li>
                        </ul>
                        
                        <h4>Payment History:</h4>
                        <ul>
                            <li>Access <strong>"Wallet → History"</strong> to see all transactions</li>
                            <li>View payments, receipts and transfers</li>
                            <li>Download digital receipts for all transactions</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo hacer pagos en el PDL?',
                        'answer': '''
                        <h3>Métodos de Pago en el PDL</h3>
                        <p>El PDL ofrece varias formas seguras de realizar pagos para agregar saldo a tu billetera o comprar ítems directamente.</p>
                        
                        <h4>Métodos de Pago Disponibles:</h4>
                        <ul>
                            <li><strong>Billetera Digital:</strong> Usa el saldo ya disponible en tu cuenta</li>
                            <li><strong>Mercado Pago:</strong> Pago mediante tarjeta de crédito, débito o boleto</li>
                            <li><strong>Stripe:</strong> Pago internacional mediante tarjeta de crédito</li>
                            <li><strong>PayPal:</strong> Pago mediante cuenta PayPal</li>
                        </ul>
                        
                        <h4>Cómo Agregar Saldo a la Billetera:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Billetera"</strong> en el menú</li>
                            <li>Haz clic en <strong>"Agregar Saldo"</strong></li>
                            <li>Elige el monto deseado o ingresa un monto personalizado</li>
                            <li>Selecciona el método de pago</li>
                            <li>Sigue las instrucciones en pantalla para completar el pago</li>
                            <li>El saldo se acreditará automáticamente después de la confirmación</li>
                        </ol>
                        
                        <h4>Cómo Pagar una Compra:</h4>
                        <ol>
                            <li>Agrega ítems al carrito en la tienda virtual</li>
                            <li>Ve al carrito y revisa los ítems</li>
                            <li>En la finalización, elige el método de pago:
                                <ul>
                                    <li><strong>Billetera Digital:</strong> Si ya tienes saldo suficiente</li>
                                    <li><strong>Mercado Pago/Stripe/PayPal:</strong> Para pago directo</li>
                                </ul>
                            </li>
                            <li>Completa el pago según el método elegido</li>
                            <li>Los ítems se entregarán automáticamente después de la confirmación</li>
                        </ol>
                        
                        <h4>Seguridad de los Pagos:</h4>
                        <ul>
                            <li>Todos los pagos se procesan de forma segura y cifrada</li>
                            <li>Nunca compartas tu información de pago</li>
                            <li>Verifica siempre el sitio antes de ingresar datos sensibles</li>
                            <li>Todas las transacciones se registran y recibes un recibo digital</li>
                        </ul>
                        
                        <h4>Problemas con Pagos:</h4>
                        <ul>
                            <li>Si el pago no fue confirmado, verifica tu correo para instrucciones</li>
                            <li>En caso de pago duplicado, contacta con el soporte</li>
                            <li>Verifica si hay saldo suficiente en la tarjeta/cuenta</li>
                            <li>Confirma si el método de pago está activo y válido</li>
                        </ul>
                        
                        <h4>Historial de Pagos:</h4>
                        <ul>
                            <li>Accede a <strong>"Billetera → Historial"</strong> para ver todas las transacciones</li>
                            <li>Visualiza pagos, recibos y transferencias</li>
                            <li>Descarga recibos digitales de todas las transacciones</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como criar minha conta e personalizar meu perfil?',
                        'answer': '''
                        <h3>Criar Conta no PDL</h3>
                        <p>Criar uma conta no PDL é simples e rápido. Siga os passos abaixo:</p>
                        
                        <h4>Como Criar Conta:</h4>
                        <ol>
                            <li>Acesse a página de registro do PDL</li>
                            <li>Preencha os dados solicitados:
                                <ul>
                                    <li>Nome de usuário (único e não pode ser alterado depois)</li>
                                    <li>E-mail válido</li>
                                    <li>Senha segura (mínimo de caracteres conforme política do servidor)</li>
                                </ul>
                            </li>
                            <li>Leia e aceite os termos de uso</li>
                            <li>Clique em <strong>"Criar Conta"</strong></li>
                            <li>Verifique seu e-mail para ativar a conta</li>
                        </ol>
                        
                        <h4>Personalizar Perfil:</h4>
                        <ol>
                            <li>Após fazer login, acesse <strong>"Meu Perfil"</strong> no menu</li>
                            <li>Você pode personalizar:
                                <ul>
                                    <li>Foto de perfil</li>
                                    <li>Biografia e informações pessoais</li>
                                    <li>Preferências de notificação</li>
                                    <li>Configurações de privacidade</li>
                                </ul>
                            </li>
                            <li>Salve as alterações</li>
                        </ol>
                        
                        <h4>Segurança da Conta:</h4>
                        <ul>
                            <li><strong>Autenticação em Duas Etapas (2FA):</strong> Ative para maior segurança</li>
                            <li><strong>Senha Forte:</strong> Use uma combinação de letras, números e símbolos</li>
                            <li><strong>E-mail Verificado:</strong> Mantenha seu e-mail atualizado para recuperação de conta</li>
                            <li><strong>Histórico de Login:</strong> Monitore acessos à sua conta</li>
                        </ul>
                        
                        <h4>Sistema de Conquistas e XP:</h4>
                        <ul>
                            <li>Ganhe XP realizando ações no painel (compras, transferências, etc.)</li>
                            <li>Desbloqueie conquistas conforme você usa o sistema</li>
                            <li>Visualize seu progresso no perfil</li>
                            <li>Compartilhe suas conquistas com outros jogadores</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to create my account and customize my profile?',
                        'answer': '''
                        <h3>Create Account in PDL</h3>
                        <p>Creating an account in PDL is simple and fast. Follow the steps below:</p>
                        
                        <h4>How to Create Account:</h4>
                        <ol>
                            <li>Access the PDL registration page</li>
                            <li>Fill in the requested data:
                                <ul>
                                    <li>Username (unique and cannot be changed later)</li>
                                    <li>Valid email</li>
                                    <li>Secure password (minimum characters according to server policy)</li>
                                </ul>
                            </li>
                            <li>Read and accept the terms of use</li>
                            <li>Click <strong>"Create Account"</strong></li>
                            <li>Check your email to activate the account</li>
                        </ol>
                        
                        <h4>Customize Profile:</h4>
                        <ol>
                            <li>After logging in, access <strong>"My Profile"</strong> in the menu</li>
                            <li>You can customize:
                                <ul>
                                    <li>Profile photo</li>
                                    <li>Biography and personal information</li>
                                    <li>Notification preferences</li>
                                    <li>Privacy settings</li>
                                </ul>
                            </li>
                            <li>Save changes</li>
                        </ol>
                        
                        <h4>Account Security:</h4>
                        <ul>
                            <li><strong>Two-Factor Authentication (2FA):</strong> Enable for greater security</li>
                            <li><strong>Strong Password:</strong> Use a combination of letters, numbers and symbols</li>
                            <li><strong>Verified Email:</strong> Keep your email updated for account recovery</li>
                            <li><strong>Login History:</strong> Monitor access to your account</li>
                        </ul>
                        
                        <h4>Achievements and XP System:</h4>
                        <ul>
                            <li>Earn XP by performing actions in the panel (purchases, transfers, etc.)</li>
                            <li>Unlock achievements as you use the system</li>
                            <li>View your progress in profile</li>
                            <li>Share your achievements with other players</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo crear mi cuenta y personalizar mi perfil?',
                        'answer': '''
                        <h3>Crear Cuenta en el PDL</h3>
                        <p>Crear una cuenta en el PDL es simple y rápido. Sigue los pasos a continuación:</p>
                        
                        <h4>Cómo Crear Cuenta:</h4>
                        <ol>
                            <li>Accede a la página de registro del PDL</li>
                            <li>Completa los datos solicitados:
                                <ul>
                                    <li>Nombre de usuario (único y no se puede cambiar después)</li>
                                    <li>Correo electrónico válido</li>
                                    <li>Contraseña segura (mínimo de caracteres según política del servidor)</li>
                                </ul>
                            </li>
                            <li>Lee y acepta los términos de uso</li>
                            <li>Haz clic en <strong>"Crear Cuenta"</strong></li>
                            <li>Verifica tu correo para activar la cuenta</li>
                        </ol>
                        
                        <h4>Personalizar Perfil:</h4>
                        <ol>
                            <li>Después de iniciar sesión, accede a <strong>"Mi Perfil"</strong> en el menú</li>
                            <li>Puedes personalizar:
                                <ul>
                                    <li>Foto de perfil</li>
                                    <li>Biografía e información personal</li>
                                    <li>Preferencias de notificación</li>
                                    <li>Configuraciones de privacidad</li>
                                </ul>
                            </li>
                            <li>Guarda los cambios</li>
                        </ol>
                        
                        <h4>Seguridad de la Cuenta:</h4>
                        <ul>
                            <li><strong>Autenticación en Dos Pasos (2FA):</strong> Activa para mayor seguridad</li>
                            <li><strong>Contraseña Fuerte:</strong> Usa una combinación de letras, números y símbolos</li>
                            <li><strong>Correo Verificado:</strong> Mantén tu correo actualizado para recuperación de cuenta</li>
                            <li><strong>Historial de Inicio de Sesión:</strong> Monitorea accesos a tu cuenta</li>
                        </ul>
                        
                        <h4>Sistema de Logros y XP:</h4>
                        <ul>
                            <li>Gana XP realizando acciones en el panel (compras, transferencias, etc.)</li>
                            <li>Desbloquea logros conforme usas el sistema</li>
                            <li>Visualiza tu progreso en el perfil</li>
                            <li>Comparte tus logros con otros jugadores</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar o sistema de Leilões?',
                        'answer': '''
                        <h3>Sistema de Leilões do PDL</h3>
                        <p>O sistema de leilões permite que você participe de leilões de itens raros e exclusivos, ou crie seus próprios leilões para vender itens.</p>
                        
                        <h4>Como Participar de um Leilão:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Leilões"</strong> no menu</li>
                            <li>Navegue pelos leilões ativos disponíveis</li>
                            <li>Clique no leilão que deseja participar</li>
                            <li>Veja os detalhes: item, lance atual, tempo restante</li>
                            <li>Digite seu lance (deve ser maior que o lance atual)</li>
                            <li>Confirme o lance</li>
                            <li>Você receberá notificações se alguém superar seu lance</li>
                        </ol>
                        
                        <h4>Como Criar um Leilão:</h4>
                        <ol>
                            <li>Vá em <strong>"Leilões → Criar Leilão"</strong></li>
                            <li>Selecione o item que deseja leiloar</li>
                            <li>Configure:
                                <ul>
                                    <li>Lance inicial (valor mínimo)</li>
                                    <li>Incremento mínimo entre lances</li>
                                    <li>Duração do leilão (horas/dias)</li>
                                    <li>Descrição do item (opcional)</li>
                                </ul>
                            </li>
                            <li>Confirme a criação do leilão</li>
                            <li>Acompanhe seu leilão na seção "Meus Leilões"</li>
                        </ol>
                        
                        <h4>Dicas Importantes:</h4>
                        <ul>
                            <li>Certifique-se de ter saldo suficiente na carteira para dar lances</li>
                            <li>O saldo é bloqueado quando você dá um lance e liberado se alguém superar</li>
                            <li>Fique atento ao tempo restante do leilão</li>
                            <li>Você pode cancelar seu lance antes que alguém supere</li>
                            <li>Ao vencer um leilão, o item será entregue automaticamente</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the Auction system?',
                        'answer': '''
                        <h3>PDL Auction System</h3>
                        <p>The auction system allows you to participate in auctions of rare and exclusive items, or create your own auctions to sell items.</p>
                        
                        <h4>How to Participate in an Auction:</h4>
                        <ol>
                            <li>Access the <strong>"Auctions"</strong> section in the menu</li>
                            <li>Browse available active auctions</li>
                            <li>Click on the auction you want to participate in</li>
                            <li>See details: item, current bid, time remaining</li>
                            <li>Enter your bid (must be higher than current bid)</li>
                            <li>Confirm the bid</li>
                            <li>You will receive notifications if someone outbids you</li>
                        </ol>
                        
                        <h4>How to Create an Auction:</h4>
                        <ol>
                            <li>Go to <strong>"Auctions → Create Auction"</strong></li>
                            <li>Select the item you want to auction</li>
                            <li>Configure:
                                <ul>
                                    <li>Starting bid (minimum value)</li>
                                    <li>Minimum increment between bids</li>
                                    <li>Auction duration (hours/days)</li>
                                    <li>Item description (optional)</li>
                                </ul>
                            </li>
                            <li>Confirm auction creation</li>
                            <li>Track your auction in "My Auctions" section</li>
                        </ol>
                        
                        <h4>Important Tips:</h4>
                        <ul>
                            <li>Make sure you have sufficient balance in wallet to place bids</li>
                            <li>Balance is blocked when you place a bid and released if someone outbids</li>
                            <li>Pay attention to remaining auction time</li>
                            <li>You can cancel your bid before someone outbids</li>
                            <li>When winning an auction, the item will be delivered automatically</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar el sistema de Subastas?',
                        'answer': '''
                        <h3>Sistema de Subastas del PDL</h3>
                        <p>El sistema de subastas te permite participar en subastas de ítems raros y exclusivos, o crear tus propias subastas para vender ítems.</p>
                        
                        <h4>Cómo Participar en una Subasta:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Subastas"</strong> en el menú</li>
                            <li>Navega por las subastas activas disponibles</li>
                            <li>Haz clic en la subasta en la que deseas participar</li>
                            <li>Ve los detalles: ítem, puja actual, tiempo restante</li>
                            <li>Ingresa tu puja (debe ser mayor que la puja actual)</li>
                            <li>Confirma la puja</li>
                            <li>Recibirás notificaciones si alguien supera tu puja</li>
                        </ol>
                        
                        <h4>Cómo Crear una Subasta:</h4>
                        <ol>
                            <li>Ve a <strong>"Subastas → Crear Subasta"</strong></li>
                            <li>Selecciona el ítem que deseas subastar</li>
                            <li>Configura:
                                <ul>
                                    <li>Puja inicial (valor mínimo)</li>
                                    <li>Incremento mínimo entre pujas</li>
                                    <li>Duración de la subasta (horas/días)</li>
                                    <li>Descripción del ítem (opcional)</li>
                                </ul>
                            </li>
                            <li>Confirma la creación de la subasta</li>
                            <li>Acompaña tu subasta en la sección "Mis Subastas"</li>
                        </ol>
                        
                        <h4>Consejos Importantes:</h4>
                        <ul>
                            <li>Asegúrate de tener saldo suficiente en la billetera para hacer pujas</li>
                            <li>El saldo se bloquea cuando haces una puja y se libera si alguien supera</li>
                            <li>Presta atención al tiempo restante de la subasta</li>
                            <li>Puedes cancelar tu puja antes de que alguien la supere</li>
                            <li>Al ganar una subasta, el ítem se entregará automáticamente</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar o Marketplace?',
                        'answer': '''
                        <h3>Marketplace do PDL</h3>
                        <p>O marketplace permite que você compre e venda <strong>personagens</strong> diretamente com outros jogadores, de forma segura e sem intermediários.</p>
                        
                        <h4>🛒 Como Comprar no Marketplace:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Marketplace"</strong> no menu</li>
                            <li>Navegue pelos personagens disponíveis para venda</li>
                            <li>Use filtros para encontrar o que procura:
                                <ul>
                                    <li>Classe do personagem</li>
                                    <li>Nível</li>
                                    <li>Faixa de preço</li>
                                    <li>Equipamentos incluídos</li>
                                </ul>
                            </li>
                            <li>Clique no personagem desejado para ver detalhes completos</li>
                            <li>Verifique:
                                <ul>
                                    <li>Nível e classe</li>
                                    <li>Equipamentos e itens incluídos</li>
                                    <li>Skills aprendidas</li>
                                    <li>Preço pedido</li>
                                    <li>Avaliações do vendedor</li>
                                </ul>
                            </li>
                            <li>Clique em <strong>"Comprar"</strong></li>
                            <li>Confirme a compra</li>
                            <li>O personagem será transferido para sua conta</li>
                        </ol>
                        
                        <h4>💰 Como Vender no Marketplace:</h4>
                        <ol>
                            <li>Vá em <strong>"Marketplace → Vender Personagem"</strong></li>
                            <li>Selecione o personagem que deseja vender da sua lista</li>
                            <li>Configure o anúncio:
                                <ul>
                                    <li>Preço de venda</li>
                                    <li>Descrição detalhada</li>
                                    <li>O que está incluso (equipamentos, itens, etc.)</li>
                                </ul>
                            </li>
                            <li>Publique o anúncio</li>
                            <li>Acompanhe suas vendas em "Minhas Vendas"</li>
                            <li>Quando vender, o valor vai para sua carteira</li>
                        </ol>
                        
                        <h4>⭐ Sistema de Avaliações:</h4>
                        <ul>
                            <li>Após uma transação, avalie o vendedor/comprador</li>
                            <li>As avaliações ajudam a construir reputação</li>
                            <li>Vendedores com boa reputação são mais confiáveis</li>
                            <li>Evite transações com jogadores sem avaliações ou com avaliações negativas</li>
                        </ul>
                        
                        <h4>🔒 Segurança:</h4>
                        <ul>
                            <li>Todas as transações são mediadas pelo sistema</li>
                            <li>O pagamento é retido até a transferência ser confirmada</li>
                            <li>Sempre verifique o perfil do vendedor antes de comprar</li>
                            <li>Leia as avaliações e comentários de outros jogadores</li>
                            <li>Em caso de problemas, entre em contato com o suporte</li>
                            <li>Nunca faça transações fora do sistema oficial</li>
                        </ul>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li>Personagens à venda ficam bloqueados até a venda ser concluída ou cancelada</li>
                            <li>Você não pode jogar com um personagem enquanto ele estiver à venda</li>
                            <li>A transferência é definitiva após confirmação</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the Marketplace?',
                        'answer': '''
                        <h3>PDL Marketplace</h3>
                        <p>The marketplace allows you to buy and sell <strong>characters</strong> directly with other players, securely and without intermediaries.</p>
                        
                        <h4>🛒 How to Buy on Marketplace:</h4>
                        <ol>
                            <li>Access the <strong>"Marketplace"</strong> section in the menu</li>
                            <li>Browse characters available for sale</li>
                            <li>Use filters to find what you're looking for (class, level, price)</li>
                            <li>Click on desired character to see full details</li>
                            <li>Check level, class, equipment, skills and price</li>
                            <li>Click <strong>"Buy"</strong></li>
                            <li>Confirm purchase</li>
                            <li>Character will be transferred to your account</li>
                        </ol>
                        
                        <h4>💰 How to Sell on Marketplace:</h4>
                        <ol>
                            <li>Go to <strong>"Marketplace → Sell Character"</strong></li>
                            <li>Select the character you want to sell</li>
                            <li>Set price and description</li>
                            <li>Publish the listing</li>
                            <li>Track your sales in "My Sales"</li>
                        </ol>
                        
                        <h4>🔒 Security:</h4>
                        <ul>
                            <li>All transactions are mediated by the system</li>
                            <li>Payment is held until transfer is confirmed</li>
                            <li>Never make transactions outside the official system</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar el Marketplace?',
                        'answer': '''
                        <h3>Marketplace del PDL</h3>
                        <p>El marketplace te permite comprar y vender <strong>personajes</strong> directamente con otros jugadores, de forma segura y sin intermediarios.</p>
                        
                        <h4>🛒 Cómo Comprar en el Marketplace:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Marketplace"</strong> en el menú</li>
                            <li>Navega por los personajes disponibles para venta</li>
                            <li>Usa filtros para encontrar lo que buscas</li>
                            <li>Haz clic en el personaje deseado para ver detalles</li>
                            <li>Verifica nivel, clase, equipamiento y precio</li>
                            <li>Haz clic en <strong>"Comprar"</strong></li>
                            <li>Confirma la compra</li>
                            <li>El personaje se transferirá a tu cuenta</li>
                        </ol>
                        
                        <h4>💰 Cómo Vender en el Marketplace:</h4>
                        <ol>
                            <li>Ve a <strong>"Marketplace → Vender Personaje"</strong></li>
                            <li>Selecciona el personaje que deseas vender</li>
                            <li>Configura precio y descripción</li>
                            <li>Publica el anuncio</li>
                        </ol>
                        
                        <h4>🔒 Seguridad:</h4>
                        <ul>
                            <li>Todas las transacciones son mediadas por el sistema</li>
                            <li>Nunca hagas transacciones fuera del sistema oficial</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar os Minigames?',
                        'answer': '''
                        <h3>Minigames do PDL</h3>
                        <p>Os minigames oferecem diversão e a chance de ganhar prêmios especiais enquanto você joga.</p>
                        
                        <h4>Tipos de Minigames Disponíveis:</h4>
                        <ul>
                            <li><strong>Roleta:</strong> Gire a roleta e ganhe prêmios aleatórios</li>
                            <li><strong>Caixas Misteriosas:</strong> Abra caixas para descobrir itens surpresa</li>
                            <li><strong>Dados:</strong> Jogue dados e ganhe prêmios baseados no resultado</li>
                            <li><strong>Pesca:</strong> Participe de eventos de pesca e ganhe recompensas</li>
                            <li><strong>Outros:</strong> Novos minigames são adicionados regularmente</li>
                        </ul>
                        
                        <h4>Como Jogar:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Minigames"</strong> no menu</li>
                            <li>Escolha o minigame que deseja jogar</li>
                            <li>Verifique os prêmios disponíveis e custos</li>
                            <li>Confirme sua participação</li>
                            <li>O resultado será exibido imediatamente</li>
                            <li>Prêmios são entregues automaticamente ao seu inventário</li>
                        </ol>
                        
                        <h4>Dicas Importantes:</h4>
                        <ul>
                            <li>Alguns minigames têm custo de entrada (saldo ou itens)</li>
                            <li>Verifique as probabilidades de ganho antes de jogar</li>
                            <li>Prêmios variam de acordo com o minigame</li>
                            <li>Participe de eventos especiais para prêmios exclusivos</li>
                            <li>Jogue com responsabilidade e dentro do seu orçamento</li>
                        </ul>
                        
                        <h4>Histórico de Minigames:</h4>
                        <ul>
                            <li>Acesse <strong>"Minigames → Meu Histórico"</strong> para ver todas as partidas</li>
                            <li>Visualize prêmios ganhos e estatísticas</li>
                            <li>Acompanhe seu progresso em conquistas relacionadas</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use Minigames?',
                        'answer': '''
                        <h3>PDL Minigames</h3>
                        <p>Minigames offer fun and the chance to win special prizes while you play.</p>
                        
                        <h4>Available Minigame Types:</h4>
                        <ul>
                            <li><strong>Roulette:</strong> Spin the roulette and win random prizes</li>
                            <li><strong>Mystery Boxes:</strong> Open boxes to discover surprise items</li>
                            <li><strong>Dice:</strong> Roll dice and win prizes based on result</li>
                            <li><strong>Fishing:</strong> Participate in fishing events and win rewards</li>
                            <li><strong>Others:</strong> New minigames are added regularly</li>
                        </ul>
                        
                        <h4>How to Play:</h4>
                        <ol>
                            <li>Access the <strong>"Minigames"</strong> section in the menu</li>
                            <li>Choose the minigame you want to play</li>
                            <li>Check available prizes and costs</li>
                            <li>Confirm your participation</li>
                            <li>Result will be displayed immediately</li>
                            <li>Prizes are automatically delivered to your inventory</li>
                        </ol>
                        
                        <h4>Important Tips:</h4>
                        <ul>
                            <li>Some minigames have entry cost (balance or items)</li>
                            <li>Check win probabilities before playing</li>
                            <li>Prizes vary according to minigame</li>
                            <li>Participate in special events for exclusive prizes</li>
                            <li>Play responsibly and within your budget</li>
                        </ul>
                        
                        <h4>Minigame History:</h4>
                        <ul>
                            <li>Access <strong>"Minigames → My History"</strong> to see all games</li>
                            <li>View prizes won and statistics</li>
                            <li>Track your progress in related achievements</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar los Minijuegos?',
                        'answer': '''
                        <h3>Minijuegos del PDL</h3>
                        <p>Los minijuegos ofrecen diversión y la oportunidad de ganar premios especiales mientras juegas.</p>
                        
                        <h4>Tipos de Minijuegos Disponibles:</h4>
                        <ul>
                            <li><strong>Ruleta:</strong> Gira la ruleta y gana premios aleatorios</li>
                            <li><strong>Cajas Misteriosas:</strong> Abre cajas para descubrir ítems sorpresa</li>
                            <li><strong>Dados:</strong> Tira dados y gana premios basados en el resultado</li>
                            <li><strong>Pesca:</strong> Participa en eventos de pesca y gana recompensas</li>
                            <li><strong>Otros:</strong> Nuevos minijuegos se agregan regularmente</li>
                        </ul>
                        
                        <h4>Cómo Jugar:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Minijuegos"</strong> en el menú</li>
                            <li>Elige el minijuego que deseas jugar</li>
                            <li>Verifica los premios disponibles y costos</li>
                            <li>Confirma tu participación</li>
                            <li>El resultado se mostrará inmediatamente</li>
                            <li>Los premios se entregan automáticamente a tu inventario</li>
                        </ol>
                        
                        <h4>Consejos Importantes:</h4>
                        <ul>
                            <li>Algunos minijuegos tienen costo de entrada (saldo o ítems)</li>
                            <li>Verifica las probabilidades de ganancia antes de jugar</li>
                            <li>Los premios varían según el minijuego</li>
                            <li>Participa en eventos especiales para premios exclusivos</li>
                            <li>Juega con responsabilidad y dentro de tu presupuesto</li>
                        </ul>
                        
                        <h4>Historial de Minijuegos:</h4>
                        <ul>
                            <li>Accede a <strong>"Minijuegos → Mi Historial"</strong> para ver todas las partidas</li>
                            <li>Visualiza premios ganados y estadísticas</li>
                            <li>Acompaña tu progreso en logros relacionados</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como gerenciar meus personagens no PDL?',
                        'answer': '''
                        <h3>Gerenciamento de Personagens</h3>
                        <p>O PDL permite que você visualize e gerencie seus personagens do servidor Lineage 2 diretamente do painel.</p>
                        
                        <h4>Visualizar Personagens:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Meus Personagens"</strong> no menu</li>
                            <li>Veja a lista de todos os seus personagens</li>
                            <li>Visualize informações como:
                                <ul>
                                    <li>Nome e nível do personagem</li>
                                    <li>Classe e raça</li>
                                    <li>Status online/offline</li>
                                    <li>Localização atual</li>
                                    <li>Estatísticas básicas</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Transferir Itens e Dinheiro:</h4>
                        <ol>
                            <li>Selecione o personagem de destino</li>
                            <li>Vá em <strong>"Carteira → Transferir para Personagem"</strong></li>
                            <li>Ou use a opção na loja para entregar itens</li>
                            <li>Confirme a transferência</li>
                            <li>Itens/dinheiro serão entregues automaticamente</li>
                        </ol>
                        
                        <h4>Receber Itens da Loja:</h4>
                        <ul>
                            <li>Ao comprar na loja, selecione o personagem que receberá os itens</li>
                            <li>Se o personagem estiver online, receberá imediatamente</li>
                            <li>Se estiver offline, receberá no próximo login</li>
                            <li>Verifique sempre se há espaço no inventário</li>
                        </ul>
                        
                        <h4>Dicas Importantes:</h4>
                        <ul>
                            <li>Mantenha espaço no inventário dos personagens para receber itens</li>
                            <li>Personagens online recebem itens instantaneamente</li>
                            <li>Verifique o status do personagem antes de fazer transferências</li>
                            <li>Em caso de problemas com entrega, entre em contato com o suporte</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to manage my characters in PDL?',
                        'answer': '''
                        <h3>Character Management</h3>
                        <p>PDL allows you to view and manage your Lineage 2 server characters directly from the panel.</p>
                        
                        <h4>View Characters:</h4>
                        <ol>
                            <li>Access the <strong>"My Characters"</strong> section in the menu</li>
                            <li>See list of all your characters</li>
                            <li>View information such as:
                                <ul>
                                    <li>Character name and level</li>
                                    <li>Class and race</li>
                                    <li>Online/offline status</li>
                                    <li>Current location</li>
                                    <li>Basic statistics</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Transfer Items and Money:</h4>
                        <ol>
                            <li>Select target character</li>
                            <li>Go to <strong>"Wallet → Transfer to Character"</strong></li>
                            <li>Or use store option to deliver items</li>
                            <li>Confirm transfer</li>
                            <li>Items/money will be delivered automatically</li>
                        </ol>
                        
                        <h4>Receive Store Items:</h4>
                        <ul>
                            <li>When buying in store, select character that will receive items</li>
                            <li>If character is online, will receive immediately</li>
                            <li>If offline, will receive on next login</li>
                            <li>Always check if there is inventory space</li>
                        </ul>
                        
                        <h4>Important Tips:</h4>
                        <ul>
                            <li>Keep inventory space in characters to receive items</li>
                            <li>Online characters receive items instantly</li>
                            <li>Check character status before making transfers</li>
                            <li>In case of delivery problems, contact support</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo gestionar mis personajes en el PDL?',
                        'answer': '''
                        <h3>Gestión de Personajes</h3>
                        <p>El PDL te permite visualizar y gestionar tus personajes del servidor Lineage 2 directamente desde el panel.</p>
                        
                        <h4>Visualizar Personajes:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Mis Personajes"</strong> en el menú</li>
                            <li>Ve la lista de todos tus personajes</li>
                            <li>Visualiza información como:
                                <ul>
                                    <li>Nombre y nivel del personaje</li>
                                    <li>Clase y raza</li>
                                    <li>Estado en línea/fuera de línea</li>
                                    <li>Ubicación actual</li>
                                    <li>Estadísticas básicas</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>Transferir Ítems y Dinero:</h4>
                        <ol>
                            <li>Selecciona el personaje de destino</li>
                            <li>Ve a <strong>"Billetera → Transferir a Personaje"</strong></li>
                            <li>O usa la opción en la tienda para entregar ítems</li>
                            <li>Confirma la transferencia</li>
                            <li>Los ítems/dinero se entregarán automáticamente</li>
                        </ol>
                        
                        <h4>Recibir Ítems de la Tienda:</h4>
                        <ul>
                            <li>Al comprar en la tienda, selecciona el personaje que recibirá los ítems</li>
                            <li>Si el personaje está en línea, recibirá inmediatamente</li>
                            <li>Si está fuera de línea, recibirá en el próximo inicio de sesión</li>
                            <li>Verifica siempre si hay espacio en el inventario</li>
                        </ul>
                        
                        <h4>Consejos Importantes:</h4>
                        <ul>
                            <li>Mantén espacio en el inventario de los personajes para recibir ítems</li>
                            <li>Los personajes en línea reciben ítems instantáneamente</li>
                            <li>Verifica el estado del personaje antes de hacer transferencias</li>
                            <li>En caso de problemas con la entrega, contacta con el soporte</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== LGPD / PROTEÇÃO DE DADOS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como o PDL protege meus dados pessoais (LGPD)?',
                        'answer': '''
                        <h3>Proteção de Dados no PDL</h3>
                        <p>O PDL está comprometido com a proteção dos seus dados pessoais, seguindo as diretrizes da <strong>LGPD (Lei Geral de Proteção de Dados)</strong> e outras regulamentações internacionais de privacidade.</p>
                        
                        <h4>🔒 Quais Dados Coletamos:</h4>
                        <ul>
                            <li><strong>Dados de Cadastro:</strong> Nome de usuário, e-mail, senha (criptografada)</li>
                            <li><strong>Dados de Perfil:</strong> Foto, biografia e preferências (opcional)</li>
                            <li><strong>Dados de Transação:</strong> Histórico de compras, pagamentos e transferências</li>
                            <li><strong>Dados de Acesso:</strong> Logs de login para segurança</li>
                            <li><strong>Dados de Jogo:</strong> Informações dos seus personagens no servidor</li>
                        </ul>
                        
                        <h4>🛡️ Como Protegemos seus Dados:</h4>
                        <ul>
                            <li><strong>Criptografia:</strong> Todos os dados sensíveis são criptografados</li>
                            <li><strong>HTTPS:</strong> Conexões seguras em todo o site</li>
                            <li><strong>Senhas Hash:</strong> Suas senhas nunca são armazenadas em texto puro</li>
                            <li><strong>Backups Seguros:</strong> Dados são copiados de forma segura</li>
                            <li><strong>Acesso Restrito:</strong> Apenas pessoal autorizado acessa dados sensíveis</li>
                        </ul>
                        
                        <h4>📋 Seus Direitos (LGPD):</h4>
                        <ul>
                            <li><strong>Acesso:</strong> Você pode solicitar uma cópia dos seus dados</li>
                            <li><strong>Correção:</strong> Pode corrigir dados incorretos ou desatualizados</li>
                            <li><strong>Exclusão:</strong> Pode solicitar a exclusão dos seus dados</li>
                            <li><strong>Portabilidade:</strong> Pode exportar seus dados</li>
                            <li><strong>Revogação:</strong> Pode revogar consentimentos dados anteriormente</li>
                        </ul>
                        
                        <h4>Como Exercer seus Direitos:</h4>
                        <ol>
                            <li>Acesse <strong>"Configurações → Privacidade"</strong></li>
                            <li>Ou entre em contato com nosso suporte</li>
                            <li>Responderemos em até 15 dias úteis</li>
                        </ol>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li>Nunca solicitamos sua senha por e-mail ou chat</li>
                            <li>Não compartilhamos seus dados com terceiros sem consentimento</li>
                            <li>Dados de pagamento são processados por gateways seguros (Mercado Pago, Stripe, PayPal)</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does PDL protect my personal data (GDPR/Privacy)?',
                        'answer': '''
                        <h3>Data Protection in PDL</h3>
                        <p>PDL is committed to protecting your personal data, following <strong>GDPR</strong> guidelines and other international privacy regulations.</p>
                        
                        <h4>🔒 What Data We Collect:</h4>
                        <ul>
                            <li><strong>Registration Data:</strong> Username, email, password (encrypted)</li>
                            <li><strong>Profile Data:</strong> Photo, biography and preferences (optional)</li>
                            <li><strong>Transaction Data:</strong> Purchase history, payments and transfers</li>
                            <li><strong>Access Data:</strong> Login logs for security</li>
                            <li><strong>Game Data:</strong> Your character information on the server</li>
                        </ul>
                        
                        <h4>🛡️ How We Protect Your Data:</h4>
                        <ul>
                            <li><strong>Encryption:</strong> All sensitive data is encrypted</li>
                            <li><strong>HTTPS:</strong> Secure connections throughout the site</li>
                            <li><strong>Password Hash:</strong> Your passwords are never stored in plain text</li>
                            <li><strong>Secure Backups:</strong> Data is backed up securely</li>
                            <li><strong>Restricted Access:</strong> Only authorized personnel access sensitive data</li>
                        </ul>
                        
                        <h4>📋 Your Rights:</h4>
                        <ul>
                            <li><strong>Access:</strong> You can request a copy of your data</li>
                            <li><strong>Correction:</strong> You can correct incorrect or outdated data</li>
                            <li><strong>Deletion:</strong> You can request deletion of your data</li>
                            <li><strong>Portability:</strong> You can export your data</li>
                            <li><strong>Revocation:</strong> You can revoke previously given consents</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo protege el PDL mis datos personales (RGPD)?',
                        'answer': '''
                        <h3>Protección de Datos en el PDL</h3>
                        <p>El PDL está comprometido con la protección de tus datos personales, siguiendo las directrices del <strong>RGPD</strong> y otras regulaciones internacionales de privacidad.</p>
                        
                        <h4>🔒 Qué Datos Recopilamos:</h4>
                        <ul>
                            <li><strong>Datos de Registro:</strong> Nombre de usuario, correo electrónico, contraseña (cifrada)</li>
                            <li><strong>Datos de Perfil:</strong> Foto, biografía y preferencias (opcional)</li>
                            <li><strong>Datos de Transacción:</strong> Historial de compras, pagos y transferencias</li>
                            <li><strong>Datos de Acceso:</strong> Registros de inicio de sesión para seguridad</li>
                            <li><strong>Datos de Juego:</strong> Información de tus personajes en el servidor</li>
                        </ul>
                        
                        <h4>🛡️ Cómo Protegemos tus Datos:</h4>
                        <ul>
                            <li><strong>Cifrado:</strong> Todos los datos sensibles están cifrados</li>
                            <li><strong>HTTPS:</strong> Conexiones seguras en todo el sitio</li>
                            <li><strong>Hash de Contraseñas:</strong> Tus contraseñas nunca se almacenan en texto plano</li>
                            <li><strong>Copias de Seguridad:</strong> Los datos se respaldan de forma segura</li>
                            <li><strong>Acceso Restringido:</strong> Solo personal autorizado accede a datos sensibles</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Posso solicitar a exclusão da minha conta e dados?',
                        'answer': '''
                        <h3>Exclusão de Conta e Dados</h3>
                        <p>Sim! De acordo com a LGPD, você tem o direito de solicitar a exclusão da sua conta e todos os dados associados.</p>
                        
                        <h4>Como Solicitar a Exclusão:</h4>
                        <ol>
                            <li>Acesse <strong>"Configurações → Conta → Excluir Conta"</strong></li>
                            <li>Ou envie uma solicitação para o suporte</li>
                            <li>Confirme sua identidade (pode ser necessário verificação)</li>
                            <li>Aguarde o processamento (até 15 dias úteis)</li>
                        </ol>
                        
                        <h4>⚠️ O que Acontece ao Excluir:</h4>
                        <ul>
                            <li><strong>Dados Removidos:</strong> Perfil, histórico, preferências</li>
                            <li><strong>Dados Mantidos:</strong> Registros financeiros (obrigação legal) por até 5 anos</li>
                            <li><strong>Personagens:</strong> Consulte as políticas do servidor de jogo</li>
                            <li><strong>Saldo:</strong> Deve ser zerado ou transferido antes da exclusão</li>
                        </ul>
                        
                        <h4>Importante:</h4>
                        <ul>
                            <li>A exclusão é <strong>irreversível</strong></li>
                            <li>Você perderá acesso a todos os itens e histórico</li>
                            <li>Conquistas e XP serão perdidos permanentemente</li>
                            <li>Considere exportar seus dados antes de excluir</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'Can I request deletion of my account and data?',
                        'answer': '''
                        <h3>Account and Data Deletion</h3>
                        <p>Yes! According to GDPR, you have the right to request deletion of your account and all associated data.</p>
                        
                        <h4>How to Request Deletion:</h4>
                        <ol>
                            <li>Access <strong>"Settings → Account → Delete Account"</strong></li>
                            <li>Or send a request to support</li>
                            <li>Confirm your identity (verification may be required)</li>
                            <li>Wait for processing (up to 15 business days)</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Puedo solicitar la eliminación de mi cuenta y datos?',
                        'answer': '''
                        <h3>Eliminación de Cuenta y Datos</h3>
                        <p>¡Sí! De acuerdo con el RGPD, tienes derecho a solicitar la eliminación de tu cuenta y todos los datos asociados.</p>
                        '''
                    }
                }
            },
            # ==================== SEGURANÇA DA CONTA ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ativar a Autenticação em Duas Etapas (2FA)?',
                        'answer': '''
                        <h3>Autenticação em Duas Etapas (2FA)</h3>
                        <p>O 2FA adiciona uma camada extra de segurança à sua conta, exigindo um código temporário além da sua senha.</p>
                        
                        <h4>Por que Ativar o 2FA:</h4>
                        <ul>
                            <li>Protege sua conta mesmo se a senha for comprometida</li>
                            <li>Impede acessos não autorizados</li>
                            <li>Protege seu saldo e itens</li>
                            <li>Recomendado para todos os usuários</li>
                        </ul>
                        
                        <h4>Como Ativar:</h4>
                        <ol>
                            <li>Acesse <strong>"Configurações → Segurança → 2FA"</strong></li>
                            <li>Clique em <strong>"Ativar 2FA"</strong></li>
                            <li>Baixe um aplicativo autenticador:
                                <ul>
                                    <li>Google Authenticator</li>
                                    <li>Authy</li>
                                    <li>Microsoft Authenticator</li>
                                </ul>
                            </li>
                            <li>Escaneie o QR Code com o aplicativo</li>
                            <li>Digite o código de 6 dígitos gerado</li>
                            <li>Salve os <strong>códigos de recuperação</strong> em local seguro</li>
                            <li>Pronto! O 2FA está ativado</li>
                        </ol>
                        
                        <h4>⚠️ Códigos de Recuperação:</h4>
                        <ul>
                            <li>São usados se você perder acesso ao app autenticador</li>
                            <li>Cada código só pode ser usado uma vez</li>
                            <li>Guarde em local seguro (papel, cofre de senhas)</li>
                            <li>Não compartilhe com ninguém</li>
                        </ul>
                        
                        <h4>Como Usar:</h4>
                        <ol>
                            <li>Faça login normalmente com usuário e senha</li>
                            <li>Quando solicitado, abra o app autenticador</li>
                            <li>Digite o código de 6 dígitos exibido</li>
                            <li>O código muda a cada 30 segundos</li>
                        </ol>
                        
                        <h4>Problemas com 2FA:</h4>
                        <ul>
                            <li>Se perdeu acesso ao app: use um código de recuperação</li>
                            <li>Se perdeu os códigos de recuperação: entre em contato com o suporte com verificação de identidade</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to enable Two-Factor Authentication (2FA)?',
                        'answer': '''
                        <h3>Two-Factor Authentication (2FA)</h3>
                        <p>2FA adds an extra layer of security to your account, requiring a temporary code in addition to your password.</p>
                        
                        <h4>Why Enable 2FA:</h4>
                        <ul>
                            <li>Protects your account even if password is compromised</li>
                            <li>Prevents unauthorized access</li>
                            <li>Protects your balance and items</li>
                            <li>Recommended for all users</li>
                        </ul>
                        
                        <h4>How to Enable:</h4>
                        <ol>
                            <li>Access <strong>"Settings → Security → 2FA"</strong></li>
                            <li>Click <strong>"Enable 2FA"</strong></li>
                            <li>Download an authenticator app:
                                <ul>
                                    <li>Google Authenticator</li>
                                    <li>Authy</li>
                                    <li>Microsoft Authenticator</li>
                                </ul>
                            </li>
                            <li>Scan the QR Code with the app</li>
                            <li>Enter the 6-digit code generated</li>
                            <li>Save the <strong>recovery codes</strong> in a safe place</li>
                            <li>Done! 2FA is enabled</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo activar la Autenticación en Dos Pasos (2FA)?',
                        'answer': '''
                        <h3>Autenticación en Dos Pasos (2FA)</h3>
                        <p>El 2FA agrega una capa extra de seguridad a tu cuenta, requiriendo un código temporal además de tu contraseña.</p>
                        
                        <h4>Por qué Activar el 2FA:</h4>
                        <ul>
                            <li>Protege tu cuenta incluso si la contraseña es comprometida</li>
                            <li>Evita accesos no autorizados</li>
                            <li>Protege tu saldo e ítems</li>
                            <li>Recomendado para todos los usuarios</li>
                        </ul>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'O que fazer se minha conta foi hackeada ou comprometida?',
                        'answer': '''
                        <h3>Conta Hackeada ou Comprometida</h3>
                        <p>Se você suspeita que sua conta foi acessada por terceiros, siga estes passos imediatamente:</p>
                        
                        <h4>🚨 Passos Imediatos:</h4>
                        <ol>
                            <li><strong>Troque sua senha imediatamente:</strong>
                                <ul>
                                    <li>Acesse "Configurações → Segurança → Alterar Senha"</li>
                                    <li>Use uma senha forte e única</li>
                                </ul>
                            </li>
                            <li><strong>Ative o 2FA</strong> se ainda não tiver ativado</li>
                            <li><strong>Verifique o histórico de login:</strong>
                                <ul>
                                    <li>Acesse "Configurações → Segurança → Histórico de Acesso"</li>
                                    <li>Verifique logins de IPs desconhecidos</li>
                                </ul>
                            </li>
                            <li><strong>Encerre outras sessões:</strong>
                                <ul>
                                    <li>Use "Encerrar todas as sessões" para deslogar de todos os dispositivos</li>
                                </ul>
                            </li>
                            <li><strong>Verifique transações:</strong>
                                <ul>
                                    <li>Acesse "Carteira → Histórico"</li>
                                    <li>Procure por transferências não autorizadas</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>📞 Entre em Contato com o Suporte:</h4>
                        <ul>
                            <li>Informe imediatamente sobre o ocorrido</li>
                            <li>Forneça detalhes sobre quando notou o problema</li>
                            <li>Liste transações ou alterações suspeitas</li>
                            <li>Podemos congelar temporariamente a conta para investigação</li>
                        </ul>
                        
                        <h4>🔒 Prevenção Futura:</h4>
                        <ul>
                            <li>Use senhas únicas (não reutilize senhas)</li>
                            <li>Ative o 2FA</li>
                            <li>Não compartilhe sua senha com ninguém</li>
                            <li>Cuidado com links e e-mails de phishing</li>
                            <li>Mantenha seu e-mail seguro</li>
                            <li>Use um gerenciador de senhas</li>
                        </ul>
                        
                        <h4>⚠️ Sinais de Conta Comprometida:</h4>
                        <ul>
                            <li>Logins de locais desconhecidos</li>
                            <li>Transações que você não fez</li>
                            <li>Alterações em configurações</li>
                            <li>Itens ou saldo desaparecendo</li>
                            <li>E-mails de notificação sobre ações que você não realizou</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What to do if my account was hacked or compromised?',
                        'answer': '''
                        <h3>Hacked or Compromised Account</h3>
                        <p>If you suspect your account has been accessed by third parties, follow these steps immediately:</p>
                        
                        <h4>🚨 Immediate Steps:</h4>
                        <ol>
                            <li><strong>Change your password immediately</strong></li>
                            <li><strong>Enable 2FA</strong> if not already enabled</li>
                            <li><strong>Check login history</strong></li>
                            <li><strong>End other sessions</strong></li>
                            <li><strong>Check transactions</strong></li>
                        </ol>
                        
                        <h4>📞 Contact Support:</h4>
                        <ul>
                            <li>Report the incident immediately</li>
                            <li>Provide details about when you noticed the problem</li>
                            <li>We can temporarily freeze the account for investigation</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Qué hacer si mi cuenta fue hackeada o comprometida?',
                        'answer': '''
                        <h3>Cuenta Hackeada o Comprometida</h3>
                        <p>Si sospechas que tu cuenta fue accedida por terceros, sigue estos pasos inmediatamente:</p>
                        
                        <h4>🚨 Pasos Inmediatos:</h4>
                        <ol>
                            <li><strong>Cambia tu contraseña inmediatamente</strong></li>
                            <li><strong>Activa el 2FA</strong></li>
                            <li><strong>Verifica el historial de inicio de sesión</strong></li>
                            <li><strong>Cierra otras sesiones</strong></li>
                            <li><strong>Verifica las transacciones</strong></li>
                        </ol>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como recuperar minha senha ou conta?',
                        'answer': '''
                        <h3>Recuperação de Senha e Conta</h3>
                        
                        <h4>Esqueci Minha Senha:</h4>
                        <ol>
                            <li>Acesse a página de login</li>
                            <li>Clique em <strong>"Esqueci minha senha"</strong></li>
                            <li>Digite seu e-mail cadastrado</li>
                            <li>Verifique sua caixa de entrada (e spam)</li>
                            <li>Clique no link de recuperação</li>
                            <li>Crie uma nova senha</li>
                        </ol>
                        
                        <h4>Não Recebo o E-mail de Recuperação:</h4>
                        <ul>
                            <li>Verifique a pasta de spam/lixo eletrônico</li>
                            <li>Confirme se o e-mail está correto</li>
                            <li>Aguarde alguns minutos e tente novamente</li>
                            <li>Se persistir, entre em contato com o suporte</li>
                        </ul>
                        
                        <h4>Perdi Acesso ao E-mail:</h4>
                        <ul>
                            <li>Entre em contato com o suporte</li>
                            <li>Será necessário verificação de identidade</li>
                            <li>Forneça informações da conta para comprovar propriedade</li>
                        </ul>
                        
                        <h4>Perdi Acesso ao 2FA:</h4>
                        <ul>
                            <li>Use um dos códigos de recuperação salvos</li>
                            <li>Se não tem os códigos, entre em contato com o suporte</li>
                            <li>Será necessária verificação rigorosa de identidade</li>
                        </ul>
                        
                        <h4>Conta Bloqueada:</h4>
                        <ul>
                            <li>Verifique se há e-mail informando o motivo</li>
                            <li>Entre em contato com o suporte para saber mais</li>
                            <li>Siga as instruções para desbloqueio se aplicável</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to recover my password or account?',
                        'answer': '''
                        <h3>Password and Account Recovery</h3>
                        
                        <h4>I Forgot My Password:</h4>
                        <ol>
                            <li>Go to login page</li>
                            <li>Click <strong>"Forgot password"</strong></li>
                            <li>Enter your registered email</li>
                            <li>Check your inbox (and spam)</li>
                            <li>Click the recovery link</li>
                            <li>Create a new password</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo recuperar mi contraseña o cuenta?',
                        'answer': '''
                        <h3>Recuperación de Contraseña y Cuenta</h3>
                        
                        <h4>Olvidé Mi Contraseña:</h4>
                        <ol>
                            <li>Accede a la página de inicio de sesión</li>
                            <li>Haz clic en <strong>"Olvidé mi contraseña"</strong></li>
                            <li>Ingresa tu correo electrónico registrado</li>
                            <li>Revisa tu bandeja de entrada (y spam)</li>
                            <li>Haz clic en el enlace de recuperación</li>
                            <li>Crea una nueva contraseña</li>
                        </ol>
                        '''
                    }
                }
            },
            # ==================== SUPORTE E TICKETS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como entrar em contato com o suporte?',
                        'answer': '''
                        <h3>Suporte ao Jogador</h3>
                        <p>O PDL oferece várias formas de obter ajuda quando você precisar.</p>
                        
                        <h4>📱 Canais de Suporte:</h4>
                        <ul>
                            <li><strong>Assistente IA:</strong> Disponível 24/7 para dúvidas rápidas</li>
                            <li><strong>Sistema de Tickets:</strong> Para problemas que precisam de análise</li>
                            <li><strong>FAQ:</strong> Perguntas frequentes respondidas</li>
                            <li><strong>Discord:</strong> Comunidade e suporte da comunidade</li>
                        </ul>
                        
                        <h4>Como Abrir um Ticket:</h4>
                        <ol>
                            <li>Acesse <strong>"Suporte → Abrir Ticket"</strong></li>
                            <li>Selecione a categoria do problema:
                                <ul>
                                    <li>Problemas com pagamento</li>
                                    <li>Problemas com itens/entrega</li>
                                    <li>Segurança da conta</li>
                                    <li>Bugs e erros</li>
                                    <li>Dúvidas gerais</li>
                                    <li>Denúncia</li>
                                </ul>
                            </li>
                            <li>Descreva o problema detalhadamente</li>
                            <li>Anexe prints/evidências se necessário</li>
                            <li>Envie o ticket</li>
                        </ol>
                        
                        <h4>⏰ Tempo de Resposta:</h4>
                        <ul>
                            <li><strong>Tickets urgentes (pagamento, segurança):</strong> Até 24 horas</li>
                            <li><strong>Tickets normais:</strong> Até 48 horas</li>
                            <li><strong>Tickets de baixa prioridade:</strong> Até 72 horas</li>
                        </ul>
                        
                        <h4>💡 Dicas para um Bom Ticket:</h4>
                        <ul>
                            <li>Seja claro e objetivo na descrição</li>
                            <li>Inclua todas as informações relevantes</li>
                            <li>Anexe capturas de tela quando possível</li>
                            <li>Não abra tickets duplicados</li>
                            <li>Responda as perguntas do suporte rapidamente</li>
                        </ul>
                        
                        <h4>Acompanhar Ticket:</h4>
                        <ul>
                            <li>Acesse <strong>"Suporte → Meus Tickets"</strong></li>
                            <li>Veja o status e histórico de respostas</li>
                            <li>Você receberá e-mail quando houver atualização</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to contact support?',
                        'answer': '''
                        <h3>Player Support</h3>
                        <p>PDL offers several ways to get help when you need it.</p>
                        
                        <h4>📱 Support Channels:</h4>
                        <ul>
                            <li><strong>AI Assistant:</strong> Available 24/7 for quick questions</li>
                            <li><strong>Ticket System:</strong> For issues that need analysis</li>
                            <li><strong>FAQ:</strong> Frequently asked questions answered</li>
                            <li><strong>Discord:</strong> Community and community support</li>
                        </ul>
                        
                        <h4>How to Open a Ticket:</h4>
                        <ol>
                            <li>Access <strong>"Support → Open Ticket"</strong></li>
                            <li>Select the problem category</li>
                            <li>Describe the problem in detail</li>
                            <li>Attach screenshots/evidence if necessary</li>
                            <li>Submit the ticket</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo contactar con el soporte?',
                        'answer': '''
                        <h3>Soporte al Jugador</h3>
                        <p>El PDL ofrece varias formas de obtener ayuda cuando la necesites.</p>
                        
                        <h4>📱 Canales de Soporte:</h4>
                        <ul>
                            <li><strong>Asistente IA:</strong> Disponible 24/7 para dudas rápidas</li>
                            <li><strong>Sistema de Tickets:</strong> Para problemas que necesitan análisis</li>
                            <li><strong>FAQ:</strong> Preguntas frecuentes respondidas</li>
                            <li><strong>Discord:</strong> Comunidad y soporte de la comunidad</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== CLANS E ALIANÇAS ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funcionam Clans e Alianças no PDL?',
                        'answer': '''
                        <h3>Sistema de Clans e Alianças</h3>
                        <p>O PDL integra informações dos Clans e Alianças do servidor de jogo, permitindo visualização e gestão pelo painel.</p>
                        
                        <h4>Visualizar Informações do Clan:</h4>
                        <ul>
                            <li>Acesse <strong>"Meu Clan"</strong> no menu</li>
                            <li>Veja membros, nível, pontos e estatísticas</li>
                            <li>Visualize a hierarquia do clan</li>
                            <li>Acompanhe rankings e conquistas</li>
                        </ul>
                        
                        <h4>Funcionalidades de Clan no PDL:</h4>
                        <ul>
                            <li><strong>Ranking de Clans:</strong> Veja a classificação de todos os clans</li>
                            <li><strong>Estatísticas:</strong> Pontos, membros, guerras vencidas</li>
                            <li><strong>Hall de Clans:</strong> Compre itens especiais para o clan (se disponível)</li>
                            <li><strong>Histórico:</strong> Veja histórico de batalhas e eventos</li>
                        </ul>
                        
                        <h4>Alianças:</h4>
                        <ul>
                            <li>Visualize informações da aliança do seu clan</li>
                            <li>Veja clans aliados e seus membros</li>
                            <li>Acompanhe estatísticas da aliança</li>
                        </ul>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li>A gestão de clans (convidar, expulsar, promover) é feita no jogo</li>
                            <li>O PDL apenas exibe informações sincronizadas do servidor</li>
                            <li>Algumas funcionalidades podem variar dependendo do servidor</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How do Clans and Alliances work in PDL?',
                        'answer': '''
                        <h3>Clan and Alliance System</h3>
                        <p>PDL integrates Clan and Alliance information from the game server, allowing visualization and management through the panel.</p>
                        
                        <h4>View Clan Information:</h4>
                        <ul>
                            <li>Access <strong>"My Clan"</strong> in the menu</li>
                            <li>See members, level, points and statistics</li>
                            <li>View clan hierarchy</li>
                            <li>Track rankings and achievements</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funcionan los Clanes y Alianzas en el PDL?',
                        'answer': '''
                        <h3>Sistema de Clanes y Alianzas</h3>
                        <p>El PDL integra información de los Clanes y Alianzas del servidor de juego, permitiendo visualización y gestión desde el panel.</p>
                        '''
                    }
                }
            },
            # ==================== PVP, GVG E EVENTOS ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funcionam eventos PvP e GvG no servidor?',
                        'answer': '''
                        <h3>Eventos PvP e GvG</h3>
                        <p>O servidor oferece diversos eventos de PvP (Player vs Player) e GvG (Guild vs Guild) para os jogadores.</p>
                        
                        <h4>Tipos de Eventos:</h4>
                        <ul>
                            <li><strong>Siege (Cerco):</strong> Batalhas por castelos entre clans</li>
                            <li><strong>Olympiad:</strong> Competição individual para ganhar pontos e títulos</li>
                            <li><strong>TvT (Team vs Team):</strong> Batalhas em equipe</li>
                            <li><strong>CTF (Capture the Flag):</strong> Eventos de captura de bandeira</li>
                            <li><strong>Raid Boss:</strong> Caça a bosses especiais</li>
                            <li><strong>Eventos Especiais:</strong> Eventos temáticos e sazonais</li>
                        </ul>
                        
                        <h4>Acompanhar Eventos no PDL:</h4>
                        <ul>
                            <li>Acesse <strong>"Eventos"</strong> no menu</li>
                            <li>Veja calendário de eventos programados</li>
                            <li>Confira rankings e resultados</li>
                            <li>Visualize prêmios disponíveis</li>
                        </ul>
                        
                        <h4>Rankings:</h4>
                        <ul>
                            <li><strong>Top PvP:</strong> Jogadores com mais kills</li>
                            <li><strong>Top PK:</strong> Jogadores com mais player kills</li>
                            <li><strong>Top Olympiad:</strong> Melhores no Olympiad</li>
                            <li><strong>Top Clans:</strong> Clans mais poderosos</li>
                        </ul>
                        
                        <h4>Dicas:</h4>
                        <ul>
                            <li>Fique atento aos horários dos eventos</li>
                            <li>Participe regularmente para ganhar recompensas</li>
                            <li>Junte-se a um clan para participar de GvG</li>
                            <li>Verifique as regras específicas de cada evento</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How do PvP and GvG events work on the server?',
                        'answer': '''
                        <h3>PvP and GvG Events</h3>
                        <p>The server offers various PvP (Player vs Player) and GvG (Guild vs Guild) events for players.</p>
                        
                        <h4>Event Types:</h4>
                        <ul>
                            <li><strong>Siege:</strong> Castle battles between clans</li>
                            <li><strong>Olympiad:</strong> Individual competition for points and titles</li>
                            <li><strong>TvT:</strong> Team battles</li>
                            <li><strong>CTF:</strong> Capture the flag events</li>
                            <li><strong>Raid Boss:</strong> Special boss hunting</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funcionan los eventos PvP y GvG en el servidor?',
                        'answer': '''
                        <h3>Eventos PvP y GvG</h3>
                        <p>El servidor ofrece diversos eventos de PvP (Player vs Player) y GvG (Guild vs Guild) para los jugadores.</p>
                        '''
                    }
                }
            },
            # ==================== ECONOMIA E TRADING ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona a economia e trading entre jogadores?',
                        'answer': '''
                        <h3>Economia e Trading no PDL</h3>
                        <p>O PDL oferece um sistema completo para negociações seguras entre jogadores.</p>
                        
                        <h4>Formas de Negociar:</h4>
                        <ul>
                            <li><strong>Marketplace:</strong> Compra e venda de personagens com preço fixo</li>
                            <li><strong>Leilões:</strong> Venda para o maior lance</li>
                            <li><strong>Transferências:</strong> Envie saldo diretamente para outro jogador</li>
                            <li><strong>Trade no Jogo:</strong> Negociação direta dentro do Lineage 2</li>
                        </ul>
                        
                        <h4>Moedas no Sistema:</h4>
                        <ul>
                            <li><strong>Saldo da Carteira (R$):</strong> Moeda real convertida</li>
                            <li><strong>Adena (no jogo):</strong> Moeda principal do Lineage 2</li>
                            <li><strong>Coins/Tokens:</strong> Moedas especiais do servidor (se houver)</li>
                        </ul>
                        
                        <h4>Dicas de Segurança no Trading:</h4>
                        <ul>
                            <li>Use sempre os sistemas oficiais (Marketplace, Leilão)</li>
                            <li>Evite negociações fora do sistema</li>
                            <li>Verifique a reputação do vendedor/comprador</li>
                            <li>Guarde provas de todas as transações</li>
                            <li>Não caia em golpes de "duplicação de itens"</li>
                            <li>Desconfie de ofertas muito boas para ser verdade</li>
                        </ul>
                        
                        <h4>⚠️ Golpes Comuns:</h4>
                        <ul>
                            <li>Ofertas de itens gratuitos em troca de senha</li>
                            <li>Links falsos de "promoções"</li>
                            <li>Pedidos de pagamento fora do sistema</li>
                            <li>Promessas de multiplicar seu dinheiro</li>
                        </ul>
                        
                        <h4>Em Caso de Problemas:</h4>
                        <ul>
                            <li>Abra um ticket imediatamente</li>
                            <li>Forneça todas as evidências (prints, logs)</li>
                            <li>Não tente resolver por conta própria</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does economy and trading between players work?',
                        'answer': '''
                        <h3>Economy and Trading in PDL</h3>
                        <p>PDL offers a complete system for secure negotiations between players.</p>
                        
                        <h4>Ways to Trade:</h4>
                        <ul>
                            <li><strong>Marketplace:</strong> Buy and sell at fixed price</li>
                            <li><strong>Auctions:</strong> Sell to highest bidder</li>
                            <li><strong>Transfers:</strong> Send balance directly to another player</li>
                            <li><strong>In-Game Trade:</strong> Direct negotiation within Lineage 2</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona la economía y el trading entre jugadores?',
                        'answer': '''
                        <h3>Economía y Trading en el PDL</h3>
                        <p>El PDL ofrece un sistema completo para negociaciones seguras entre jugadores.</p>
                        '''
                    }
                }
            },
            # ==================== PROBLEMAS TÉCNICOS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'O que fazer se encontrar erros ou bugs no PDL?',
                        'answer': '''
                        <h3>Reportar Erros e Bugs</h3>
                        <p>Encontrou um problema no PDL? Ajude-nos a melhorar reportando!</p>
                        
                        <h4>Problemas Comuns e Soluções:</h4>
                        <ul>
                            <li><strong>Página não carrega:</strong>
                                <ul>
                                    <li>Limpe o cache do navegador</li>
                                    <li>Tente outro navegador</li>
                                    <li>Verifique sua conexão de internet</li>
                                </ul>
                            </li>
                            <li><strong>Login não funciona:</strong>
                                <ul>
                                    <li>Verifique se caps lock está desativado</li>
                                    <li>Tente recuperar a senha</li>
                                    <li>Limpe cookies do site</li>
                                </ul>
                            </li>
                            <li><strong>Pagamento não confirmou:</strong>
                                <ul>
                                    <li>Aguarde alguns minutos</li>
                                    <li>Verifique seu e-mail</li>
                                    <li>Consulte o histórico de pagamentos</li>
                                </ul>
                            </li>
                            <li><strong>Itens não entregues:</strong>
                                <ul>
                                    <li>Verifique se o personagem está correto</li>
                                    <li>Tente logar/deslogar do personagem</li>
                                    <li>Verifique espaço no inventário</li>
                                </ul>
                            </li>
                        </ul>
                        
                        <h4>Como Reportar um Bug:</h4>
                        <ol>
                            <li>Acesse <strong>"Suporte → Reportar Bug"</strong></li>
                            <li>Descreva o problema detalhadamente:
                                <ul>
                                    <li>O que você estava fazendo</li>
                                    <li>O que esperava acontecer</li>
                                    <li>O que realmente aconteceu</li>
                                </ul>
                            </li>
                            <li>Inclua:
                                <ul>
                                    <li>Navegador e versão</li>
                                    <li>Sistema operacional</li>
                                    <li>Capturas de tela do erro</li>
                                    <li>Passos para reproduzir</li>
                                </ul>
                            </li>
                            <li>Envie o relatório</li>
                        </ol>
                        
                        <h4>⚠️ Erros Críticos:</h4>
                        <ul>
                            <li>Se encontrar uma vulnerabilidade de segurança</li>
                            <li>Entre em contato imediatamente pelo suporte</li>
                            <li>Não compartilhe publicamente a vulnerabilidade</li>
                            <li>Você pode ser recompensado por reportar responsavelmente</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What to do if I find errors or bugs in PDL?',
                        'answer': '''
                        <h3>Report Errors and Bugs</h3>
                        <p>Found a problem in PDL? Help us improve by reporting!</p>
                        
                        <h4>Common Problems and Solutions:</h4>
                        <ul>
                            <li><strong>Page doesn't load:</strong> Clear browser cache, try another browser</li>
                            <li><strong>Login doesn't work:</strong> Check caps lock, try password recovery</li>
                            <li><strong>Payment not confirmed:</strong> Wait a few minutes, check email</li>
                            <li><strong>Items not delivered:</strong> Check character, inventory space</li>
                        </ul>
                        
                        <h4>How to Report a Bug:</h4>
                        <ol>
                            <li>Access <strong>"Support → Report Bug"</strong></li>
                            <li>Describe the problem in detail</li>
                            <li>Include screenshots and steps to reproduce</li>
                            <li>Submit the report</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Qué hacer si encuentro errores o bugs en el PDL?',
                        'answer': '''
                        <h3>Reportar Errores y Bugs</h3>
                        <p>¿Encontraste un problema en el PDL? ¡Ayúdanos a mejorar reportándolo!</p>
                        
                        <h4>Problemas Comunes y Soluciones:</h4>
                        <ul>
                            <li><strong>La página no carga:</strong> Limpia la caché del navegador</li>
                            <li><strong>El inicio de sesión no funciona:</strong> Verifica caps lock</li>
                            <li><strong>El pago no se confirmó:</strong> Espera unos minutos</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== ASSISTENTE IA ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar o Assistente de IA do PDL?',
                        'answer': '''
                        <h3>Assistente de Inteligência Artificial</h3>
                        <p>O PDL conta com um assistente de IA avançado para ajudar você com dúvidas e informações sobre o sistema.</p>
                        
                        <h4>O que o Assistente Pode Fazer:</h4>
                        <ul>
                            <li>Responder dúvidas sobre o PDL e suas funcionalidades</li>
                            <li>Explicar como usar cada recurso do painel</li>
                            <li>Ajudar com problemas comuns</li>
                            <li>Fornecer informações sobre o servidor de jogo</li>
                            <li>Orientar sobre pagamentos e transações</li>
                            <li>Dar dicas de segurança</li>
                        </ul>
                        
                        <h4>Como Usar:</h4>
                        <ol>
                            <li>Clique no ícone do assistente (geralmente no canto da tela)</li>
                            <li>Digite sua pergunta ou dúvida</li>
                            <li>Aguarde a resposta</li>
                            <li>Faça perguntas de acompanhamento se necessário</li>
                        </ol>
                        
                        <h4>💡 Dicas para Melhores Respostas:</h4>
                        <ul>
                            <li>Seja específico na sua pergunta</li>
                            <li>Forneça contexto quando relevante</li>
                            <li>Pergunte uma coisa de cada vez</li>
                            <li>Use palavras-chave relacionadas ao assunto</li>
                        </ul>
                        
                        <h4>O que o Assistente NÃO Pode Fazer:</h4>
                        <ul>
                            <li>Acessar ou modificar sua conta</li>
                            <li>Fazer transações por você</li>
                            <li>Resolver problemas que precisam de análise humana</li>
                            <li>Fornecer informações confidenciais de outros jogadores</li>
                        </ul>
                        
                        <h4>⚠️ Quando Usar o Suporte Humano:</h4>
                        <ul>
                            <li>Para problemas com pagamentos não resolvidos</li>
                            <li>Questões de segurança da conta</li>
                            <li>Denúncias de jogadores</li>
                            <li>Solicitações que requerem ação administrativa</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the PDL AI Assistant?',
                        'answer': '''
                        <h3>Artificial Intelligence Assistant</h3>
                        <p>PDL has an advanced AI assistant to help you with questions and information about the system.</p>
                        
                        <h4>What the Assistant Can Do:</h4>
                        <ul>
                            <li>Answer questions about PDL and its features</li>
                            <li>Explain how to use each panel resource</li>
                            <li>Help with common problems</li>
                            <li>Provide information about the game server</li>
                            <li>Guide on payments and transactions</li>
                        </ul>
                        
                        <h4>How to Use:</h4>
                        <ol>
                            <li>Click the assistant icon</li>
                            <li>Type your question</li>
                            <li>Wait for the response</li>
                            <li>Ask follow-up questions if needed</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar el Asistente de IA del PDL?',
                        'answer': '''
                        <h3>Asistente de Inteligencia Artificial</h3>
                        <p>El PDL cuenta con un asistente de IA avanzado para ayudarte con dudas e información sobre el sistema.</p>
                        
                        <h4>Lo que el Asistente Puede Hacer:</h4>
                        <ul>
                            <li>Responder dudas sobre el PDL y sus funcionalidades</li>
                            <li>Explicar cómo usar cada recurso del panel</li>
                            <li>Ayudar con problemas comunes</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== TERMOS DE USO E REGRAS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Quais são as regras e termos de uso do PDL?',
                        'answer': '''
                        <h3>Termos de Uso e Regras</h3>
                        <p>Ao usar o PDL, você concorda em seguir nossas regras para garantir uma boa experiência para todos.</p>
                        
                        <h4>📜 Regras Gerais:</h4>
                        <ul>
                            <li><strong>Conta Pessoal:</strong> Sua conta é pessoal e intransferível</li>
                            <li><strong>Informações Verdadeiras:</strong> Forneça dados corretos no cadastro</li>
                            <li><strong>Responsabilidade:</strong> Você é responsável por todas as ações na sua conta</li>
                            <li><strong>Segurança:</strong> Mantenha suas credenciais seguras</li>
                        </ul>
                        
                        <h4>🚫 Condutas Proibidas:</h4>
                        <ul>
                            <li>Usar bots, hacks ou programas não autorizados</li>
                            <li>Explorar bugs ou glitches</li>
                            <li>Fazer chargebacks fraudulentos</li>
                            <li>Vender/comprar contas</li>
                            <li>Compartilhar conta com terceiros</li>
                            <li>Assédio ou comportamento tóxico</li>
                            <li>Spam ou propaganda não autorizada</li>
                            <li>Tentativa de fraude ou golpes</li>
                        </ul>
                        
                        <h4>⚖️ Consequências:</h4>
                        <ul>
                            <li><strong>Advertência:</strong> Para infrações leves</li>
                            <li><strong>Suspensão Temporária:</strong> Para infrações moderadas</li>
                            <li><strong>Banimento Permanente:</strong> Para infrações graves</li>
                            <li><strong>Perda de Itens/Saldo:</strong> Se obtidos de forma irregular</li>
                        </ul>
                        
                        <h4>📋 Direitos do PDL:</h4>
                        <ul>
                            <li>Modificar preços e produtos a qualquer momento</li>
                            <li>Suspender contas que violem os termos</li>
                            <li>Alterar funcionalidades do sistema</li>
                            <li>Realizar manutenções programadas ou emergenciais</li>
                        </ul>
                        
                        <h4>💼 Seus Direitos:</h4>
                        <ul>
                            <li>Acesso ao sistema enquanto em conformidade com os termos</li>
                            <li>Suporte para problemas legítimos</li>
                            <li>Proteção dos seus dados pessoais</li>
                            <li>Recurso em caso de punição</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What are the rules and terms of use of PDL?',
                        'answer': '''
                        <h3>Terms of Use and Rules</h3>
                        <p>By using PDL, you agree to follow our rules to ensure a good experience for everyone.</p>
                        
                        <h4>📜 General Rules:</h4>
                        <ul>
                            <li><strong>Personal Account:</strong> Your account is personal and non-transferable</li>
                            <li><strong>True Information:</strong> Provide correct data when registering</li>
                            <li><strong>Responsibility:</strong> You are responsible for all actions on your account</li>
                        </ul>
                        
                        <h4>🚫 Prohibited Conduct:</h4>
                        <ul>
                            <li>Using bots, hacks or unauthorized programs</li>
                            <li>Exploiting bugs or glitches</li>
                            <li>Fraudulent chargebacks</li>
                            <li>Selling/buying accounts</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cuáles son las reglas y términos de uso del PDL?',
                        'answer': '''
                        <h3>Términos de Uso y Reglas</h3>
                        <p>Al usar el PDL, aceptas seguir nuestras reglas para garantizar una buena experiencia para todos.</p>
                        
                        <h4>📜 Reglas Generales:</h4>
                        <ul>
                            <li><strong>Cuenta Personal:</strong> Tu cuenta es personal e intransferible</li>
                            <li><strong>Información Verdadera:</strong> Proporciona datos correctos al registrarte</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== REEMBOLSO E CANCELAMENTO ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funcionam reembolsos e cancelamentos?',
                        'answer': '''
                        <h3>Política de Reembolso e Cancelamento</h3>
                        <p>Entenda como funcionam os reembolsos e cancelamentos no PDL.</p>
                        
                        <h4>💰 Reembolso de Saldo Não Utilizado:</h4>
                        <ul>
                            <li>Saldo adicionado à carteira pode ser reembolsado se não foi utilizado</li>
                            <li>Solicite através do suporte</li>
                            <li>Sujeito a taxa de processamento</li>
                            <li>Prazo de até 30 dias para processamento</li>
                        </ul>
                        
                        <h4>🛒 Reembolso de Compras:</h4>
                        <ul>
                            <li><strong>Antes da Entrega:</strong> Reembolso integral possível</li>
                            <li><strong>Após Entrega:</strong> Geralmente não é possível reembolsar</li>
                            <li><strong>Itens com Defeito:</strong> Substituição ou crédito</li>
                            <li><strong>Erro do Sistema:</strong> Reembolso ou correção</li>
                        </ul>
                        
                        <h4>❌ Casos SEM Reembolso:</h4>
                        <ul>
                            <li>Itens já utilizados ou equipados</li>
                            <li>Saldo transferido para outros jogadores</li>
                            <li>Saldo transferido para personagens no jogo</li>
                            <li>Compras em promoções (salvo erro do sistema)</li>
                            <li>Após 7 dias da compra (para itens digitais)</li>
                            <li>Contas banidas por violação de regras</li>
                        </ul>
                        
                        <h4>Como Solicitar Reembolso:</h4>
                        <ol>
                            <li>Acesse <strong>"Suporte → Abrir Ticket"</strong></li>
                            <li>Selecione <strong>"Reembolso"</strong> como categoria</li>
                            <li>Forneça:
                                <ul>
                                    <li>Número da transação/compra</li>
                                    <li>Motivo do reembolso</li>
                                    <li>Comprovantes se necessário</li>
                                </ul>
                            </li>
                            <li>Aguarde análise (até 7 dias úteis)</li>
                        </ol>
                        
                        <h4>📋 Cancelamento de Serviços:</h4>
                        <ul>
                            <li>Assinaturas podem ser canceladas a qualquer momento</li>
                            <li>O acesso continua até o fim do período pago</li>
                            <li>Não há reembolso proporcional do período restante</li>
                        </ul>
                        
                        <h4>⚠️ Chargebacks:</h4>
                        <ul>
                            <li>Fazer chargeback sem contatar o suporte primeiro resultará em banimento</li>
                            <li>Sempre tente resolver pelo suporte antes</li>
                            <li>Chargebacks fraudulentos serão reportados</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How do refunds and cancellations work?',
                        'answer': '''
                        <h3>Refund and Cancellation Policy</h3>
                        <p>Understand how refunds and cancellations work in PDL.</p>
                        
                        <h4>💰 Refund of Unused Balance:</h4>
                        <ul>
                            <li>Balance added to wallet can be refunded if not used</li>
                            <li>Request through support</li>
                            <li>Subject to processing fee</li>
                        </ul>
                        
                        <h4>🛒 Purchase Refunds:</h4>
                        <ul>
                            <li><strong>Before Delivery:</strong> Full refund possible</li>
                            <li><strong>After Delivery:</strong> Generally not refundable</li>
                            <li><strong>Defective Items:</strong> Replacement or credit</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funcionan los reembolsos y cancelaciones?',
                        'answer': '''
                        <h3>Política de Reembolso y Cancelación</h3>
                        <p>Entiende cómo funcionan los reembolsos y cancelaciones en el PDL.</p>
                        
                        <h4>💰 Reembolso de Saldo No Utilizado:</h4>
                        <ul>
                            <li>El saldo agregado a la billetera puede ser reembolsado si no fue utilizado</li>
                            <li>Solicita a través del soporte</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== DOAÇÕES E VIP ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona o sistema de VIP ou doações?',
                        'answer': '''
                        <h3>Sistema VIP e Doações</h3>
                        <p>O PDL pode oferecer sistemas de VIP ou doações dependendo da configuração do servidor.</p>
                        
                        <h4>Benefícios VIP (podem variar):</h4>
                        <ul>
                            <li>Bônus de experiência no jogo</li>
                            <li>Acesso a áreas exclusivas</li>
                            <li>Itens especiais</li>
                            <li>Descontos na loja</li>
                            <li>Suporte prioritário</li>
                            <li>Distintivos e títulos exclusivos</li>
                        </ul>
                        
                        <h4>Como Adquirir VIP:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"VIP"</strong> ou <strong>"Doações"</strong></li>
                            <li>Escolha o plano desejado</li>
                            <li>Selecione o período (mensal, trimestral, anual)</li>
                            <li>Complete o pagamento</li>
                            <li>Benefícios são ativados automaticamente</li>
                        </ol>
                        
                        <h4>Duração e Renovação:</h4>
                        <ul>
                            <li>VIP tem duração determinada (dias)</li>
                            <li>Pode ser renovado antes do vencimento</li>
                            <li>Benefícios expiram após o período</li>
                            <li>Alguns itens VIP são permanentes</li>
                        </ul>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li>VIP não garante vantagens em PvP (depende do servidor)</li>
                            <li>Benefícios podem mudar com atualizações</li>
                            <li>Consulte as regras específicas do servidor</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does the VIP or donation system work?',
                        'answer': '''
                        <h3>VIP and Donation System</h3>
                        <p>PDL may offer VIP or donation systems depending on server configuration.</p>
                        
                        <h4>VIP Benefits (may vary):</h4>
                        <ul>
                            <li>Experience bonus in game</li>
                            <li>Access to exclusive areas</li>
                            <li>Special items</li>
                            <li>Store discounts</li>
                            <li>Priority support</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona el sistema VIP o donaciones?',
                        'answer': '''
                        <h3>Sistema VIP y Donaciones</h3>
                        <p>El PDL puede ofrecer sistemas VIP o donaciones dependiendo de la configuración del servidor.</p>
                        '''
                    }
                }
            },
            # ==================== CLASSES E BUILDS ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Onde posso encontrar informações sobre classes e builds?',
                        'answer': '''
                        <h3>Classes e Builds no Lineage 2</h3>
                        <p>Informações sobre classes e builds podem ser encontradas em várias fontes.</p>
                        
                        <h4>No PDL:</h4>
                        <ul>
                            <li>Acesse a seção <strong>"Wiki"</strong> ou <strong>"Guias"</strong> se disponível</li>
                            <li>Consulte o fórum da comunidade</li>
                            <li>Pergunte no Discord do servidor</li>
                        </ul>
                        
                        <h4>Classes Principais:</h4>
                        <ul>
                            <li><strong>Guerreiros:</strong> Gladiador, Warlord, Paladin, Dark Avenger, etc.</li>
                            <li><strong>Arqueiros:</strong> Hawkeye, Silver Ranger, Phantom Ranger, etc.</li>
                            <li><strong>Magos:</strong> Sorcerer, Necromancer, Spellhowler, etc.</li>
                            <li><strong>Suportes:</strong> Bishop, Elder, Shillien Elder, etc.</li>
                            <li><strong>Summoners:</strong> Warlock, Elemental Summoner, Phantom Summoner</li>
                            <li><strong>Outras:</strong> Dagger classes, Tanks, etc.</li>
                        </ul>
                        
                        <h4>Dicas para Escolher uma Classe:</h4>
                        <ul>
                            <li>Considere seu estilo de jogo (solo, grupo, PvP)</li>
                            <li>Pesquise sobre as classes mais fortes na crônica do servidor</li>
                            <li>Consulte jogadores experientes</li>
                            <li>Teste diferentes classes antes de investir muito</li>
                        </ul>
                        
                        <h4>Builds e Equipamentos:</h4>
                        <ul>
                            <li>Builds variam muito dependendo da crônica</li>
                            <li>Consulte guias específicos para a versão do servidor</li>
                            <li>A loja pode ter itens recomendados para cada classe</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'Where can I find information about classes and builds?',
                        'answer': '''
                        <h3>Classes and Builds in Lineage 2</h3>
                        <p>Information about classes and builds can be found from various sources.</p>
                        
                        <h4>In PDL:</h4>
                        <ul>
                            <li>Access the <strong>"Wiki"</strong> or <strong>"Guides"</strong> section if available</li>
                            <li>Check the community forum</li>
                            <li>Ask on the server Discord</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Dónde puedo encontrar información sobre clases y builds?',
                        'answer': '''
                        <h3>Clases y Builds en Lineage 2</h3>
                        <p>La información sobre clases y builds se puede encontrar en varias fuentes.</p>
                        '''
                    }
                }
            },
            # ==================== NOTIFICAÇÕES ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como configurar notificações no PDL?',
                        'answer': '''
                        <h3>Configurações de Notificação</h3>
                        <p>O PDL pode enviar notificações importantes sobre sua conta e atividades.</p>
                        
                        <h4>Tipos de Notificações:</h4>
                        <ul>
                            <li><strong>E-mail:</strong> Pagamentos, segurança, atualizações</li>
                            <li><strong>Push (navegador):</strong> Alertas em tempo real</li>
                            <li><strong>No painel:</strong> Notificações internas do sistema</li>
                        </ul>
                        
                        <h4>Como Configurar:</h4>
                        <ol>
                            <li>Acesse <strong>"Configurações → Notificações"</strong></li>
                            <li>Escolha quais notificações deseja receber:
                                <ul>
                                    <li>Pagamentos confirmados</li>
                                    <li>Entregas de itens</li>
                                    <li>Lances em leilões</li>
                                    <li>Alertas de segurança</li>
                                    <li>Promoções e ofertas</li>
                                    <li>Atualizações do sistema</li>
                                </ul>
                            </li>
                            <li>Salve as preferências</li>
                        </ol>
                        
                        <h4>⚠️ Notificações Importantes:</h4>
                        <ul>
                            <li>Alertas de segurança não podem ser desativados</li>
                            <li>Confirmações de pagamento são sempre enviadas</li>
                            <li>Mantenha seu e-mail atualizado para receber notificações</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to configure notifications in PDL?',
                        'answer': '''
                        <h3>Notification Settings</h3>
                        <p>PDL can send important notifications about your account and activities.</p>
                        
                        <h4>Notification Types:</h4>
                        <ul>
                            <li><strong>Email:</strong> Payments, security, updates</li>
                            <li><strong>Push (browser):</strong> Real-time alerts</li>
                            <li><strong>In panel:</strong> Internal system notifications</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo configurar notificaciones en el PDL?',
                        'answer': '''
                        <h3>Configuración de Notificaciones</h3>
                        <p>El PDL puede enviar notificaciones importantes sobre tu cuenta y actividades.</p>
                        '''
                    }
                }
            },
            # ==================== IDIOMAS E LOCALIZAÇÃO ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Posso mudar o idioma do PDL?',
                        'answer': '''
                        <h3>Idiomas Disponíveis</h3>
                        <p>O PDL está disponível em múltiplos idiomas para melhor atender jogadores de diferentes países.</p>
                        
                        <h4>Idiomas Suportados:</h4>
                        <ul>
                            <li>🇧🇷 Português (Brasil) - Padrão</li>
                            <li>🇺🇸 English (Inglês)</li>
                            <li>🇪🇸 Español (Espanhol)</li>
                        </ul>
                        
                        <h4>Como Mudar o Idioma:</h4>
                        <ol>
                            <li>Procure o seletor de idioma (geralmente no menu ou rodapé)</li>
                            <li>Clique no ícone da bandeira ou nome do idioma</li>
                            <li>Selecione o idioma desejado</li>
                            <li>A página será atualizada no novo idioma</li>
                        </ol>
                        
                        <h4>Observações:</h4>
                        <ul>
                            <li>Sua preferência de idioma é salva automaticamente</li>
                            <li>Alguns conteúdos podem estar apenas em Português</li>
                            <li>O suporte ao cliente está disponível principalmente em Português</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'Can I change the PDL language?',
                        'answer': '''
                        <h3>Available Languages</h3>
                        <p>PDL is available in multiple languages to better serve players from different countries.</p>
                        
                        <h4>Supported Languages:</h4>
                        <ul>
                            <li>🇧🇷 Portuguese (Brazil) - Default</li>
                            <li>🇺🇸 English</li>
                            <li>🇪🇸 Spanish</li>
                        </ul>
                        
                        <h4>How to Change Language:</h4>
                        <ol>
                            <li>Look for the language selector (usually in menu or footer)</li>
                            <li>Click the flag icon or language name</li>
                            <li>Select desired language</li>
                            <li>Page will be updated in new language</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Puedo cambiar el idioma del PDL?',
                        'answer': '''
                        <h3>Idiomas Disponibles</h3>
                        <p>El PDL está disponible en múltiples idiomas para atender mejor a jugadores de diferentes países.</p>
                        
                        <h4>Idiomas Soportados:</h4>
                        <ul>
                            <li>🇧🇷 Portugués (Brasil) - Predeterminado</li>
                            <li>🇺🇸 Inglés</li>
                            <li>🇪🇸 Español</li>
                        </ul>
                        '''
                    }
                }
            },
            # ==================== MOBILE E RESPONSIVIDADE ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Posso acessar o PDL pelo celular?',
                        'answer': '''
                        <h3>Acesso Mobile</h3>
                        <p>Sim! O PDL foi desenvolvido com design responsivo e funciona perfeitamente em dispositivos móveis.</p>
                        
                        <h4>📱 Funciona em:</h4>
                        <ul>
                            <li>Smartphones (Android e iOS)</li>
                            <li>Tablets</li>
                            <li>Qualquer navegador moderno</li>
                        </ul>
                        
                        <h4>Funcionalidades Disponíveis no Mobile:</h4>
                        <ul>
                            <li>✅ Login e gerenciamento de conta</li>
                            <li>✅ Visualização de personagens</li>
                            <li>✅ Compras na loja</li>
                            <li>✅ Pagamentos</li>
                            <li>✅ Transferências</li>
                            <li>✅ Leilões e Marketplace</li>
                            <li>✅ Minigames</li>
                            <li>✅ Suporte e tickets</li>
                            <li>✅ Assistente IA</li>
                        </ul>
                        
                        <h4>Dicas para Melhor Experiência:</h4>
                        <ul>
                            <li>Use a versão mais recente do navegador</li>
                            <li>Mantenha o navegador atualizado</li>
                            <li>Use Wi-Fi para operações importantes</li>
                            <li>Você pode adicionar à tela inicial como um app</li>
                        </ul>
                        
                        <h4>Adicionar à Tela Inicial:</h4>
                        <ol>
                            <li>Acesse o PDL pelo navegador</li>
                            <li>No menu do navegador, selecione "Adicionar à tela inicial"</li>
                            <li>O PDL ficará como um ícone de app no seu celular</li>
                        </ol>
                        '''
                    },
                    'en': {
                        'question': 'Can I access PDL on my phone?',
                        'answer': '''
                        <h3>Mobile Access</h3>
                        <p>Yes! PDL was developed with responsive design and works perfectly on mobile devices.</p>
                        
                        <h4>📱 Works on:</h4>
                        <ul>
                            <li>Smartphones (Android and iOS)</li>
                            <li>Tablets</li>
                            <li>Any modern browser</li>
                        </ul>
                        
                        <h4>Features Available on Mobile:</h4>
                        <ul>
                            <li>✅ Login and account management</li>
                            <li>✅ Character viewing</li>
                            <li>✅ Store purchases</li>
                            <li>✅ Payments</li>
                            <li>✅ Transfers</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Puedo acceder al PDL desde mi celular?',
                        'answer': '''
                        <h3>Acceso Móvil</h3>
                        <p>¡Sí! El PDL fue desarrollado con diseño responsivo y funciona perfectamente en dispositivos móviles.</p>
                        '''
                    }
                }
            },
            # ==================== BONUS: DICAS GERAIS ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Quais são as melhores dicas para novos jogadores?',
                        'answer': '''
                        <h3>Dicas para Novos Jogadores</h3>
                        <p>Bem-vindo ao PDL! Aqui estão algumas dicas para começar bem sua jornada.</p>
                        
                        <h4>🎯 Primeiros Passos:</h4>
                        <ol>
                            <li><strong>Configure sua conta:</strong>
                                <ul>
                                    <li>Ative o 2FA para segurança</li>
                                    <li>Complete seu perfil</li>
                                    <li>Verifique seu e-mail</li>
                                </ul>
                            </li>
                            <li><strong>Explore o painel:</strong>
                                <ul>
                                    <li>Conheça todas as funcionalidades</li>
                                    <li>Leia as FAQs</li>
                                    <li>Use o assistente IA para dúvidas</li>
                                </ul>
                            </li>
                            <li><strong>Vincule seus personagens:</strong>
                                <ul>
                                    <li>Verifique se seus chars aparecem no painel</li>
                                    <li>Selecione um char principal para entregas</li>
                                </ul>
                            </li>
                        </ol>
                        
                        <h4>💡 Dicas de Economia:</h4>
                        <ul>
                            <li>Aproveite promoções e ofertas especiais</li>
                            <li>Compare preços antes de comprar</li>
                            <li>Use a carteira para ter saldo disponível</li>
                            <li>Participe de eventos para ganhar itens grátis</li>
                        </ul>
                        
                        <h4>🔒 Dicas de Segurança:</h4>
                        <ul>
                            <li>Nunca compartilhe sua senha</li>
                            <li>Ative autenticação em duas etapas</li>
                            <li>Cuidado com links suspeitos</li>
                            <li>Use senhas fortes e únicas</li>
                        </ul>
                        
                        <h4>🎮 Dicas de Jogo:</h4>
                        <ul>
                            <li>Junte-se a um clan para mais conteúdo</li>
                            <li>Participe de eventos do servidor</li>
                            <li>Consulte guias e tutoriais da comunidade</li>
                            <li>Não tenha pressa, aproveite a jornada</li>
                        </ul>
                        
                        <h4>❓ Precisa de Ajuda?</h4>
                        <ul>
                            <li>Use o assistente IA para perguntas rápidas</li>
                            <li>Abra um ticket para problemas complexos</li>
                            <li>Participe do Discord da comunidade</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What are the best tips for new players?',
                        'answer': '''
                        <h3>Tips for New Players</h3>
                        <p>Welcome to PDL! Here are some tips to start your journey well.</p>
                        
                        <h4>🎯 First Steps:</h4>
                        <ol>
                            <li>Set up your account (enable 2FA, complete profile)</li>
                            <li>Explore the panel</li>
                            <li>Link your characters</li>
                        </ol>
                        
                        <h4>💡 Economy Tips:</h4>
                        <ul>
                            <li>Take advantage of promotions</li>
                            <li>Compare prices before buying</li>
                            <li>Participate in events for free items</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cuáles son los mejores consejos para nuevos jugadores?',
                        'answer': '''
                        <h3>Consejos para Nuevos Jugadores</h3>
                        <p>¡Bienvenido al PDL! Aquí hay algunos consejos para comenzar bien tu viaje.</p>
                        '''
                    }
                }
            },
            # ==================== NAVEGAÇÃO E USO DO SITE ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como navegar pelo menu e encontrar o que preciso no PDL?',
                        'answer': '''
                        <h3>Navegação no PDL</h3>
                        <p>O PDL possui um menu intuitivo para você encontrar tudo o que precisa rapidamente.</p>
                        
                        <h4>📍 Menu Principal:</h4>
                        <ul>
                            <li><strong>🏠 Início/Dashboard:</strong> Visão geral da sua conta, saldo, personagens e atividades recentes</li>
                            <li><strong>🛒 Loja:</strong> Compre itens, pacotes e serviços</li>
                            <li><strong>💰 Carteira:</strong> Gerencie seu saldo, faça transferências e veja histórico</li>
                            <li><strong>👤 Perfil:</strong> Suas informações, conquistas e configurações</li>
                            <li><strong>🎮 Personagens:</strong> Veja e gerencie seus personagens do jogo</li>
                            <li><strong>🔨 Leilões:</strong> Participe de leilões de itens</li>
                            <li><strong>🏪 Marketplace:</strong> Compre e venda com outros jogadores</li>
                            <li><strong>🎲 Minigames:</strong> Jogos e diversão com prêmios</li>
                            <li><strong>📊 Rankings:</strong> Veja os melhores jogadores e clans</li>
                            <li><strong>❓ Suporte:</strong> Ajuda, FAQ e tickets</li>
                        </ul>
                        
                        <h4>🔍 Barra de Busca:</h4>
                        <ul>
                            <li>Use a barra de busca no topo para encontrar itens rapidamente</li>
                            <li>Digite o nome do item ou categoria</li>
                            <li>Os resultados aparecem instantaneamente</li>
                        </ul>
                        
                        <h4>📱 Menu no Celular:</h4>
                        <ul>
                            <li>Clique no ícone de menu (☰) para abrir o menu lateral</li>
                            <li>Todas as opções estão disponíveis no menu móvel</li>
                            <li>Deslize para navegar entre seções</li>
                        </ul>
                        
                        <h4>⚡ Atalhos Úteis:</h4>
                        <ul>
                            <li>Clique no logo para voltar ao início</li>
                            <li>O ícone do carrinho mostra quantos itens você tem</li>
                            <li>O sino mostra suas notificações</li>
                            <li>Seu avatar leva às configurações da conta</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to navigate the menu and find what I need in PDL?',
                        'answer': '''
                        <h3>Navigation in PDL</h3>
                        <p>PDL has an intuitive menu to help you find everything you need quickly.</p>
                        
                        <h4>📍 Main Menu:</h4>
                        <ul>
                            <li><strong>🏠 Home/Dashboard:</strong> Overview of your account, balance, characters and recent activities</li>
                            <li><strong>🛒 Store:</strong> Buy items, packages and services</li>
                            <li><strong>💰 Wallet:</strong> Manage balance, make transfers and view history</li>
                            <li><strong>👤 Profile:</strong> Your info, achievements and settings</li>
                            <li><strong>🎮 Characters:</strong> View and manage your game characters</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo navegar por el menú y encontrar lo que necesito en el PDL?',
                        'answer': '''
                        <h3>Navegación en el PDL</h3>
                        <p>El PDL tiene un menú intuitivo para que encuentres todo lo que necesitas rápidamente.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'O que é o Dashboard e como usar?',
                        'answer': '''
                        <h3>Dashboard - Sua Página Inicial</h3>
                        <p>O Dashboard é a primeira página que você vê ao fazer login. Ele mostra um resumo completo da sua conta.</p>
                        
                        <h4>📊 O que você encontra no Dashboard:</h4>
                        <ul>
                            <li><strong>Saldo da Carteira:</strong> Quanto dinheiro você tem disponível</li>
                            <li><strong>Personagens:</strong> Lista dos seus personagens e status (online/offline)</li>
                            <li><strong>Atividades Recentes:</strong> Últimas compras, transferências e ações</li>
                            <li><strong>Notificações:</strong> Avisos importantes sobre sua conta</li>
                            <li><strong>Promoções:</strong> Ofertas especiais e descontos ativos</li>
                            <li><strong>Eventos:</strong> Eventos do servidor em andamento</li>
                        </ul>
                        
                        <h4>🎯 Cards e Widgets:</h4>
                        <ul>
                            <li><strong>Card de Saldo:</strong> Mostra seu saldo atual e botão para adicionar mais</li>
                            <li><strong>Card de Personagens:</strong> Seus chars com nível e classe</li>
                            <li><strong>Card de Conquistas:</strong> Progresso nas conquistas e XP</li>
                            <li><strong>Card de Compras:</strong> Últimas compras realizadas</li>
                        </ul>
                        
                        <h4>⚡ Ações Rápidas:</h4>
                        <ul>
                            <li>Clique em "Adicionar Saldo" para recarregar a carteira</li>
                            <li>Clique em um personagem para ver detalhes</li>
                            <li>Clique em uma transação para ver detalhes completos</li>
                            <li>Use os botões de ação rápida para ir direto às seções</li>
                        </ul>
                        
                        <h4>🔄 Atualização:</h4>
                        <ul>
                            <li>O Dashboard atualiza automaticamente</li>
                            <li>Você pode clicar em "Atualizar" para forçar atualização</li>
                            <li>Dados de personagens sincronizam com o servidor de jogo</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What is the Dashboard and how to use it?',
                        'answer': '''
                        <h3>Dashboard - Your Home Page</h3>
                        <p>The Dashboard is the first page you see when you log in. It shows a complete summary of your account.</p>
                        
                        <h4>📊 What you find on Dashboard:</h4>
                        <ul>
                            <li><strong>Wallet Balance:</strong> How much money you have available</li>
                            <li><strong>Characters:</strong> List of your characters and status</li>
                            <li><strong>Recent Activities:</strong> Latest purchases, transfers and actions</li>
                            <li><strong>Notifications:</strong> Important notices about your account</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Qué es el Dashboard y cómo usarlo?',
                        'answer': '''
                        <h3>Dashboard - Tu Página de Inicio</h3>
                        <p>El Dashboard es la primera página que ves al iniciar sesión. Muestra un resumen completo de tu cuenta.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver meu histórico de transações e compras?',
                        'answer': '''
                        <h3>Histórico de Transações</h3>
                        <p>O PDL mantém um registro completo de todas as suas transações para sua segurança e controle.</p>
                        
                        <h4>📋 Onde Encontrar:</h4>
                        <ul>
                            <li><strong>Carteira → Histórico:</strong> Todas as movimentações financeiras</li>
                            <li><strong>Loja → Minhas Compras:</strong> Histórico de compras na loja</li>
                            <li><strong>Leilões → Meus Leilões:</strong> Leilões que você participou</li>
                            <li><strong>Marketplace → Minhas Vendas:</strong> Suas vendas no marketplace</li>
                        </ul>
                        
                        <h4>💰 Tipos de Transações na Carteira:</h4>
                        <ul>
                            <li><strong>Depósito:</strong> Quando você adiciona saldo (pagamento)</li>
                            <li><strong>Compra:</strong> Quando você compra algo na loja</li>
                            <li><strong>Transferência Enviada:</strong> Quando você envia para outro jogador</li>
                            <li><strong>Transferência Recebida:</strong> Quando você recebe de outro jogador</li>
                            <li><strong>Transferência para Jogo:</strong> Quando envia para personagem</li>
                            <li><strong>Prêmio:</strong> Quando ganha em minigames ou eventos</li>
                            <li><strong>Reembolso:</strong> Quando recebe um reembolso</li>
                        </ul>
                        
                        <h4>🔍 Filtros Disponíveis:</h4>
                        <ul>
                            <li><strong>Por Data:</strong> Selecione período específico</li>
                            <li><strong>Por Tipo:</strong> Filtre por tipo de transação</li>
                            <li><strong>Por Valor:</strong> Busque por faixa de valores</li>
                            <li><strong>Por Status:</strong> Pendente, Concluído, Cancelado</li>
                        </ul>
                        
                        <h4>📄 Detalhes da Transação:</h4>
                        <ul>
                            <li>Clique em qualquer transação para ver detalhes</li>
                            <li>Veja data, hora, valor e descrição</li>
                            <li>Baixe comprovante/recibo se necessário</li>
                            <li>Veja ID da transação para referência no suporte</li>
                        </ul>
                        
                        <h4>📥 Exportar Histórico:</h4>
                        <ul>
                            <li>Use o botão "Exportar" para baixar seu histórico</li>
                            <li>Disponível em formato CSV ou PDF</li>
                            <li>Útil para controle pessoal ou declarações</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to view my transaction and purchase history?',
                        'answer': '''
                        <h3>Transaction History</h3>
                        <p>PDL keeps a complete record of all your transactions for your security and control.</p>
                        
                        <h4>📋 Where to Find:</h4>
                        <ul>
                            <li><strong>Wallet → History:</strong> All financial movements</li>
                            <li><strong>Store → My Purchases:</strong> Store purchase history</li>
                            <li><strong>Auctions → My Auctions:</strong> Auctions you participated in</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver mi historial de transacciones y compras?',
                        'answer': '''
                        <h3>Historial de Transacciones</h3>
                        <p>El PDL mantiene un registro completo de todas tus transacciones para tu seguridad y control.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como verificar se meus itens foram entregues?',
                        'answer': '''
                        <h3>Verificar Entrega de Itens</h3>
                        <p>Após uma compra, você pode acompanhar o status da entrega dos seus itens.</p>
                        
                        <h4>📦 Status de Entrega:</h4>
                        <ul>
                            <li><strong>🟡 Pendente:</strong> Aguardando confirmação do pagamento</li>
                            <li><strong>🔵 Processando:</strong> Pagamento confirmado, preparando entrega</li>
                            <li><strong>🟢 Entregue:</strong> Itens enviados para o personagem</li>
                            <li><strong>🔴 Falhou:</strong> Problema na entrega (verifique inventário cheio)</li>
                        </ul>
                        
                        <h4>🔍 Onde Verificar:</h4>
                        <ol>
                            <li>Acesse <strong>"Loja → Minhas Compras"</strong></li>
                            <li>Encontre a compra na lista</li>
                            <li>Veja o status de cada item</li>
                            <li>Clique para ver detalhes completos</li>
                        </ol>
                        
                        <h4>✅ Confirmar Recebimento no Jogo:</h4>
                        <ol>
                            <li>Entre no jogo com o personagem selecionado</li>
                            <li>Verifique seu inventário</li>
                            <li>Os itens devem aparecer lá</li>
                            <li>Se estava offline, os itens chegam ao logar</li>
                        </ol>
                        
                        <h4>⚠️ Itens Não Chegaram?</h4>
                        <ul>
                            <li><strong>Verifique o personagem:</strong> Confirmou que selecionou o personagem correto?</li>
                            <li><strong>Verifique o inventário:</strong> Tem espaço suficiente?</li>
                            <li><strong>Verifique o peso:</strong> O personagem suporta o peso?</li>
                            <li><strong>Relogue o personagem:</strong> Saia e entre novamente</li>
                            <li><strong>Aguarde alguns minutos:</strong> Pode haver delay de sincronização</li>
                            <li><strong>Verifique o warehouse:</strong> Alguns itens vão para o armazém</li>
                        </ul>
                        
                        <h4>🎫 Abrir Ticket:</h4>
                        <p>Se após verificar tudo os itens ainda não chegaram:</p>
                        <ol>
                            <li>Acesse <strong>"Suporte → Abrir Ticket"</strong></li>
                            <li>Selecione "Problema com Entrega"</li>
                            <li>Informe o número da compra</li>
                            <li>Descreva o problema</li>
                            <li>Anexe prints se possível</li>
                        </ol>
                        '''
                    },
                    'en': {
                        'question': 'How to verify if my items were delivered?',
                        'answer': '''
                        <h3>Verify Item Delivery</h3>
                        <p>After a purchase, you can track the delivery status of your items.</p>
                        
                        <h4>📦 Delivery Status:</h4>
                        <ul>
                            <li><strong>🟡 Pending:</strong> Waiting for payment confirmation</li>
                            <li><strong>🔵 Processing:</strong> Payment confirmed, preparing delivery</li>
                            <li><strong>🟢 Delivered:</strong> Items sent to character</li>
                            <li><strong>🔴 Failed:</strong> Delivery problem (check full inventory)</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo verificar si mis ítems fueron entregados?',
                        'answer': '''
                        <h3>Verificar Entrega de Ítems</h3>
                        <p>Después de una compra, puedes rastrear el estado de entrega de tus ítems.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar a busca e filtros na loja?',
                        'answer': '''
                        <h3>Busca e Filtros na Loja</h3>
                        <p>A loja possui ferramentas poderosas para você encontrar exatamente o que procura.</p>
                        
                        <h4>🔍 Barra de Busca:</h4>
                        <ul>
                            <li>Digite o nome do item (ex: "Sword", "Top Grade")</li>
                            <li>Resultados aparecem enquanto você digita</li>
                            <li>Busca por nome, descrição e categoria</li>
                            <li>Não precisa digitar o nome completo</li>
                        </ul>
                        
                        <h4>📁 Categorias:</h4>
                        <ul>
                            <li><strong>Armas:</strong> Espadas, arcos, adagas, etc.</li>
                            <li><strong>Armaduras:</strong> Sets, peças individuais</li>
                            <li><strong>Acessórios:</strong> Jóias, cintos, capas</li>
                            <li><strong>Consumíveis:</strong> Poções, scrolls, buffs</li>
                            <li><strong>Pacotes:</strong> Combos com vários itens</li>
                            <li><strong>Serviços:</strong> Mudança de nome, aparência, etc.</li>
                            <li><strong>VIP:</strong> Assinaturas e benefícios</li>
                        </ul>
                        
                        <h4>🎛️ Filtros Avançados:</h4>
                        <ul>
                            <li><strong>Preço:</strong> Defina faixa mínima e máxima</li>
                            <li><strong>Grade:</strong> No Grade, D, C, B, A, S, S80, S84</li>
                            <li><strong>Tipo:</strong> Específico por categoria</li>
                            <li><strong>Disponibilidade:</strong> Em estoque, esgotado</li>
                            <li><strong>Promoção:</strong> Apenas itens em oferta</li>
                        </ul>
                        
                        <h4>📊 Ordenação:</h4>
                        <ul>
                            <li>Por preço (menor/maior)</li>
                            <li>Por nome (A-Z, Z-A)</li>
                            <li>Por popularidade (mais vendidos)</li>
                            <li>Por novidade (mais recentes)</li>
                            <li>Por desconto (maiores descontos)</li>
                        </ul>
                        
                        <h4>💡 Dicas de Busca:</h4>
                        <ul>
                            <li>Use palavras-chave específicas</li>
                            <li>Combine filtros para resultados precisos</li>
                            <li>Salve buscas frequentes nos favoritos</li>
                            <li>Verifique a seção "Promoções" regularmente</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use search and filters in the store?',
                        'answer': '''
                        <h3>Search and Filters in Store</h3>
                        <p>The store has powerful tools to help you find exactly what you're looking for.</p>
                        
                        <h4>🔍 Search Bar:</h4>
                        <ul>
                            <li>Type the item name</li>
                            <li>Results appear as you type</li>
                            <li>Searches name, description and category</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar la búsqueda y filtros en la tienda?',
                        'answer': '''
                        <h3>Búsqueda y Filtros en la Tienda</h3>
                        <p>La tienda tiene herramientas poderosas para que encuentres exactamente lo que buscas.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar o carrinho de compras?',
                        'answer': '''
                        <h3>Carrinho de Compras</h3>
                        <p>O carrinho permite que você adicione vários itens antes de finalizar a compra.</p>
                        
                        <h4>🛒 Adicionar ao Carrinho:</h4>
                        <ol>
                            <li>Navegue pela loja e encontre o item</li>
                            <li>Clique no item para ver detalhes</li>
                            <li>Selecione a quantidade desejada</li>
                            <li>Clique em <strong>"Adicionar ao Carrinho"</strong></li>
                            <li>Uma notificação confirma que foi adicionado</li>
                            <li>Continue comprando ou vá para o carrinho</li>
                        </ol>
                        
                        <h4>🔢 Ícone do Carrinho:</h4>
                        <ul>
                            <li>Fica no menu superior</li>
                            <li>Mostra o número de itens adicionados</li>
                            <li>Clique para ver/editar o carrinho</li>
                        </ul>
                        
                        <h4>✏️ Editar Carrinho:</h4>
                        <ul>
                            <li><strong>Alterar quantidade:</strong> Use os botões + e - ou digite</li>
                            <li><strong>Remover item:</strong> Clique no X ou ícone de lixeira</li>
                            <li><strong>Limpar tudo:</strong> Botão "Limpar Carrinho"</li>
                        </ul>
                        
                        <h4>💰 Resumo do Carrinho:</h4>
                        <ul>
                            <li>Subtotal de cada item</li>
                            <li>Descontos aplicados</li>
                            <li>Total geral da compra</li>
                            <li>Economia (se houver promoção)</li>
                        </ul>
                        
                        <h4>🎁 Cupom de Desconto:</h4>
                        <ol>
                            <li>Digite o código do cupom no campo indicado</li>
                            <li>Clique em "Aplicar"</li>
                            <li>O desconto será calculado automaticamente</li>
                            <li>Verifique as condições do cupom</li>
                        </ol>
                        
                        <h4>✅ Finalizar Compra:</h4>
                        <ol>
                            <li>Revise todos os itens</li>
                            <li>Selecione o personagem para entrega</li>
                            <li>Escolha o método de pagamento</li>
                            <li>Clique em "Finalizar Compra"</li>
                        </ol>
                        
                        <h4>⚠️ Observações:</h4>
                        <ul>
                            <li>O carrinho é salvo automaticamente (mesmo se fechar o navegador)</li>
                            <li>Itens podem esgotar enquanto estão no carrinho</li>
                            <li>Preços podem mudar até a finalização</li>
                            <li>Verifique disponibilidade antes de finalizar</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the shopping cart?',
                        'answer': '''
                        <h3>Shopping Cart</h3>
                        <p>The cart allows you to add multiple items before completing your purchase.</p>
                        
                        <h4>🛒 Add to Cart:</h4>
                        <ol>
                            <li>Browse the store and find the item</li>
                            <li>Click on item to see details</li>
                            <li>Select desired quantity</li>
                            <li>Click <strong>"Add to Cart"</strong></li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar el carrito de compras?',
                        'answer': '''
                        <h3>Carrito de Compras</h3>
                        <p>El carrito te permite agregar varios ítems antes de finalizar la compra.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como selecionar o personagem para receber itens?',
                        'answer': '''
                        <h3>Selecionar Personagem para Entrega</h3>
                        <p>Ao fazer uma compra ou transferência, você precisa selecionar qual personagem receberá os itens.</p>
                        
                        <h4>👤 Na Finalização da Compra:</h4>
                        <ol>
                            <li>Vá para o carrinho de compras</li>
                            <li>Clique em "Finalizar Compra"</li>
                            <li>Na seção "Personagem de Destino":</li>
                            <li>Você verá a lista dos seus personagens</li>
                            <li>Selecione o personagem desejado</li>
                            <li>Continue para o pagamento</li>
                        </ol>
                        
                        <h4>📋 Informações do Personagem:</h4>
                        <ul>
                            <li>Nome do personagem</li>
                            <li>Nível e classe</li>
                            <li>Status (🟢 Online / 🔴 Offline)</li>
                        </ul>
                        
                        <h4>🔄 Personagem Padrão:</h4>
                        <ul>
                            <li>Você pode definir um personagem como padrão</li>
                            <li>Acesse <strong>"Personagens → Configurações"</strong></li>
                            <li>Selecione "Definir como Padrão"</li>
                            <li>Este será pré-selecionado em compras futuras</li>
                        </ul>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li><strong>Verifique antes de confirmar:</strong> Não é possível trocar após o pagamento</li>
                            <li><strong>Inventário:</strong> O personagem precisa ter espaço no inventário</li>
                            <li><strong>Online/Offline:</strong> Se offline, recebe ao logar</li>
                            <li><strong>Não aparece:</strong> Se o char não aparece, pode ser novo - aguarde sincronização</li>
                        </ul>
                        
                        <h4>🔧 Personagem Não Aparece na Lista?</h4>
                        <ul>
                            <li>Verifique se está logando na conta correta</li>
                            <li>Personagens novos podem levar alguns minutos para aparecer</li>
                            <li>Tente atualizar a página</li>
                            <li>Entre em contato com o suporte se persistir</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to select character to receive items?',
                        'answer': '''
                        <h3>Select Character for Delivery</h3>
                        <p>When making a purchase or transfer, you need to select which character will receive the items.</p>
                        
                        <h4>👤 At Checkout:</h4>
                        <ol>
                            <li>Go to shopping cart</li>
                            <li>Click "Checkout"</li>
                            <li>In "Destination Character" section</li>
                            <li>Select the desired character</li>
                            <li>Continue to payment</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo seleccionar el personaje para recibir ítems?',
                        'answer': '''
                        <h3>Seleccionar Personaje para Entrega</h3>
                        <p>Al hacer una compra o transferencia, necesitas seleccionar qué personaje recibirá los ítems.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar cupons de desconto?',
                        'answer': '''
                        <h3>Cupons de Desconto</h3>
                        <p>O PDL oferece cupons de desconto em diversas ocasiões. Veja como utilizá-los.</p>
                        
                        <h4>🎟️ Onde Encontrar Cupons:</h4>
                        <ul>
                            <li>Promoções no site</li>
                            <li>E-mails promocionais</li>
                            <li>Redes sociais do servidor</li>
                            <li>Discord da comunidade</li>
                            <li>Eventos especiais</li>
                            <li>Recompensas de conquistas</li>
                        </ul>
                        
                        <h4>📝 Como Aplicar o Cupom:</h4>
                        <ol>
                            <li>Adicione itens ao carrinho</li>
                            <li>Vá para o carrinho de compras</li>
                            <li>Procure o campo <strong>"Cupom de Desconto"</strong></li>
                            <li>Digite o código exatamente como recebeu</li>
                            <li>Clique em <strong>"Aplicar"</strong></li>
                            <li>O desconto será mostrado no total</li>
                        </ol>
                        
                        <h4>⚠️ Condições dos Cupons:</h4>
                        <ul>
                            <li><strong>Validade:</strong> Cupons têm data de expiração</li>
                            <li><strong>Uso único:</strong> Maioria só pode ser usado uma vez</li>
                            <li><strong>Valor mínimo:</strong> Alguns exigem compra mínima</li>
                            <li><strong>Categorias:</strong> Podem ser válidos só para certas categorias</li>
                            <li><strong>Não cumulativo:</strong> Geralmente não combina com outras promoções</li>
                        </ul>
                        
                        <h4>❌ Cupom Não Funciona?</h4>
                        <ul>
                            <li>Verifique se digitou corretamente (maiúsculas/minúsculas)</li>
                            <li>Confirme se não expirou</li>
                            <li>Verifique se atende ao valor mínimo</li>
                            <li>Confirme se é válido para os itens no carrinho</li>
                            <li>Verifique se já não foi usado</li>
                        </ul>
                        
                        <h4>💡 Dica:</h4>
                        <ul>
                            <li>Siga o servidor nas redes sociais para não perder cupons</li>
                            <li>Verifique e-mails de promoções (inclusive spam)</li>
                            <li>Cupons de aniversário e datas especiais são comuns</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use discount coupons?',
                        'answer': '''
                        <h3>Discount Coupons</h3>
                        <p>PDL offers discount coupons on various occasions. See how to use them.</p>
                        
                        <h4>📝 How to Apply Coupon:</h4>
                        <ol>
                            <li>Add items to cart</li>
                            <li>Go to shopping cart</li>
                            <li>Find the "Discount Coupon" field</li>
                            <li>Enter the code exactly as received</li>
                            <li>Click "Apply"</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar cupones de descuento?',
                        'answer': '''
                        <h3>Cupones de Descuento</h3>
                        <p>El PDL ofrece cupones de descuento en diversas ocasiones. Ve cómo utilizarlos.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver rankings e estatísticas do servidor?',
                        'answer': '''
                        <h3>Rankings e Estatísticas</h3>
                        <p>O PDL exibe rankings atualizados do servidor para você acompanhar os melhores jogadores e clans.</p>
                        
                        <h4>🏆 Tipos de Rankings:</h4>
                        <ul>
                            <li><strong>Top Level:</strong> Jogadores com maior nível</li>
                            <li><strong>Top PvP:</strong> Jogadores com mais kills em PvP</li>
                            <li><strong>Top PK:</strong> Jogadores com mais player kills</li>
                            <li><strong>Top Clans:</strong> Clans mais poderosos</li>
                            <li><strong>Top Olympiad:</strong> Melhores no Olympiad</li>
                            <li><strong>Heroes:</strong> Heróis atuais do servidor</li>
                            <li><strong>Castle Owners:</strong> Clans donos de castelos</li>
                        </ul>
                        
                        <h4>📊 Como Acessar:</h4>
                        <ol>
                            <li>Acesse <strong>"Rankings"</strong> no menu principal</li>
                            <li>Selecione o tipo de ranking desejado</li>
                            <li>Use os filtros para refinar (classe, raça, etc.)</li>
                            <li>Clique em um jogador para ver detalhes</li>
                        </ol>
                        
                        <h4>📈 Estatísticas Disponíveis:</h4>
                        <ul>
                            <li>Total de jogadores online/offline</li>
                            <li>Pico de jogadores</li>
                            <li>Estatísticas de classes mais jogadas</li>
                            <li>Economia do servidor (se disponível)</li>
                        </ul>
                        
                        <h4>🔄 Atualização:</h4>
                        <ul>
                            <li>Rankings são atualizados periodicamente</li>
                            <li>Geralmente a cada hora ou em tempo real</li>
                            <li>A última atualização é mostrada na página</li>
                        </ul>
                        
                        <h4>🎯 Sua Posição:</h4>
                        <ul>
                            <li>Veja onde você está no ranking</li>
                            <li>Acompanhe seu progresso ao longo do tempo</li>
                            <li>Compare com amigos e rivais</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to view server rankings and statistics?',
                        'answer': '''
                        <h3>Rankings and Statistics</h3>
                        <p>PDL displays updated server rankings for you to follow the best players and clans.</p>
                        
                        <h4>🏆 Ranking Types:</h4>
                        <ul>
                            <li><strong>Top Level:</strong> Highest level players</li>
                            <li><strong>Top PvP:</strong> Players with most PvP kills</li>
                            <li><strong>Top Clans:</strong> Most powerful clans</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver rankings y estadísticas del servidor?',
                        'answer': '''
                        <h3>Rankings y Estadísticas</h3>
                        <p>El PDL muestra rankings actualizados del servidor para que sigas a los mejores jugadores y clanes.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver e editar meu perfil público?',
                        'answer': '''
                        <h3>Perfil Público</h3>
                        <p>Seu perfil público mostra suas informações, conquistas e estatísticas para outros jogadores.</p>
                        
                        <h4>👤 Acessar Meu Perfil:</h4>
                        <ol>
                            <li>Clique no seu avatar/nome no menu</li>
                            <li>Selecione <strong>"Meu Perfil"</strong></li>
                            <li>Ou acesse diretamente pelo menu principal</li>
                        </ol>
                        
                        <h4>📋 Informações do Perfil:</h4>
                        <ul>
                            <li><strong>Foto de perfil:</strong> Sua imagem personalizada</li>
                            <li><strong>Nome de usuário:</strong> Seu nome no sistema</li>
                            <li><strong>Biografia:</strong> Descrição sobre você</li>
                            <li><strong>Nível/XP:</strong> Seu progresso no PDL</li>
                            <li><strong>Conquistas:</strong> Badges desbloqueados</li>
                            <li><strong>Personagens:</strong> Seus chars (se público)</li>
                            <li><strong>Estatísticas:</strong> Compras, tempo no sistema, etc.</li>
                        </ul>
                        
                        <h4>✏️ Editar Perfil:</h4>
                        <ol>
                            <li>No seu perfil, clique em <strong>"Editar Perfil"</strong></li>
                            <li>Altere as informações desejadas:
                                <ul>
                                    <li>Foto de perfil (upload de imagem)</li>
                                    <li>Biografia</li>
                                    <li>Redes sociais</li>
                                </ul>
                            </li>
                            <li>Clique em <strong>"Salvar"</strong></li>
                        </ol>
                        
                        <h4>🔒 Configurações de Privacidade:</h4>
                        <ul>
                            <li><strong>Perfil Público:</strong> Qualquer um pode ver</li>
                            <li><strong>Perfil Privado:</strong> Só você vê</li>
                            <li><strong>Ocultar Personagens:</strong> Não mostrar seus chars</li>
                            <li><strong>Ocultar Estatísticas:</strong> Não mostrar seus números</li>
                        </ul>
                        
                        <h4>🔗 Compartilhar Perfil:</h4>
                        <ul>
                            <li>Copie o link do seu perfil</li>
                            <li>Compartilhe com amigos</li>
                            <li>Coloque na assinatura do fórum</li>
                        </ul>
                        
                        <h4>🏅 Conquistas e Badges:</h4>
                        <ul>
                            <li>Ganhe conquistas por ações no sistema</li>
                            <li>Badges são exibidos no perfil</li>
                            <li>Algumas conquistas são raras e exclusivas</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to view and edit my public profile?',
                        'answer': '''
                        <h3>Public Profile</h3>
                        <p>Your public profile shows your information, achievements and statistics to other players.</p>
                        
                        <h4>👤 Access My Profile:</h4>
                        <ol>
                            <li>Click your avatar/name in menu</li>
                            <li>Select <strong>"My Profile"</strong></li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver y editar mi perfil público?',
                        'answer': '''
                        <h3>Perfil Público</h3>
                        <p>Tu perfil público muestra tu información, logros y estadísticas a otros jugadores.</p>
                        '''
                    }
                }
            },
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como alterar minhas configurações de conta?',
                        'answer': '''
                        <h3>Configurações da Conta</h3>
                        <p>Gerencie todas as configurações da sua conta em um só lugar.</p>
                        
                        <h4>⚙️ Acessar Configurações:</h4>
                        <ol>
                            <li>Clique no seu avatar no menu</li>
                            <li>Selecione <strong>"Configurações"</strong></li>
                            <li>Ou acesse pelo menu <strong>"Perfil → Configurações"</strong></li>
                        </ol>
                        
                        <h4>🔧 Configurações Disponíveis:</h4>
                        
                        <h5>📧 Conta:</h5>
                        <ul>
                            <li>Alterar e-mail</li>
                            <li>Alterar senha</li>
                            <li>Verificar e-mail</li>
                            <li>Excluir conta</li>
                        </ul>
                        
                        <h5>🔒 Segurança:</h5>
                        <ul>
                            <li>Ativar/desativar 2FA</li>
                            <li>Gerar códigos de recuperação</li>
                            <li>Histórico de login</li>
                            <li>Encerrar outras sessões</li>
                            <li>Limites de transferência</li>
                        </ul>
                        
                        <h5>🔔 Notificações:</h5>
                        <ul>
                            <li>E-mails de promoções</li>
                            <li>Alertas de segurança</li>
                            <li>Notificações de pagamento</li>
                            <li>Notificações de leilões</li>
                            <li>Newsletter</li>
                        </ul>
                        
                        <h5>🎨 Aparência:</h5>
                        <ul>
                            <li>Tema (claro/escuro)</li>
                            <li>Idioma</li>
                            <li>Formato de data/hora</li>
                            <li>Moeda preferida</li>
                        </ul>
                        
                        <h5>🔐 Privacidade:</h5>
                        <ul>
                            <li>Visibilidade do perfil</li>
                            <li>Mostrar personagens</li>
                            <li>Mostrar estatísticas</li>
                            <li>Exportar dados</li>
                        </ul>
                        
                        <h4>💾 Salvar Alterações:</h4>
                        <ul>
                            <li>Clique em "Salvar" após cada alteração</li>
                            <li>Algumas mudanças requerem confirmação por e-mail</li>
                            <li>Alterações de segurança podem pedir senha</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to change my account settings?',
                        'answer': '''
                        <h3>Account Settings</h3>
                        <p>Manage all your account settings in one place.</p>
                        
                        <h4>⚙️ Access Settings:</h4>
                        <ol>
                            <li>Click your avatar in menu</li>
                            <li>Select <strong>"Settings"</strong></li>
                        </ol>
                        
                        <h4>🔧 Available Settings:</h4>
                        <ul>
                            <li>Account: email, password</li>
                            <li>Security: 2FA, login history</li>
                            <li>Notifications: emails, alerts</li>
                            <li>Appearance: theme, language</li>
                            <li>Privacy: profile visibility</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo cambiar las configuraciones de mi cuenta?',
                        'answer': '''
                        <h3>Configuraciones de la Cuenta</h3>
                        <p>Gestiona todas las configuraciones de tu cuenta en un solo lugar.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como mudar entre tema claro e escuro?',
                        'answer': '''
                        <h3>Tema Claro e Escuro</h3>
                        <p>O PDL oferece tema claro e escuro para sua preferência visual.</p>
                        
                        <h4>🌙 Mudar o Tema:</h4>
                        
                        <h5>Método Rápido:</h5>
                        <ul>
                            <li>Procure o ícone de lua/sol no menu</li>
                            <li>Clique para alternar entre claro e escuro</li>
                            <li>A mudança é instantânea</li>
                        </ul>
                        
                        <h5>Pelo Menu:</h5>
                        <ol>
                            <li>Acesse <strong>"Configurações → Aparência"</strong></li>
                            <li>Selecione o tema desejado:
                                <ul>
                                    <li>☀️ Claro</li>
                                    <li>🌙 Escuro</li>
                                    <li>💻 Automático (segue o sistema)</li>
                                </ul>
                            </li>
                            <li>A preferência é salva automaticamente</li>
                        </ol>
                        
                        <h4>💡 Dicas:</h4>
                        <ul>
                            <li>Tema escuro é mais confortável à noite</li>
                            <li>Tema escuro pode economizar bateria em telas OLED</li>
                            <li>O modo automático ajusta conforme horário ou sistema</li>
                            <li>Sua preferência é lembrada em todos os dispositivos</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to switch between light and dark theme?',
                        'answer': '''
                        <h3>Light and Dark Theme</h3>
                        <p>PDL offers light and dark themes for your visual preference.</p>
                        
                        <h4>🌙 Change Theme:</h4>
                        <ul>
                            <li>Look for moon/sun icon in menu</li>
                            <li>Click to toggle between light and dark</li>
                            <li>Or go to Settings → Appearance</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo cambiar entre tema claro y oscuro?',
                        'answer': '''
                        <h3>Tema Claro y Oscuro</h3>
                        <p>El PDL ofrece tema claro y oscuro para tu preferencia visual.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver promoções e ofertas especiais?',
                        'answer': '''
                        <h3>Promoções e Ofertas</h3>
                        <p>O PDL frequentemente oferece promoções e descontos especiais. Veja como não perder nenhuma!</p>
                        
                        <h4>🏷️ Onde Encontrar Promoções:</h4>
                        <ul>
                            <li><strong>Banner na Home:</strong> Destaques na página inicial</li>
                            <li><strong>Seção "Promoções":</strong> No menu da loja</li>
                            <li><strong>Loja → Ofertas:</strong> Itens com desconto</li>
                            <li><strong>E-mail:</strong> Promoções exclusivas por e-mail</li>
                            <li><strong>Notificações:</strong> Alertas de novas ofertas</li>
                        </ul>
                        
                        <h4>🔥 Tipos de Promoções:</h4>
                        <ul>
                            <li><strong>Desconto Percentual:</strong> X% off em itens selecionados</li>
                            <li><strong>Pacotes Promocionais:</strong> Combos com preço especial</li>
                            <li><strong>Flash Sales:</strong> Ofertas relâmpago por tempo limitado</li>
                            <li><strong>Promoções Sazonais:</strong> Natal, Ano Novo, etc.</li>
                            <li><strong>Eventos Especiais:</strong> Aniversário do servidor, etc.</li>
                            <li><strong>Primeira Compra:</strong> Desconto para novos usuários</li>
                        </ul>
                        
                        <h4>⏰ Promoções por Tempo Limitado:</h4>
                        <ul>
                            <li>Veja o contador de tempo na oferta</li>
                            <li>Promoções podem acabar a qualquer momento</li>
                            <li>Estoque limitado - não deixe para depois!</li>
                        </ul>
                        
                        <h4>📧 Não Perder Promoções:</h4>
                        <ol>
                            <li>Ative notificações de promoções em Configurações</li>
                            <li>Verifique seu e-mail regularmente (inclusive spam)</li>
                            <li>Siga o servidor nas redes sociais</li>
                            <li>Entre no Discord da comunidade</li>
                            <li>Visite o site regularmente</li>
                        </ol>
                        
                        <h4>💡 Dica:</h4>
                        <ul>
                            <li>Compare preços antes de comprar</li>
                            <li>Verifique se a promoção é real (preço original vs. promocional)</li>
                            <li>Algumas promoções exigem cupom - verifique as condições</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to see promotions and special offers?',
                        'answer': '''
                        <h3>Promotions and Offers</h3>
                        <p>PDL frequently offers promotions and special discounts. See how not to miss any!</p>
                        
                        <h4>🏷️ Where to Find Promotions:</h4>
                        <ul>
                            <li><strong>Home Banner:</strong> Highlights on home page</li>
                            <li><strong>"Promotions" Section:</strong> In store menu</li>
                            <li><strong>Email:</strong> Exclusive email promotions</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver promociones y ofertas especiales?',
                        'answer': '''
                        <h3>Promociones y Ofertas</h3>
                        <p>El PDL frecuentemente ofrece promociones y descuentos especiales.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como participar de eventos e sorteios?',
                        'answer': '''
                        <h3>Eventos e Sorteios</h3>
                        <p>O PDL organiza eventos e sorteios regularmente com prêmios incríveis.</p>
                        
                        <h4>🎉 Tipos de Eventos:</h4>
                        <ul>
                            <li><strong>Sorteios:</strong> Concorra a itens e saldo</li>
                            <li><strong>Eventos de Comunidade:</strong> Participação em grupo</li>
                            <li><strong>Competições:</strong> Quem acumular mais pontos</li>
                            <li><strong>Eventos Sazonais:</strong> Datas comemorativas</li>
                            <li><strong>Caça ao Tesouro:</strong> Encontre itens escondidos</li>
                        </ul>
                        
                        <h4>📍 Onde Encontrar:</h4>
                        <ul>
                            <li><strong>"Eventos"</strong> no menu principal</li>
                            <li>Banner na página inicial</li>
                            <li>Notificações do sistema</li>
                            <li>Discord e redes sociais</li>
                        </ul>
                        
                        <h4>🎫 Como Participar de Sorteios:</h4>
                        <ol>
                            <li>Acesse a página do evento/sorteio</li>
                            <li>Leia as regras e requisitos</li>
                            <li>Clique em <strong>"Participar"</strong></li>
                            <li>Complete as ações necessárias (se houver)</li>
                            <li>Aguarde o resultado</li>
                            <li>Vencedores são anunciados na página do evento</li>
                        </ol>
                        
                        <h4>📋 Requisitos Comuns:</h4>
                        <ul>
                            <li>Conta ativa e verificada</li>
                            <li>Estar logado durante o evento</li>
                            <li>Completar tarefas específicas</li>
                            <li>Fazer uma compra mínima (em alguns casos)</li>
                        </ul>
                        
                        <h4>🏆 Receber Prêmios:</h4>
                        <ul>
                            <li>Prêmios são entregues automaticamente ao vencedor</li>
                            <li>Veja o resultado em "Meus Eventos"</li>
                            <li>Prêmios vão para a carteira ou inventário</li>
                            <li>Você recebe notificação se ganhar</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to participate in events and giveaways?',
                        'answer': '''
                        <h3>Events and Giveaways</h3>
                        <p>PDL organizes events and giveaways regularly with amazing prizes.</p>
                        
                        <h4>🎫 How to Participate:</h4>
                        <ol>
                            <li>Access the event page</li>
                            <li>Read rules and requirements</li>
                            <li>Click "Participate"</li>
                            <li>Wait for results</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo participar en eventos y sorteos?',
                        'answer': '''
                        <h3>Eventos y Sorteos</h3>
                        <p>El PDL organiza eventos y sorteos regularmente con premios increíbles.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver o calendário de eventos do servidor?',
                        'answer': '''
                        <h3>Calendário de Eventos</h3>
                        <p>O PDL exibe um calendário com todos os eventos programados do servidor.</p>
                        
                        <h4>📅 Acessar o Calendário:</h4>
                        <ol>
                            <li>Acesse <strong>"Eventos"</strong> no menu</li>
                            <li>Clique em <strong>"Calendário"</strong></li>
                            <li>Navegue pelos meses</li>
                        </ol>
                        
                        <h4>🎮 Tipos de Eventos no Calendário:</h4>
                        <ul>
                            <li><strong>Siege (Cerco):</strong> Batalhas por castelos</li>
                            <li><strong>Olympiad:</strong> Período das olimpíadas</li>
                            <li><strong>Eventos TvT:</strong> Team vs Team</li>
                            <li><strong>Raid Bosses:</strong> Horários de spawn</li>
                            <li><strong>Manutenções:</strong> Períodos de manutenção</li>
                            <li><strong>Promoções:</strong> Início e fim de ofertas</li>
                            <li><strong>Eventos Especiais:</strong> Eventos temáticos</li>
                        </ul>
                        
                        <h4>🔔 Configurar Lembretes:</h4>
                        <ul>
                            <li>Clique em um evento no calendário</li>
                            <li>Ative "Lembrar-me"</li>
                            <li>Escolha quando ser notificado (1h antes, 30min, etc.)</li>
                            <li>Receba notificação no horário</li>
                        </ul>
                        
                        <h4>⏰ Fuso Horário:</h4>
                        <ul>
                            <li>Eventos são mostrados no horário do servidor</li>
                            <li>Verifique qual é o fuso horário do servidor</li>
                            <li>Alguns eventos podem mostrar em horário local</li>
                        </ul>
                        
                        <h4>📱 Exportar para Calendário:</h4>
                        <ul>
                            <li>Exporte eventos para Google Calendar, Outlook, etc.</li>
                            <li>Clique em "Exportar" no evento</li>
                            <li>Adicione ao seu calendário pessoal</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to view the server event calendar?',
                        'answer': '''
                        <h3>Event Calendar</h3>
                        <p>PDL displays a calendar with all scheduled server events.</p>
                        
                        <h4>📅 Access Calendar:</h4>
                        <ol>
                            <li>Go to "Events" in menu</li>
                            <li>Click "Calendar"</li>
                            <li>Browse through months</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver el calendario de eventos del servidor?',
                        'answer': '''
                        <h3>Calendario de Eventos</h3>
                        <p>El PDL muestra un calendario con todos los eventos programados del servidor.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona o sistema de conquistas e XP?',
                        'answer': '''
                        <h3>Sistema de Conquistas e XP</h3>
                        <p>O PDL possui um sistema de gamificação que recompensa você por usar o painel.</p>
                        
                        <h4>⭐ O que é XP:</h4>
                        <ul>
                            <li>Pontos de experiência ganhos por ações no painel</li>
                            <li>Acumule XP para subir de nível</li>
                            <li>Níveis mais altos podem ter benefícios</li>
                        </ul>
                        
                        <h4>📈 Como Ganhar XP:</h4>
                        <ul>
                            <li>Fazer login diariamente</li>
                            <li>Completar o perfil</li>
                            <li>Fazer compras na loja</li>
                            <li>Participar de leilões</li>
                            <li>Usar o marketplace</li>
                            <li>Jogar minigames</li>
                            <li>Indicar amigos</li>
                            <li>Participar de eventos</li>
                        </ul>
                        
                        <h4>🏆 Conquistas (Achievements):</h4>
                        <ul>
                            <li>Objetivos específicos para desbloquear</li>
                            <li>Cada conquista dá XP bônus</li>
                            <li>Badges são exibidos no perfil</li>
                            <li>Algumas conquistas são secretas</li>
                        </ul>
                        
                        <h4>📋 Exemplos de Conquistas:</h4>
                        <ul>
                            <li>🎯 Primeira Compra</li>
                            <li>🛒 Comprador Frequente (X compras)</li>
                            <li>💰 Mãos de Ouro (Ganhar em minigame)</li>
                            <li>🏆 Campeão de Leilões</li>
                            <li>👥 Comerciante (X vendas no marketplace)</li>
                            <li>📅 Veterano (X dias de conta)</li>
                            <li>🔒 Segurança Primeiro (Ativar 2FA)</li>
                        </ul>
                        
                        <h4>📊 Ver Progresso:</h4>
                        <ol>
                            <li>Acesse <strong>"Perfil → Conquistas"</strong></li>
                            <li>Veja conquistas desbloqueadas</li>
                            <li>Veja progresso nas conquistas em andamento</li>
                            <li>Descubra dicas para desbloquear novas</li>
                        </ol>
                        
                        <h4>🎁 Recompensas:</h4>
                        <ul>
                            <li>XP para subir de nível</li>
                            <li>Badges exclusivos</li>
                            <li>Títulos especiais</li>
                            <li>Cupons de desconto (algumas conquistas)</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does the achievement and XP system work?',
                        'answer': '''
                        <h3>Achievement and XP System</h3>
                        <p>PDL has a gamification system that rewards you for using the panel.</p>
                        
                        <h4>📈 How to Earn XP:</h4>
                        <ul>
                            <li>Daily login</li>
                            <li>Complete profile</li>
                            <li>Make purchases</li>
                            <li>Participate in auctions</li>
                            <li>Play minigames</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona el sistema de logros y XP?',
                        'answer': '''
                        <h3>Sistema de Logros y XP</h3>
                        <p>El PDL tiene un sistema de gamificación que te recompensa por usar el panel.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como favoritar itens na loja?',
                        'answer': '''
                        <h3>Lista de Favoritos / Wishlist</h3>
                        <p>Salve itens que você deseja comprar no futuro na sua lista de favoritos.</p>
                        
                        <h4>❤️ Adicionar aos Favoritos:</h4>
                        <ol>
                            <li>Navegue pela loja</li>
                            <li>Encontre o item desejado</li>
                            <li>Clique no ícone de coração (❤️) ou "Favoritar"</li>
                            <li>O item é salvo na sua lista</li>
                        </ol>
                        
                        <h4>📋 Ver Meus Favoritos:</h4>
                        <ol>
                            <li>Acesse <strong>"Loja → Favoritos"</strong></li>
                            <li>Ou clique no ícone de coração no menu</li>
                            <li>Veja todos os itens salvos</li>
                        </ol>
                        
                        <h4>🔔 Alertas de Preço:</h4>
                        <ul>
                            <li>Ative alertas para itens favoritados</li>
                            <li>Receba notificação quando entrar em promoção</li>
                            <li>Seja avisado quando voltar ao estoque</li>
                        </ul>
                        
                        <h4>🗑️ Remover dos Favoritos:</h4>
                        <ul>
                            <li>Clique novamente no coração</li>
                            <li>Ou use "Remover" na lista de favoritos</li>
                        </ul>
                        
                        <h4>💡 Dicas:</h4>
                        <ul>
                            <li>Use favoritos para planejar compras futuras</li>
                            <li>Favoritos são sincronizados em todos os dispositivos</li>
                            <li>Você pode ter quantos favoritos quiser</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to favorite items in the store?',
                        'answer': '''
                        <h3>Favorites / Wishlist</h3>
                        <p>Save items you want to buy in the future to your favorites list.</p>
                        
                        <h4>❤️ Add to Favorites:</h4>
                        <ol>
                            <li>Browse the store</li>
                            <li>Find desired item</li>
                            <li>Click heart icon (❤️) or "Favorite"</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo agregar ítems a favoritos en la tienda?',
                        'answer': '''
                        <h3>Lista de Favoritos / Wishlist</h3>
                        <p>Guarda ítems que deseas comprar en el futuro en tu lista de favoritos.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver detalhes de um item antes de comprar?',
                        'answer': '''
                        <h3>Detalhes do Item</h3>
                        <p>Antes de comprar, você pode ver todas as informações sobre um item.</p>
                        
                        <h4>👁️ Ver Detalhes:</h4>
                        <ol>
                            <li>Navegue pela loja</li>
                            <li>Clique no item desejado</li>
                            <li>A página de detalhes será aberta</li>
                        </ol>
                        
                        <h4>📋 Informações Disponíveis:</h4>
                        <ul>
                            <li><strong>Nome:</strong> Nome completo do item</li>
                            <li><strong>Imagem:</strong> Visualização do item</li>
                            <li><strong>Descrição:</strong> O que o item faz</li>
                            <li><strong>Preço:</strong> Valor atual (e original se em promoção)</li>
                            <li><strong>Grade:</strong> Nível do item (D, C, B, A, S, etc.)</li>
                            <li><strong>Categoria:</strong> Tipo do item</li>
                            <li><strong>Estoque:</strong> Quantidade disponível</li>
                            <li><strong>Requisitos:</strong> Nível ou classe necessária</li>
                        </ul>
                        
                        <h4>📊 Estatísticas (para equipamentos):</h4>
                        <ul>
                            <li>P.Atk / M.Atk</li>
                            <li>P.Def / M.Def</li>
                            <li>Atributos especiais</li>
                            <li>Slots de SA (Special Ability)</li>
                        </ul>
                        
                        <h4>💬 Avaliações e Comentários:</h4>
                        <ul>
                            <li>Veja avaliações de outros compradores</li>
                            <li>Leia comentários sobre o item</li>
                            <li>Verifique a nota média</li>
                        </ul>
                        
                        <h4>🔗 Itens Relacionados:</h4>
                        <ul>
                            <li>Veja itens similares</li>
                            <li>Itens frequentemente comprados juntos</li>
                            <li>Complementos para o item</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to see item details before buying?',
                        'answer': '''
                        <h3>Item Details</h3>
                        <p>Before buying, you can see all information about an item.</p>
                        
                        <h4>📋 Available Information:</h4>
                        <ul>
                            <li>Name and image</li>
                            <li>Description</li>
                            <li>Price</li>
                            <li>Grade and category</li>
                            <li>Stock availability</li>
                            <li>Requirements</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver detalles de un ítem antes de comprar?',
                        'answer': '''
                        <h3>Detalles del Ítem</h3>
                        <p>Antes de comprar, puedes ver toda la información sobre un ítem.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona o sistema de indicação de amigos?',
                        'answer': '''
                        <h3>Sistema de Indicação</h3>
                        <p>Indique amigos para o PDL e ganhe recompensas quando eles se cadastrarem e fizerem compras.</p>
                        
                        <h4>🎁 Como Funciona:</h4>
                        <ol>
                            <li>Você recebe um link/código de indicação único</li>
                            <li>Compartilhe com amigos</li>
                            <li>Quando eles se cadastrarem pelo seu link, ficam vinculados a você</li>
                            <li>Você ganha recompensas quando eles completam ações</li>
                        </ol>
                        
                        <h4>🔗 Obter Seu Link:</h4>
                        <ol>
                            <li>Acesse <strong>"Perfil → Indicações"</strong></li>
                            <li>Copie seu link ou código único</li>
                            <li>Compartilhe por onde preferir</li>
                        </ol>
                        
                        <h4>🏆 Recompensas (podem variar):</h4>
                        <ul>
                            <li><strong>Por Cadastro:</strong> XP e/ou saldo bônus</li>
                            <li><strong>Por Primeira Compra:</strong> Percentual da compra em créditos</li>
                            <li><strong>Por Compras Subsequentes:</strong> Comissão contínua</li>
                            <li><strong>Metas de Indicação:</strong> Prêmios por quantidade de indicados</li>
                        </ul>
                        
                        <h4>📊 Acompanhar Indicações:</h4>
                        <ul>
                            <li>Veja quantos amigos se cadastraram</li>
                            <li>Acompanhe suas recompensas</li>
                            <li>Veja ranking de indicadores</li>
                        </ul>
                        
                        <h4>🎯 Benefícios para o Amigo:</h4>
                        <ul>
                            <li>Pode receber bônus de boas-vindas</li>
                            <li>Desconto na primeira compra</li>
                            <li>Outros benefícios do servidor</li>
                        </ul>
                        
                        <h4>⚠️ Regras:</h4>
                        <ul>
                            <li>Não crie contas falsas para ganhar recompensas</li>
                            <li>Auto-indicação é proibida</li>
                            <li>Fraudes resultam em banimento</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does the friend referral system work?',
                        'answer': '''
                        <h3>Referral System</h3>
                        <p>Refer friends to PDL and earn rewards when they sign up and make purchases.</p>
                        
                        <h4>🎁 How it Works:</h4>
                        <ol>
                            <li>Get your unique referral link/code</li>
                            <li>Share with friends</li>
                            <li>Earn rewards when they complete actions</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona el sistema de referidos?',
                        'answer': '''
                        <h3>Sistema de Referidos</h3>
                        <p>Invita amigos al PDL y gana recompensas cuando se registren y hagan compras.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Onde encontro informações sobre o servidor de jogo?',
                        'answer': '''
                        <h3>Informações do Servidor</h3>
                        <p>O PDL exibe informações importantes sobre o servidor de Lineage 2 conectado.</p>
                        
                        <h4>📊 Informações Disponíveis:</h4>
                        <ul>
                            <li><strong>Status:</strong> Se o servidor está online/offline</li>
                            <li><strong>Jogadores Online:</strong> Quantidade atual de jogadores</li>
                            <li><strong>Crônica:</strong> Versão do jogo (Interlude, H5, etc.)</li>
                            <li><strong>Rates:</strong> Taxas de XP, SP, Drop, Adena</li>
                            <li><strong>Uptime:</strong> Tempo online desde última manutenção</li>
                        </ul>
                        
                        <h4>📍 Onde Encontrar:</h4>
                        <ul>
                            <li>Dashboard (página inicial)</li>
                            <li>Seção "Servidor" ou "Info"</li>
                            <li>Rodapé do site</li>
                        </ul>
                        
                        <h4>🔧 Informações Técnicas:</h4>
                        <ul>
                            <li>IP do servidor (para conexão)</li>
                            <li>Portas de conexão</li>
                            <li>Download do cliente</li>
                            <li>Requisitos do sistema</li>
                        </ul>
                        
                        <h4>📋 Regras do Servidor:</h4>
                        <ul>
                            <li>Acesse a seção de "Regras" para ver as regras específicas</li>
                            <li>Cada servidor pode ter regras diferentes</li>
                            <li>Leia antes de jogar para evitar punições</li>
                        </ul>
                        
                        <h4>📞 Contato do Servidor:</h4>
                        <ul>
                            <li>Discord oficial</li>
                            <li>Fórum</li>
                            <li>Redes sociais</li>
                            <li>E-mail de suporte</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'Where to find game server information?',
                        'answer': '''
                        <h3>Server Information</h3>
                        <p>PDL displays important information about the connected Lineage 2 server.</p>
                        
                        <h4>📊 Available Information:</h4>
                        <ul>
                            <li>Server status (online/offline)</li>
                            <li>Players online</li>
                            <li>Chronicle version</li>
                            <li>XP/Drop rates</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Dónde encontrar información del servidor de juego?',
                        'answer': '''
                        <h3>Información del Servidor</h3>
                        <p>El PDL muestra información importante sobre el servidor de Lineage 2 conectado.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como baixar o cliente do jogo?',
                        'answer': '''
                        <h3>Download do Cliente</h3>
                        <p>Para jogar no servidor, você precisa baixar o cliente do jogo compatível.</p>
                        
                        <h4>📥 Onde Baixar:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Download"</strong> no menu</li>
                            <li>Ou procure o link na página inicial</li>
                            <li>Escolha a opção de download</li>
                        </ol>
                        
                        <h4>📋 Opções de Download:</h4>
                        <ul>
                            <li><strong>Cliente Completo:</strong> Instalação do zero</li>
                            <li><strong>Patch:</strong> Se você já tem um cliente base</li>
                            <li><strong>Torrent:</strong> Download via torrent (mais rápido)</li>
                            <li><strong>Google Drive/Mega:</strong> Links diretos</li>
                        </ul>
                        
                        <h4>💻 Requisitos Mínimos:</h4>
                        <ul>
                            <li>Sistema Operacional: Windows 7/8/10/11</li>
                            <li>Processador: Consulte a página de download</li>
                            <li>Memória RAM: Consulte a página de download</li>
                            <li>Espaço em disco: Varia por crônica</li>
                            <li>Placa de vídeo: Consulte a página de download</li>
                        </ul>
                        
                        <h4>🔧 Instalação:</h4>
                        <ol>
                            <li>Baixe o cliente completo</li>
                            <li>Extraia os arquivos (se compactado)</li>
                            <li>Execute o instalador ou extrator</li>
                            <li>Aplique o patch do servidor (se necessário)</li>
                            <li>Configure o system.cfg (se necessário)</li>
                            <li>Execute o launcher ou L2.exe</li>
                        </ol>
                        
                        <h4>⚠️ Problemas Comuns:</h4>
                        <ul>
                            <li><strong>Erro ao conectar:</strong> Verifique IP/porta nas configurações</li>
                            <li><strong>Gameguard:</strong> Desative antivírus temporariamente</li>
                            <li><strong>Crash:</strong> Execute como administrador</li>
                            <li><strong>Tela preta:</strong> Atualize drivers de vídeo</li>
                        </ul>
                        
                        <h4>❓ Precisa de Ajuda:</h4>
                        <ul>
                            <li>Consulte os guias de instalação</li>
                            <li>Pergunte no Discord</li>
                            <li>Abra um ticket de suporte</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to download the game client?',
                        'answer': '''
                        <h3>Client Download</h3>
                        <p>To play on the server, you need to download the compatible game client.</p>
                        
                        <h4>📥 Where to Download:</h4>
                        <ol>
                            <li>Go to "Download" section in menu</li>
                            <li>Choose download option</li>
                            <li>Follow installation instructions</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo descargar el cliente del juego?',
                        'answer': '''
                        <h3>Descarga del Cliente</h3>
                        <p>Para jugar en el servidor, necesitas descargar el cliente del juego compatible.</p>
                        '''
                    }
                }
            },
            # ==================== NOTÍCIAS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como ver as notícias e atualizações do servidor?',
                        'answer': '''
                        <h3>Notícias e Atualizações</h3>
                        <p>O PDL mantém você informado sobre todas as novidades do servidor através da seção de notícias.</p>
                        
                        <h4>📰 Acessar Notícias:</h4>
                        <ol>
                            <li>Clique em <strong>"Notícias"</strong> no menu principal</li>
                            <li>Veja a lista de notícias mais recentes</li>
                            <li>Clique em uma notícia para ler completa</li>
                        </ol>
                        
                        <h4>📋 Tipos de Notícias:</h4>
                        <ul>
                            <li><strong>Atualizações:</strong> Mudanças e novidades no servidor</li>
                            <li><strong>Eventos:</strong> Anúncios de eventos especiais</li>
                            <li><strong>Manutenções:</strong> Avisos de manutenção programada</li>
                            <li><strong>Promoções:</strong> Ofertas e descontos especiais</li>
                            <li><strong>Comunicados:</strong> Informações importantes da equipe</li>
                            <li><strong>Changelog:</strong> Lista de alterações técnicas</li>
                        </ul>
                        
                        <h4>🔔 Ser Notificado:</h4>
                        <ul>
                            <li>Ative notificações em <strong>"Configurações → Notificações"</strong></li>
                            <li>Receba e-mail quando houver notícias importantes</li>
                            <li>Notícias importantes aparecem no Dashboard</li>
                            <li>Siga o servidor nas redes sociais</li>
                        </ul>
                        
                        <h4>📌 Notícias Fixadas:</h4>
                        <ul>
                            <li>Notícias importantes ficam fixadas no topo</li>
                            <li>Leia sempre as notícias fixadas - são importantes!</li>
                        </ul>
                        
                        <h4>🔍 Filtrar Notícias:</h4>
                        <ul>
                            <li>Filtre por categoria</li>
                            <li>Busque por palavras-chave</li>
                            <li>Veja notícias de períodos específicos</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to see server news and updates?',
                        'answer': '''
                        <h3>News and Updates</h3>
                        <p>PDL keeps you informed about all server news through the news section.</p>
                        
                        <h4>📰 Access News:</h4>
                        <ol>
                            <li>Click <strong>"News"</strong> in main menu</li>
                            <li>See list of latest news</li>
                            <li>Click on news to read full article</li>
                        </ol>
                        
                        <h4>📋 News Types:</h4>
                        <ul>
                            <li>Updates, Events, Maintenance, Promotions, Announcements</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo ver las noticias y actualizaciones del servidor?',
                        'answer': '''
                        <h3>Noticias y Actualizaciones</h3>
                        <p>El PDL te mantiene informado sobre todas las novedades del servidor a través de la sección de noticias.</p>
                        '''
                    }
                }
            },
            # ==================== REDE SOCIAL / FEED ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar a rede social e o feed do PDL?',
                        'answer': '''
                        <h3>Rede Social do PDL</h3>
                        <p>O PDL possui uma rede social integrada onde você pode interagir com outros jogadores, compartilhar conquistas e fazer parte da comunidade.</p>
                        
                        <h4>📱 Acessar o Feed:</h4>
                        <ol>
                            <li>Clique em <strong>"Social"</strong> ou <strong>"Feed"</strong> no menu</li>
                            <li>Veja posts de outros jogadores</li>
                            <li>Interaja com curtidas e comentários</li>
                        </ol>
                        
                        <h4>✍️ Criar uma Publicação:</h4>
                        <ol>
                            <li>No feed, clique em <strong>"Criar Post"</strong> ou na caixa de texto</li>
                            <li>Escreva seu texto</li>
                            <li>Adicione imagens se desejar</li>
                            <li>Use hashtags para categorizar (#pvp, #clan, #evento)</li>
                            <li>Clique em <strong>"Publicar"</strong></li>
                        </ol>
                        
                        <h4>👍 Interagir com Posts:</h4>
                        <ul>
                            <li><strong>Curtir:</strong> Clique no ícone de coração/like</li>
                            <li><strong>Comentar:</strong> Escreva um comentário no post</li>
                            <li><strong>Compartilhar:</strong> Reposte para seus seguidores</li>
                            <li><strong>Salvar:</strong> Salve posts para ver depois</li>
                        </ul>
                        
                        <h4>👥 Seguir Jogadores:</h4>
                        <ul>
                            <li>Visite o perfil de um jogador</li>
                            <li>Clique em <strong>"Seguir"</strong></li>
                            <li>Posts dele aparecerão no seu feed</li>
                            <li>Veja quem você segue em "Seguindo"</li>
                            <li>Veja seus seguidores em "Seguidores"</li>
                        </ul>
                        
                        <h4>#️⃣ Hashtags:</h4>
                        <ul>
                            <li>Use hashtags para categorizar posts</li>
                            <li>Clique em uma hashtag para ver posts relacionados</li>
                            <li>Hashtags populares aparecem em destaque</li>
                        </ul>
                        
                        <h4>🔍 Buscar no Feed:</h4>
                        <ul>
                            <li>Busque por jogadores</li>
                            <li>Busque por hashtags</li>
                            <li>Busque por conteúdo</li>
                        </ul>
                        
                        <h4>⚙️ Gerenciar Seus Posts:</h4>
                        <ul>
                            <li>Acesse <strong>"Meus Posts"</strong> para ver suas publicações</li>
                            <li>Edite ou delete posts que você criou</li>
                        </ul>
                        
                        <h4>⚠️ Regras da Comunidade:</h4>
                        <ul>
                            <li>Respeite outros jogadores</li>
                            <li>Não faça spam ou propaganda</li>
                            <li>Não poste conteúdo ofensivo</li>
                            <li>Denuncie posts que violem as regras</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the social network and PDL feed?',
                        'answer': '''
                        <h3>PDL Social Network</h3>
                        <p>PDL has an integrated social network where you can interact with other players, share achievements and be part of the community.</p>
                        
                        <h4>📱 Access Feed:</h4>
                        <ol>
                            <li>Click "Social" or "Feed" in menu</li>
                            <li>See posts from other players</li>
                            <li>Interact with likes and comments</li>
                        </ol>
                        
                        <h4>✍️ Create a Post:</h4>
                        <ol>
                            <li>Click "Create Post"</li>
                            <li>Write your text and add images</li>
                            <li>Use hashtags</li>
                            <li>Click "Publish"</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar la red social y el feed del PDL?',
                        'answer': '''
                        <h3>Red Social del PDL</h3>
                        <p>El PDL tiene una red social integrada donde puedes interactuar con otros jugadores y ser parte de la comunidad.</p>
                        '''
                    }
                }
            },
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona a verificação de perfil na rede social?',
                        'answer': '''
                        <h3>Verificação de Perfil</h3>
                        <p>O PDL oferece verificação de perfil para jogadores que atendem certos requisitos.</p>
                        
                        <h4>✅ O que é o Selo de Verificação:</h4>
                        <ul>
                            <li>Um selo que aparece ao lado do seu nome</li>
                            <li>Indica que seu perfil é autêntico</li>
                            <li>Dá mais credibilidade às suas publicações</li>
                        </ul>
                        
                        <h4>📋 Requisitos (podem variar):</h4>
                        <ul>
                            <li>Conta ativa há X dias</li>
                            <li>Perfil completo (foto, bio)</li>
                            <li>2FA ativado</li>
                            <li>Sem histórico de violações</li>
                            <li>Nível mínimo de atividade</li>
                        </ul>
                        
                        <h4>🎯 Como Solicitar:</h4>
                        <ol>
                            <li>Acesse <strong>"Perfil → Verificação"</strong></li>
                            <li>Verifique se atende aos requisitos</li>
                            <li>Preencha o formulário de solicitação</li>
                            <li>Aguarde análise da equipe</li>
                        </ol>
                        
                        <h4>⏰ Prazo:</h4>
                        <ul>
                            <li>Solicitações são analisadas em até 7 dias</li>
                            <li>Você receberá notificação do resultado</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does profile verification work on social network?',
                        'answer': '''
                        <h3>Profile Verification</h3>
                        <p>PDL offers profile verification for players who meet certain requirements.</p>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona la verificación de perfil en la red social?',
                        'answer': '''
                        <h3>Verificación de Perfil</h3>
                        <p>El PDL ofrece verificación de perfil para jugadores que cumplen ciertos requisitos.</p>
                        '''
                    }
                }
            },
            # ==================== MENSAGENS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como enviar mensagens para outros jogadores?',
                        'answer': '''
                        <h3>Sistema de Mensagens</h3>
                        <p>O PDL possui um sistema de mensagens para você se comunicar com outros jogadores diretamente pelo painel.</p>
                        
                        <h4>💬 Acessar Mensagens:</h4>
                        <ol>
                            <li>Clique no ícone de mensagens no menu</li>
                            <li>Ou acesse <strong>"Mensagens"</strong> no menu principal</li>
                            <li>Veja suas conversas recentes</li>
                        </ol>
                        
                        <h4>✉️ Enviar Nova Mensagem:</h4>
                        <ol>
                            <li>Clique em <strong>"Nova Mensagem"</strong></li>
                            <li>Digite o nome do destinatário</li>
                            <li>Escreva sua mensagem</li>
                            <li>Clique em <strong>"Enviar"</strong></li>
                        </ol>
                        
                        <h4>📥 Caixa de Entrada:</h4>
                        <ul>
                            <li>Veja todas as mensagens recebidas</li>
                            <li>Mensagens não lidas ficam destacadas</li>
                            <li>Clique para abrir e responder</li>
                        </ul>
                        
                        <h4>📤 Mensagens Enviadas:</h4>
                        <ul>
                            <li>Veja mensagens que você enviou</li>
                            <li>Confirme se foram lidas (se disponível)</li>
                        </ul>
                        
                        <h4>🔔 Notificações:</h4>
                        <ul>
                            <li>Receba notificação de novas mensagens</li>
                            <li>O ícone mostra quantidade de não lidas</li>
                            <li>Configure alertas por e-mail se desejar</li>
                        </ul>
                        
                        <h4>🚫 Bloquear Usuários:</h4>
                        <ul>
                            <li>Se alguém estiver incomodando, você pode bloquear</li>
                            <li>Acesse o perfil do usuário → "Bloquear"</li>
                            <li>Usuários bloqueados não podem te enviar mensagens</li>
                        </ul>
                        
                        <h4>⚠️ Regras:</h4>
                        <ul>
                            <li>Não envie spam ou mensagens em massa</li>
                            <li>Respeite outros jogadores</li>
                            <li>Denuncie mensagens abusivas</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to send messages to other players?',
                        'answer': '''
                        <h3>Messaging System</h3>
                        <p>PDL has a messaging system for you to communicate with other players directly through the panel.</p>
                        
                        <h4>✉️ Send New Message:</h4>
                        <ol>
                            <li>Click "New Message"</li>
                            <li>Enter recipient name</li>
                            <li>Write your message</li>
                            <li>Click "Send"</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo enviar mensajes a otros jugadores?',
                        'answer': '''
                        <h3>Sistema de Mensajes</h3>
                        <p>El PDL tiene un sistema de mensajes para comunicarte con otros jugadores directamente desde el panel.</p>
                        '''
                    }
                }
            },
            # ==================== WIKI ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como usar a Wiki do servidor?',
                        'answer': '''
                        <h3>Wiki do Servidor</h3>
                        <p>A Wiki contém informações detalhadas sobre o servidor, mecânicas do jogo, itens e muito mais.</p>
                        
                        <h4>📚 Acessar a Wiki:</h4>
                        <ol>
                            <li>Clique em <strong>"Wiki"</strong> no menu</li>
                            <li>Navegue pelas categorias</li>
                            <li>Use a busca para encontrar conteúdo específico</li>
                        </ol>
                        
                        <h4>📋 Conteúdo da Wiki:</h4>
                        <ul>
                            <li><strong>Guias:</strong> Tutoriais e guias para iniciantes</li>
                            <li><strong>Classes:</strong> Informações sobre cada classe</li>
                            <li><strong>Itens:</strong> Database de itens do servidor</li>
                            <li><strong>Quests:</strong> Lista de quests disponíveis</li>
                            <li><strong>NPCs:</strong> Localização e funções de NPCs</li>
                            <li><strong>Mapas:</strong> Mapas e localizações</li>
                            <li><strong>Mecânicas:</strong> Explicação de sistemas do jogo</li>
                            <li><strong>Rates:</strong> Taxas do servidor</li>
                        </ul>
                        
                        <h4>🔍 Buscar na Wiki:</h4>
                        <ul>
                            <li>Use a barra de busca</li>
                            <li>Digite palavras-chave</li>
                            <li>Resultados mostram páginas relevantes</li>
                        </ul>
                        
                        <h4>📖 Histórico de Atualizações:</h4>
                        <ul>
                            <li>Veja changelog e atualizações recentes</li>
                            <li>Saiba o que mudou no servidor</li>
                        </ul>
                        
                        <h4>🗺️ Sitemap:</h4>
                        <ul>
                            <li>Veja todas as páginas da Wiki organizadas</li>
                            <li>Navegue pela estrutura completa</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the server Wiki?',
                        'answer': '''
                        <h3>Server Wiki</h3>
                        <p>The Wiki contains detailed information about the server, game mechanics, items and more.</p>
                        
                        <h4>📚 Access Wiki:</h4>
                        <ol>
                            <li>Click "Wiki" in menu</li>
                            <li>Browse categories</li>
                            <li>Use search to find specific content</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar la Wiki del servidor?',
                        'answer': '''
                        <h3>Wiki del Servidor</h3>
                        <p>La Wiki contiene información detallada sobre el servidor, mecánicas del juego, ítems y más.</p>
                        '''
                    }
                }
            },
            # ==================== ROADMAP ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'O que é o Roadmap e como acompanhar?',
                        'answer': '''
                        <h3>Roadmap de Atualizações</h3>
                        <p>O Roadmap mostra os planos futuros do servidor, o que está sendo desenvolvido e próximas atualizações.</p>
                        
                        <h4>🗺️ Acessar o Roadmap:</h4>
                        <ol>
                            <li>Clique em <strong>"Roadmap"</strong> no menu</li>
                            <li>Veja a linha do tempo de atualizações</li>
                            <li>Clique em um item para ver detalhes</li>
                        </ol>
                        
                        <h4>📋 O que o Roadmap Mostra:</h4>
                        <ul>
                            <li><strong>Planejado:</strong> Funcionalidades futuras previstas</li>
                            <li><strong>Em Desenvolvimento:</strong> O que está sendo feito agora</li>
                            <li><strong>Concluído:</strong> O que já foi implementado</li>
                            <li><strong>Cancelado:</strong> Planos que foram abandonados</li>
                        </ul>
                        
                        <h4>📊 Status das Atualizações:</h4>
                        <ul>
                            <li>🔵 Planejado</li>
                            <li>🟡 Em progresso</li>
                            <li>🟢 Concluído</li>
                            <li>🔴 Cancelado</li>
                        </ul>
                        
                        <h4>💡 Dicas:</h4>
                        <ul>
                            <li>Acompanhe regularmente para saber das novidades</li>
                            <li>Datas são estimativas e podem mudar</li>
                            <li>Sugira funcionalidades pelo suporte ou Discord</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What is the Roadmap and how to follow it?',
                        'answer': '''
                        <h3>Update Roadmap</h3>
                        <p>The Roadmap shows future server plans, what is being developed and upcoming updates.</p>
                        '''
                    },
                    'es': {
                        'question': '¿Qué es el Roadmap y cómo seguirlo?',
                        'answer': '''
                        <h3>Roadmap de Actualizaciones</h3>
                        <p>El Roadmap muestra los planes futuros del servidor y próximas actualizaciones.</p>
                        '''
                    }
                }
            },
            # ==================== INVENTÁRIO / BAG ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona o Inventário/Bag no PDL?',
                        'answer': '''
                        <h3>Inventário no PDL (Bag)</h3>
                        <p>O PDL possui um sistema de inventário onde você pode armazenar itens antes de enviar para seus personagens no jogo.</p>
                        
                        <h4>🎒 O que é a Bag:</h4>
                        <ul>
                            <li>Um inventário virtual no painel</li>
                            <li>Armazena itens ganhos em minigames, eventos ou compras</li>
                            <li>Você pode enviar itens da Bag para seus personagens</li>
                        </ul>
                        
                        <h4>📦 Acessar seu Inventário:</h4>
                        <ol>
                            <li>Clique em <strong>"Bag"</strong> ou <strong>"Inventário"</strong> no menu</li>
                            <li>Veja todos os itens armazenados</li>
                            <li>Filtre por categoria se necessário</li>
                        </ol>
                        
                        <h4>📤 Enviar Itens para Personagem:</h4>
                        <ol>
                            <li>Selecione o item na Bag</li>
                            <li>Clique em <strong>"Enviar para Personagem"</strong></li>
                            <li>Escolha o personagem de destino</li>
                            <li>Confirme o envio</li>
                            <li>O item aparecerá no inventário do char</li>
                        </ol>
                        
                        <h4>🎁 Como Itens Vão para a Bag:</h4>
                        <ul>
                            <li>Prêmios de minigames (roleta, caixas, etc.)</li>
                            <li>Recompensas de eventos</li>
                            <li>Itens de promoções especiais</li>
                            <li>Presentes recebidos</li>
                        </ul>
                        
                        <h4>⏰ Validade dos Itens:</h4>
                        <ul>
                            <li>Alguns itens podem ter prazo de validade</li>
                            <li>Verifique a data de expiração</li>
                            <li>Envie para o jogo antes de expirar</li>
                        </ul>
                        
                        <h4>📊 Histórico:</h4>
                        <ul>
                            <li>Veja histórico de itens recebidos</li>
                            <li>Veja itens enviados para personagens</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does the Inventory/Bag work in PDL?',
                        'answer': '''
                        <h3>PDL Inventory (Bag)</h3>
                        <p>PDL has an inventory system where you can store items before sending to your in-game characters.</p>
                        
                        <h4>📤 Send Items to Character:</h4>
                        <ol>
                            <li>Select item in Bag</li>
                            <li>Click "Send to Character"</li>
                            <li>Choose destination character</li>
                            <li>Confirm</li>
                        </ol>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona el Inventario/Bag en el PDL?',
                        'answer': '''
                        <h3>Inventario en el PDL (Bag)</h3>
                        <p>El PDL tiene un sistema de inventario donde puedes almacenar ítems antes de enviarlos a tus personajes.</p>
                        '''
                    }
                }
            },
            # ==================== BATTLE PASS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona o Battle Pass?',
                        'answer': '''
                        <h3>Battle Pass</h3>
                        <p>O Battle Pass é um sistema de recompensas por temporada onde você completa missões para ganhar prêmios exclusivos.</p>
                        
                        <h4>🎮 O que é o Battle Pass:</h4>
                        <ul>
                            <li>Sistema de progressão por temporada</li>
                            <li>Complete missões para ganhar XP</li>
                            <li>Suba de nível e desbloqueie recompensas</li>
                            <li>Versão gratuita e premium disponíveis</li>
                        </ul>
                        
                        <h4>📋 Acessar o Battle Pass:</h4>
                        <ol>
                            <li>Clique em <strong>"Battle Pass"</strong> no menu de games</li>
                            <li>Veja seu nível atual e progresso</li>
                            <li>Veja as missões disponíveis</li>
                            <li>Veja as recompensas de cada nível</li>
                        </ol>
                        
                        <h4>🎯 Missões:</h4>
                        <ul>
                            <li><strong>Missões Diárias:</strong> Renovam todo dia</li>
                            <li><strong>Missões Semanais:</strong> Renovam toda semana</li>
                            <li><strong>Missões de Temporada:</strong> Disponíveis durante toda temporada</li>
                        </ul>
                        
                        <h4>⬆️ Subir de Nível:</h4>
                        <ul>
                            <li>Complete missões para ganhar XP</li>
                            <li>Acumule XP suficiente para subir de nível</li>
                            <li>Cada nível desbloqueia novas recompensas</li>
                        </ul>
                        
                        <h4>🆓 Gratuito vs 💎 Premium:</h4>
                        <ul>
                            <li><strong>Gratuito:</strong> Recompensas básicas em alguns níveis</li>
                            <li><strong>Premium:</strong> Todas as recompensas + exclusivas</li>
                            <li>Você pode comprar o Premium a qualquer momento</li>
                            <li>Ao comprar, recebe retroativamente as recompensas</li>
                        </ul>
                        
                        <h4>🎁 Tipos de Recompensas:</h4>
                        <ul>
                            <li>Itens exclusivos</li>
                            <li>Skins e visuais</li>
                            <li>Moedas e recursos</li>
                            <li>Títulos especiais</li>
                            <li>E muito mais!</li>
                        </ul>
                        
                        <h4>⏰ Temporadas:</h4>
                        <ul>
                            <li>Cada temporada dura um período limitado</li>
                            <li>Ao fim da temporada, progresso é resetado</li>
                            <li>Novas recompensas a cada temporada</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does Battle Pass work?',
                        'answer': '''
                        <h3>Battle Pass</h3>
                        <p>Battle Pass is a seasonal reward system where you complete missions to earn exclusive prizes.</p>
                        
                        <h4>🎮 What is Battle Pass:</h4>
                        <ul>
                            <li>Seasonal progression system</li>
                            <li>Complete missions to earn XP</li>
                            <li>Level up and unlock rewards</li>
                            <li>Free and premium versions available</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona el Battle Pass?',
                        'answer': '''
                        <h3>Battle Pass</h3>
                        <p>El Battle Pass es un sistema de recompensas por temporada donde completas misiones para ganar premios exclusivos.</p>
                        '''
                    }
                }
            },
            # ==================== DAILY BONUS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como funciona o Bônus Diário?',
                        'answer': '''
                        <h3>Bônus Diário</h3>
                        <p>O sistema de Bônus Diário recompensa você por acessar o PDL todos os dias.</p>
                        
                        <h4>🎁 Como Funciona:</h4>
                        <ul>
                            <li>Acesse o PDL uma vez por dia</li>
                            <li>Resgate seu bônus diário</li>
                            <li>Quanto mais dias consecutivos, melhores os prêmios</li>
                        </ul>
                        
                        <h4>📅 Acessar o Bônus Diário:</h4>
                        <ol>
                            <li>Faça login no PDL</li>
                            <li>Clique em <strong>"Bônus Diário"</strong> ou no pop-up que aparece</li>
                            <li>Clique em <strong>"Resgatar"</strong></li>
                            <li>O prêmio vai para sua Bag ou Carteira</li>
                        </ol>
                        
                        <h4>📈 Sequência de Dias:</h4>
                        <ul>
                            <li>Dia 1: Prêmio básico</li>
                            <li>Dia 2-6: Prêmios progressivamente melhores</li>
                            <li>Dia 7: Prêmio especial de semana completa!</li>
                            <li>Após 7 dias, o ciclo reinicia com prêmios ainda melhores</li>
                        </ul>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li>Se perder um dia, a sequência pode resetar</li>
                            <li>O bônus reseta à meia-noite (horário do servidor)</li>
                            <li>Acesse diariamente para maximizar recompensas</li>
                        </ul>
                        
                        <h4>📊 Histórico:</h4>
                        <ul>
                            <li>Veja seu histórico de bônus resgatados</li>
                            <li>Acompanhe sua sequência atual</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How does Daily Bonus work?',
                        'answer': '''
                        <h3>Daily Bonus</h3>
                        <p>The Daily Bonus system rewards you for accessing PDL every day.</p>
                        
                        <h4>🎁 How it Works:</h4>
                        <ul>
                            <li>Access PDL once a day</li>
                            <li>Claim your daily bonus</li>
                            <li>More consecutive days = better prizes</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo funciona el Bono Diario?',
                        'answer': '''
                        <h3>Bono Diario</h3>
                        <p>El sistema de Bono Diario te recompensa por acceder al PDL todos los días.</p>
                        '''
                    }
                }
            },
            # ==================== JOGOS: ROLETA, DADOS, PESCA, SLOTS, CAIXAS ====================
            {
                'is_public': True,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Quais minigames estão disponíveis e como jogar?',
                        'answer': '''
                        <h3>Minigames Disponíveis</h3>
                        <p>O PDL oferece diversos minigames para você se divertir e ganhar prêmios.</p>
                        
                        <h4>🎰 Roleta (Roulette):</h4>
                        <ul>
                            <li>Gire a roleta e ganhe prêmios aleatórios</li>
                            <li>Cada giro tem um custo (moedas ou tokens)</li>
                            <li>Prêmios variam de itens comuns a raros</li>
                            <li>Acesse: <strong>"Minigames → Roleta"</strong></li>
                        </ul>
                        
                        <h4>🎲 Jogo de Dados (Dice Game):</h4>
                        <ul>
                            <li>Role os dados e tente a sorte</li>
                            <li>Aposte em números ou combinações</li>
                            <li>Quanto maior o risco, maior a recompensa</li>
                            <li>Acesse: <strong>"Minigames → Dados"</strong></li>
                        </ul>
                        
                        <h4>🎣 Pesca (Fishing Game):</h4>
                        <ul>
                            <li>Participe de pescarias virtuais</li>
                            <li>Pegue peixes que dão recompensas</li>
                            <li>Peixes raros dão prêmios melhores</li>
                            <li>Acesse: <strong>"Minigames → Pesca"</strong></li>
                        </ul>
                        
                        <h4>🎰 Caça-Níqueis (Slot Machine):</h4>
                        <ul>
                            <li>Estilo casino clássico</li>
                            <li>Combine símbolos para ganhar</li>
                            <li>Jackpots especiais disponíveis</li>
                            <li>Acesse: <strong>"Minigames → Slots"</strong></li>
                        </ul>
                        
                        <h4>📦 Abertura de Caixas (Box Opening):</h4>
                        <ul>
                            <li>Compre ou ganhe caixas misteriosas</li>
                            <li>Abra para descobrir o que tem dentro</li>
                            <li>Caixas diferentes têm prêmios diferentes</li>
                            <li>Acesse: <strong>"Minigames → Caixas"</strong></li>
                        </ul>
                        
                        <h4>💰 Moedas e Tokens:</h4>
                        <ul>
                            <li>Minigames usam tokens ou moedas especiais</li>
                            <li>Ganhe tokens em eventos ou compre na loja</li>
                            <li>Veja seu saldo de tokens no painel</li>
                        </ul>
                        
                        <h4>🏆 Rankings:</h4>
                        <ul>
                            <li>Cada minigame tem seu próprio ranking</li>
                            <li>Veja quem mais ganhou</li>
                            <li>Compita para ficar no topo!</li>
                        </ul>
                        
                        <h4>⚠️ Jogue com Responsabilidade:</h4>
                        <ul>
                            <li>Defina um limite de gastos</li>
                            <li>Minigames são para diversão</li>
                            <li>Não gaste mais do que pode</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What minigames are available and how to play?',
                        'answer': '''
                        <h3>Available Minigames</h3>
                        <p>PDL offers several minigames for you to have fun and win prizes.</p>
                        
                        <h4>🎰 Roulette:</h4>
                        <ul>
                            <li>Spin the wheel and win random prizes</li>
                        </ul>
                        
                        <h4>🎲 Dice Game:</h4>
                        <ul>
                            <li>Roll dice and try your luck</li>
                        </ul>
                        
                        <h4>🎣 Fishing:</h4>
                        <ul>
                            <li>Catch fish for rewards</li>
                        </ul>
                        
                        <h4>🎰 Slot Machine:</h4>
                        <ul>
                            <li>Classic casino style slots</li>
                        </ul>
                        
                        <h4>📦 Box Opening:</h4>
                        <ul>
                            <li>Open mystery boxes for prizes</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Qué minijuegos están disponibles y cómo jugar?',
                        'answer': '''
                        <h3>Minijuegos Disponibles</h3>
                        <p>El PDL ofrece varios minijuegos para divertirte y ganar premios.</p>
                        '''
                    }
                }
            },
            # ==================== TOKENS E MOEDAS ESPECIAIS ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'O que são Tokens e como conseguir?',
                        'answer': '''
                        <h3>Sistema de Tokens</h3>
                        <p>Tokens são moedas especiais usadas em minigames e funcionalidades específicas do PDL.</p>
                        
                        <h4>🪙 O que são Tokens:</h4>
                        <ul>
                            <li>Moeda especial do sistema</li>
                            <li>Usados em minigames (roleta, caixas, etc.)</li>
                            <li>Diferentes dos reais da carteira</li>
                        </ul>
                        
                        <h4>💰 Como Conseguir Tokens:</h4>
                        <ul>
                            <li><strong>Comprar:</strong> Na loja do PDL</li>
                            <li><strong>Eventos:</strong> Prêmios de eventos especiais</li>
                            <li><strong>Battle Pass:</strong> Recompensas de níveis</li>
                            <li><strong>Bônus Diário:</strong> Alguns dias dão tokens</li>
                            <li><strong>Conquistas:</strong> Desbloqueando achievements</li>
                            <li><strong>Promoções:</strong> Ofertas especiais</li>
                        </ul>
                        
                        <h4>📊 Ver Saldo de Tokens:</h4>
                        <ul>
                            <li>Veja no Dashboard</li>
                            <li>Veja na página de Minigames</li>
                            <li>Veja em <strong>"Minigames → Histórico de Tokens"</strong></li>
                        </ul>
                        
                        <h4>📜 Histórico:</h4>
                        <ul>
                            <li>Veja todos os tokens ganhos</li>
                            <li>Veja todos os tokens gastos</li>
                            <li>Acompanhe seu saldo ao longo do tempo</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'What are Tokens and how to get them?',
                        'answer': '''
                        <h3>Token System</h3>
                        <p>Tokens are special currency used in minigames and specific PDL features.</p>
                        '''
                    },
                    'es': {
                        'question': '¿Qué son los Tokens y cómo conseguirlos?',
                        'answer': '''
                        <h3>Sistema de Tokens</h3>
                        <p>Los Tokens son monedas especiales usadas en minijuegos y funcionalidades específicas del PDL.</p>
                        '''
                    }
                }
            },
            # ==================== DENUNCIAR CONTEÚDO ====================
            {
                'is_public': False,
                'show_in_internal': True,
                'translations': {
                    'pt': {
                        'question': 'Como denunciar conteúdo ou jogadores?',
                        'answer': '''
                        <h3>Denunciar Conteúdo ou Jogadores</h3>
                        <p>Se você encontrar conteúdo impróprio ou jogadores que violam as regras, pode denunciar.</p>
                        
                        <h4>🚨 O que pode ser denunciado:</h4>
                        <ul>
                            <li>Posts ofensivos na rede social</li>
                            <li>Mensagens abusivas</li>
                            <li>Spam e propaganda</li>
                            <li>Conteúdo impróprio</li>
                            <li>Golpes e fraudes</li>
                            <li>Comportamento tóxico</li>
                            <li>Uso de hacks/cheats</li>
                        </ul>
                        
                        <h4>📝 Como Denunciar:</h4>
                        <ol>
                            <li>No conteúdo (post, mensagem), clique em <strong>"⋮"</strong> ou <strong>"Denunciar"</strong></li>
                            <li>Selecione o motivo da denúncia</li>
                            <li>Adicione detalhes se necessário</li>
                            <li>Envie a denúncia</li>
                        </ol>
                        
                        <h4>🎫 Denúncia por Ticket:</h4>
                        <ol>
                            <li>Acesse <strong>"Suporte → Abrir Ticket"</strong></li>
                            <li>Selecione categoria <strong>"Denúncia"</strong></li>
                            <li>Forneça todas as informações e evidências</li>
                            <li>Anexe prints se possível</li>
                        </ol>
                        
                        <h4>✅ O que acontece após denunciar:</h4>
                        <ul>
                            <li>A equipe analisa a denúncia</li>
                            <li>Ações são tomadas conforme a gravidade</li>
                            <li>Você pode ser notificado do resultado</li>
                            <li>Denúncias são confidenciais</li>
                        </ul>
                        
                        <h4>⚠️ Importante:</h4>
                        <ul>
                            <li>Não faça denúncias falsas</li>
                            <li>Forneça evidências quando possível</li>
                            <li>Denúncias falsas podem resultar em punição</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to report content or players?',
                        'answer': '''
                        <h3>Report Content or Players</h3>
                        <p>If you find inappropriate content or players violating rules, you can report them.</p>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo denunciar contenido o jugadores?',
                        'answer': '''
                        <h3>Denunciar Contenido o Jugadores</h3>
                        <p>Si encuentras contenido inapropiado o jugadores que violan las reglas, puedes denunciar.</p>
                        '''
                    }
                }
            },
        ]
