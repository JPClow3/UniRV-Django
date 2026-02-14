from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from editais.models import Edital, EditalValor, Cronograma


class Command(BaseCommand):
    help = "Seed the database with sample 'editais' data for local development and populate detail fields for existing editais."

    def _get_detailed_content(self, edital_titulo, edital_numero=""):
        """Generate detailed content for all edital detail fields based on the edital title."""

        # Base content templates that will be customized
        objetivo_base = """
        <p>Este edital tem como objetivo principal fomentar a inovação e o desenvolvimento tecnológico no agronegócio brasileiro, 
        promovendo a integração entre pesquisa, desenvolvimento e mercado.</p>
        <p>Buscamos apoiar projetos que demonstrem potencial de impacto positivo no setor agrícola, 
        com foco em sustentabilidade, eficiência produtiva e inovação tecnológica.</p>
        """

        etapas_base = """
        <h3>Etapas do Processo</h3>
        <ol>
            <li><strong>Inscrição:</strong> Período de 30 dias para submissão de propostas através do portal oficial.</li>
            <li><strong>Análise de Elegibilidade:</strong> Verificação documental e atendimento aos critérios básicos (15 dias).</li>
            <li><strong>Avaliação Técnica:</strong> Análise detalhada por comitê especializado (30 dias).</li>
            <li><strong>Apresentação:</strong> Pitch para banca avaliadora (7 dias).</li>
            <li><strong>Divulgação de Resultados:</strong> Publicação dos projetos aprovados (5 dias após apresentação).</li>
            <li><strong>Contratação:</strong> Assinatura de termos e início dos projetos (30 dias).</li>
        </ol>
        """

        recursos_base = """
        <h3>Recursos Disponíveis</h3>
        <p>O edital disponibiliza recursos financeiros e técnicos para o desenvolvimento dos projetos aprovados:</p>
        <ul>
            <li><strong>Recursos Financeiros:</strong> Até R$ 500.000,00 por projeto, distribuídos em parcelas conforme cronograma de execução.</li>
            <li><strong>Apoio Técnico:</strong> Mentoria especializada, acesso a laboratórios e infraestrutura de pesquisa.</li>
            <li><strong>Networking:</strong> Conexão com investidores, parceiros estratégicos e mercado.</li>
            <li><strong>Capacitação:</strong> Workshops, treinamentos e eventos de capacitação técnica e empresarial.</li>
        </ul>
        <p><strong>Prazo de Execução:</strong> 12 a 24 meses, conforme complexidade do projeto.</p>
        """

        itens_financiaveis_base = """
        <h3>Itens Financiáveis</h3>
        <p>Os recursos podem ser utilizados para os seguintes itens:</p>
        <ul>
            <li>Equipamentos e materiais de pesquisa e desenvolvimento</li>
            <li>Serviços técnicos especializados e consultorias</li>
            <li>Desenvolvimento de protótipos e testes de campo</li>
            <li>Registro de propriedade intelectual (patentes, marcas)</li>
            <li>Participação em eventos, feiras e missões técnicas</li>
            <li>Publicações científicas e divulgação de resultados</li>
            <li>Bolsa de pesquisa para equipe técnica</li>
            <li>Infraestrutura e adequação de espaços físicos (limitado a 20% do total)</li>
        </ul>
        <p><strong>Não são financiáveis:</strong> Despesas administrativas gerais, impostos, financiamento de dívidas ou projetos já concluídos.</p>
        """

        criterios_elegibilidade_base = """
        <h3>Critérios de Elegibilidade</h3>
        <p>Para participar, os proponentes devem atender aos seguintes requisitos:</p>
        <ul>
            <li>Ser pessoa jurídica constituída há pelo menos 6 meses ou pessoa física com CNPJ</li>
            <li>Apresentar proposta técnica e financeira completa e coerente</li>
            <li>Demonstrar capacidade técnica e operacional para execução do projeto</li>
            <li>Não possuir pendências junto a órgãos públicos ou inadimplência fiscal</li>
            <li>Ter experiência comprovada na área do projeto ou parceria com instituição de pesquisa</li>
            <li>Apresentar contrapartida mínima de 20% do valor total do projeto</li>
            <li>Projeto deve estar alinhado com as áreas prioritárias do edital</li>
        </ul>
        """

        criterios_avaliacao_base = """
        <h3>Critérios de Avaliação</h3>
        <p>Os projetos serão avaliados com base nos seguintes critérios e pesos:</p>
        <ul>
            <li><strong>Inovação e Originalidade (25%):</strong> Grau de inovação, diferenciação e potencial disruptivo da solução proposta.</li>
            <li><strong>Viabilidade Técnica (20%):</strong> Capacidade técnica da equipe, metodologia adequada e infraestrutura disponível.</li>
            <li><strong>Impacto e Relevância (20%):</strong> Potencial de impacto no agronegócio, benefícios sociais e ambientais.</li>
            <li><strong>Viabilidade Econômica (15%):</strong> Modelo de negócio, projeções financeiras e sustentabilidade do projeto.</li>
            <li><strong>Capacidade de Execução (10%):</strong> Experiência da equipe, cronograma realista e gestão de riscos.</li>
            <li><strong>Alinhamento Estratégico (10%):</strong> Adequação às políticas públicas e prioridades setoriais.</li>
        </ul>
        <p><strong>Nota Mínima para Aprovação:</strong> 7,0 (sete) pontos, em escala de 0 a 10.</p>
        """

        itens_essenciais_observacoes_base = """
        <h3>Itens Essenciais e Observações</h3>
        <p><strong>Documentação Obrigatória:</strong></p>
        <ul>
            <li>Proposta técnica completa (formato PDF, máximo 50 páginas)</li>
            <li>Proposta financeira detalhada com planilha orçamentária</li>
            <li>Documentos legais da empresa (contrato social, CNPJ, etc.)</li>
            <li>Currículos da equipe técnica</li>
            <li>Comprovante de experiência em projetos similares</li>
            <li>Declaração de não ter pendências fiscais ou trabalhistas</li>
        </ul>
        <p><strong>Observações Importantes:</strong></p>
        <ul>
            <li>O não cumprimento de prazos implica em desclassificação automática</li>
            <li>Projetos com pendências documentais serão desclassificados</li>
            <li>Recursos contra decisões da banca avaliadora não serão aceitos</li>
            <li>Os recursos são liberados mediante apresentação de relatórios técnicos e financeiros</li>
            <li>Projetos aprovados devem manter atualizado o cadastro junto ao órgão financiador</li>
        </ul>
        """

        detalhes_unirv_base = """
        <h3>Pontos Relevantes para a UniRV</h3>
        <p>A Universidade de Rio Verde (UniRV) possui características estratégicas que favorecem a participação neste edital:</p>
        <ul>
            <li><strong>Localização Estratégica:</strong> Situada no coração do agronegócio goiano, com acesso direto a produtores e cooperativas.</li>
            <li><strong>Infraestrutura:</strong> Laboratórios equipados, fazenda experimental e parcerias com empresas do setor.</li>
            <li><strong>Corpo Docente:</strong> Professores com experiência em pesquisa aplicada e extensão rural.</li>
            <li><strong>AgroHub:</strong> Centro de inovação com incubadora de startups e conexão com o ecossistema de inovação.</li>
            <li><strong>Parcerias:</strong> Convênios com instituições de pesquisa nacionais e internacionais.</li>
        </ul>
        <p><strong>Recomendações:</strong></p>
        <ul>
            <li>Envolver professores e pesquisadores da UniRV como coordenadores ou consultores</li>
            <li>Utilizar a infraestrutura da universidade e da fazenda experimental</li>
            <li>Estabelecer parcerias com startups incubadas no AgroHub</li>
            <li>Incluir alunos de pós-graduação como bolsistas de pesquisa</li>
        </ul>
        """

        analise_base = """
        <h2>Análise do Edital</h2>
        <h3>Pontos-Chave</h3>
        <ul>
            <li><strong>Público-Alvo:</strong> Empresas, startups, pesquisadores e instituições de pesquisa focadas em inovação no agronegócio.</li>
            <li><strong>Abrangência:</strong> Nacional, com foco em projetos que demonstrem potencial de aplicação prática.</li>
            <li><strong>Valor Total:</strong> R$ 5.000.000,00 distribuídos entre projetos aprovados.</li>
            <li><strong>Prazo de Inscrição:</strong> 30 dias corridos a partir da publicação.</li>
        </ul>
        <h3>Oportunidades</h3>
        <p>Este edital representa uma excelente oportunidade para projetos que buscam:</p>
        <ul>
            <li>Desenvolver soluções tecnológicas para o campo</li>
            <li>Validar produtos e serviços junto ao mercado</li>
            <li>Estabelecer parcerias estratégicas</li>
            <li>Acessar recursos para pesquisa e desenvolvimento</li>
        </ul>
        <h3>Desafios</h3>
        <p>Principais desafios para participação:</p>
        <ul>
            <li>Necessidade de contrapartida financeira (20% do valor total)</li>
            <li>Documentação completa e detalhada</li>
            <li>Competição com projetos de outras regiões</li>
            <li>Prazos apertados para elaboração da proposta</li>
        </ul>
        """

        # Customize content based on edital title keywords
        if (
            "sustentabilidade" in edital_titulo.lower()
            or "sustentável" in edital_titulo.lower()
        ):
            objetivo_base = """
            <p>Este edital tem como objetivo fomentar pesquisas e projetos que promovam a sustentabilidade no agronegócio, 
            integrando práticas ambientais, sociais e econômicas.</p>
            <p>Buscamos soluções que reduzam o impacto ambiental da produção agrícola, promovam a conservação de recursos naturais 
            e garantam a viabilidade econômica dos produtores rurais.</p>
            """
            itens_financiaveis_base = """
            <h3>Itens Financiáveis</h3>
            <p>Os recursos podem ser utilizados para:</p>
            <ul>
                <li>Projetos de agricultura de baixo carbono e recuperação de áreas degradadas</li>
                <li>Sistemas de produção orgânica e agroecológica</li>
                <li>Tecnologias de economia de água e energia</li>
                <li>Desenvolvimento de bioinsumos e fertilizantes orgânicos</li>
                <li>Sistemas de monitoramento ambiental e rastreabilidade</li>
                <li>Projetos de economia circular e aproveitamento de resíduos</li>
            </ul>
            """
        elif "inovação" in edital_titulo.lower() or "inovação" in edital_titulo.lower():
            objetivo_base = """
            <p>Este edital visa apoiar projetos de inovação tecnológica que transformem o agronegócio brasileiro, 
            promovendo a adoção de tecnologias de ponta e soluções disruptivas.</p>
            <p>Focamos em projetos que integrem inteligência artificial, IoT, biotecnologia e outras tecnologias emergentes 
            para aumentar a produtividade e competitividade do setor.</p>
            """

        return {
            "objetivo": objetivo_base.strip(),
            "etapas": etapas_base.strip(),
            "recursos": recursos_base.strip(),
            "itens_financiaveis": itens_financiaveis_base.strip(),
            "criterios_elegibilidade": criterios_elegibilidade_base.strip(),
            "criterios_avaliacao": criterios_avaliacao_base.strip(),
            "itens_essenciais_observacoes": itens_essenciais_observacoes_base.strip(),
            "detalhes_unirv": detalhes_unirv_base.strip(),
            "analise": analise_base.strip(),
        }

    def handle(self, *args, **options):
        # First, create sample editais if they don't exist
        samples = [
            {
                "numero_edital": "01/2025",
                "titulo": "Programa de Fomento à Inovação no Agro",
                "url": "https://example.com/edital-inovacao-agro",
                "entidade_principal": "Agência de Fomento X",
                "status": "aberto",
                "start_date": timezone.now().date(),
                "end_date": timezone.now().date() + timedelta(days=60),
            },
            {
                "numero_edital": "02/2025",
                "titulo": "Chamamento Público para Pesquisas em Sustentabilidade",
                "url": "https://example.com/chamamento-sustentabilidade",
                "entidade_principal": "Fundação Y",
                "status": "em_andamento",
                "start_date": timezone.now().date() - timedelta(days=30),
                "end_date": timezone.now().date() + timedelta(days=30),
            },
        ]

        created_count = 0
        for data in samples:
            edital, created = Edital.objects.get_or_create(
                titulo=data["titulo"],
                defaults=data,
            )
            if created:
                created_count += 1
                # Attach a sample valor
                EditalValor.objects.create(
                    edital=edital,
                    valor_total=1000000,
                    moeda="BRL",
                )
                # Attach a sample cronograma
                Cronograma.objects.create(
                    edital=edital,
                    data_inicio=timezone.now().date(),
                    data_fim=timezone.now().date() + timedelta(days=30),
                    descricao="Período de submissão de propostas",
                )

        # Now, populate detail fields for all existing editais
        all_editais = Edital.objects.all()
        updated_count = 0

        for edital in all_editais:
            needs_update = False
            detailed_content = self._get_detailed_content(
                edital.titulo, edital.numero_edital or ""
            )

            # Update fields that are empty or None
            for field, content in detailed_content.items():
                current_value = getattr(edital, field, None)
                if not current_value or current_value.strip() == "":
                    setattr(edital, field, content)
                    needs_update = True

            if needs_update:
                edital.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Updated detail fields for: {edital.titulo}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. Created {created_count} new edital(is). Updated {updated_count} existing edital(is) with detailed content."
            )
        )
