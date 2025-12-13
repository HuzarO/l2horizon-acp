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
                            <li><strong>Marketplace:</strong> Compre e venda itens diretamente com outros jogadores</li>
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
                            <li><strong>Marketplace:</strong> Buy and sell items directly with other players</li>
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
                            <li><strong>Marketplace:</strong> Compra y vende ítems directamente con otros jugadores</li>
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
                            <li>Compra e venda de itens diretamente com outros jogadores</li>
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
                            <li>Buy and sell items directly with other players</li>
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
                            <li>Compra y vende ítems directamente con otros jugadores</li>
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
                        <p>O marketplace permite que você compre e venda itens diretamente com outros jogadores, sem intermediários.</p>
                        
                        <h4>Como Comprar no Marketplace:</h4>
                        <ol>
                            <li>Acesse a seção <strong>"Marketplace"</strong> no menu</li>
                            <li>Navegue pelos itens disponíveis para venda</li>
                            <li>Use filtros para encontrar itens específicos</li>
                            <li>Clique no item desejado para ver detalhes</li>
                            <li>Verifique o preço, vendedor e avaliações</li>
                            <li>Clique em <strong>"Comprar"</strong></li>
                            <li>Confirme a compra</li>
                            <li>O item será transferido automaticamente para você</li>
                        </ol>
                        
                        <h4>Como Vender no Marketplace:</h4>
                        <ol>
                            <li>Vá em <strong>"Marketplace → Vender Item"</strong></li>
                            <li>Selecione o item que deseja vender</li>
                            <li>Configure:
                                <ul>
                                    <li>Preço de venda</li>
                                    <li>Quantidade disponível</li>
                                    <li>Descrição do item</li>
                                    <li>Fotos (se disponível)</li>
                                </ul>
                            </li>
                            <li>Publique o anúncio</li>
                            <li>Acompanhe suas vendas em "Minhas Vendas"</li>
                        </ol>
                        
                        <h4>Sistema de Avaliações:</h4>
                        <ul>
                            <li>Após uma transação, você pode avaliar o vendedor/comprador</li>
                            <li>As avaliações ajudam a construir reputação</li>
                            <li>Jogadores com boa reputação têm mais confiança</li>
                            <li>Evite transações com jogadores sem avaliações ou com avaliações negativas</li>
                        </ul>
                        
                        <h4>Dicas de Segurança:</h4>
                        <ul>
                            <li>Sempre verifique o perfil do vendedor antes de comprar</li>
                            <li>Leia as avaliações e comentários de outros jogadores</li>
                            <li>Use o sistema de mensagens para negociar detalhes</li>
                            <li>Em caso de problemas, entre em contato com o suporte</li>
                            <li>Nunca faça transações fora do sistema oficial</li>
                        </ul>
                        '''
                    },
                    'en': {
                        'question': 'How to use the Marketplace?',
                        'answer': '''
                        <h3>PDL Marketplace</h3>
                        <p>The marketplace allows you to buy and sell items directly with other players, without intermediaries.</p>
                        
                        <h4>How to Buy on Marketplace:</h4>
                        <ol>
                            <li>Access the <strong>"Marketplace"</strong> section in the menu</li>
                            <li>Browse items available for sale</li>
                            <li>Use filters to find specific items</li>
                            <li>Click on desired item to see details</li>
                            <li>Check price, seller and ratings</li>
                            <li>Click <strong>"Buy"</strong></li>
                            <li>Confirm purchase</li>
                            <li>Item will be automatically transferred to you</li>
                        </ol>
                        
                        <h4>How to Sell on Marketplace:</h4>
                        <ol>
                            <li>Go to <strong>"Marketplace → Sell Item"</strong></li>
                            <li>Select the item you want to sell</li>
                            <li>Configure:
                                <ul>
                                    <li>Selling price</li>
                                    <li>Available quantity</li>
                                    <li>Item description</li>
                                    <li>Photos (if available)</li>
                                </ul>
                            </li>
                            <li>Publish the listing</li>
                            <li>Track your sales in "My Sales"</li>
                        </ol>
                        
                        <h4>Rating System:</h4>
                        <ul>
                            <li>After a transaction, you can rate the seller/buyer</li>
                            <li>Ratings help build reputation</li>
                            <li>Players with good reputation have more trust</li>
                            <li>Avoid transactions with players without ratings or with negative ratings</li>
                        </ul>
                        
                        <h4>Security Tips:</h4>
                        <ul>
                            <li>Always check seller profile before buying</li>
                            <li>Read reviews and comments from other players</li>
                            <li>Use messaging system to negotiate details</li>
                            <li>In case of problems, contact support</li>
                            <li>Never make transactions outside the official system</li>
                        </ul>
                        '''
                    },
                    'es': {
                        'question': '¿Cómo usar el Marketplace?',
                        'answer': '''
                        <h3>Marketplace del PDL</h3>
                        <p>El marketplace te permite comprar y vender ítems directamente con otros jugadores, sin intermediarios.</p>
                        
                        <h4>Cómo Comprar en el Marketplace:</h4>
                        <ol>
                            <li>Accede a la sección <strong>"Marketplace"</strong> en el menú</li>
                            <li>Navega por los ítems disponibles para venta</li>
                            <li>Usa filtros para encontrar ítems específicos</li>
                            <li>Haz clic en el ítem deseado para ver detalles</li>
                            <li>Verifica el precio, vendedor y evaluaciones</li>
                            <li>Haz clic en <strong>"Comprar"</strong></li>
                            <li>Confirma la compra</li>
                            <li>El ítem se transferirá automáticamente a ti</li>
                        </ol>
                        
                        <h4>Cómo Vender en el Marketplace:</h4>
                        <ol>
                            <li>Ve a <strong>"Marketplace → Vender Ítem"</strong></li>
                            <li>Selecciona el ítem que deseas vender</li>
                            <li>Configura:
                                <ul>
                                    <li>Precio de venta</li>
                                    <li>Cantidad disponible</li>
                                    <li>Descripción del ítem</li>
                                    <li>Fotos (si está disponible)</li>
                                </ul>
                            </li>
                            <li>Publica el anuncio</li>
                            <li>Acompaña tus ventas en "Mis Ventas"</li>
                        </ol>
                        
                        <h4>Sistema de Evaluaciones:</h4>
                        <ul>
                            <li>Después de una transacción, puedes evaluar al vendedor/comprador</li>
                            <li>Las evaluaciones ayudan a construir reputación</li>
                            <li>Los jugadores con buena reputación tienen más confianza</li>
                            <li>Evita transacciones con jugadores sin evaluaciones o con evaluaciones negativas</li>
                        </ul>
                        
                        <h4>Consejos de Seguridad:</h4>
                        <ul>
                            <li>Siempre verifica el perfil del vendedor antes de comprar</li>
                            <li>Lee las evaluaciones y comentarios de otros jugadores</li>
                            <li>Usa el sistema de mensajería para negociar detalles</li>
                            <li>En caso de problemas, contacta con el soporte</li>
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
        ]
