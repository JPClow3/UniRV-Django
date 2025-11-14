"""
Management command to populate editais from PDF files in docs extras folder.
Extracts basic information from filenames and creates edital entries.
"""
import os
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from editais.models import Edital, EditalValor, Cronograma


class Command(BaseCommand):
    help = "Populate editais from PDF files in 'docs extras' folder"

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-path',
            type=str,
            default='docs extras',
            help='Path to folder containing PDF files'
        )

    def extract_info_from_filename(self, filename):
        """Extract edital information from PDF filename"""
        # Remove .pdf extension
        name = filename.replace('.pdf', '').strip()
        
        # Map of known editais with proper titles and entities
        known_editais = {
            '11_11_Pro-Amazonia_2025_Edital': {
                'titulo': 'Edital Pro-Amazônia 2025',
                'entidade_principal': 'Programa Pro-Amazônia',
                'numero_edital': 'Pro-Amazônia 2025',
            },
            '11_11_2025_Edital_FIP_Bioeconomia_e_Sustentabilidade': {
                'titulo': 'Edital FIP - Bioeconomia e Sustentabilidade 2025',
                'entidade_principal': 'FIP - Fundo de Investimento em Pesquisa',
                'numero_edital': 'FIP 2025',
            },
            'Chamada_28_2025___Apoio_a_Manutencao_de_Equipamentos': {
                'titulo': 'Chamada Pública Nº 28/2025 - Apoio à Manutenção de Equipamentos',
                'entidade_principal': 'FAPEG - Fundação de Amparo à Pesquisa do Estado de Goiás',
                'numero_edital': '28/2025',
            },
            'CHAMADA_PUBLICA_FAPEG_N__31_2025___EDITAL_COMPLEMENTAR_A_CHAMADA_CONFAP_ERC_IA_2025': {
                'titulo': 'Chamada Pública FAPEG Nº 31/2025 - Edital Complementar à Chamada CONFAP/ERC IA 2025',
                'entidade_principal': 'FAPEG - Fundação de Amparo à Pesquisa do Estado de Goiás',
                'numero_edital': '31/2025',
            },
            'Edital_27_2025': {
                'titulo': 'Edital 27/2025',
                'entidade_principal': 'FAPEG - Fundação de Amparo à Pesquisa do Estado de Goiás',
                'numero_edital': '27/2025',
            },
            'Edital_Centelha_3_GO___Revisado_final__1_': {
                'titulo': 'Edital Centelha 3 - Goiás (Revisado)',
                'entidade_principal': 'Programa Centelha',
                'numero_edital': 'Centelha 3 GO',
            },
            'EDITAL_PAPIG_INCUBADORAS_REVISADO': {
                'titulo': 'Edital PAPIG - Incubadoras (Revisado)',
                'entidade_principal': 'PAPIG - Programa de Apoio à Pesquisa e Inovação',
                'numero_edital': 'PAPIG Incubadoras',
            },
            'Edital_PEIEX_CORRIGIDO_APOS_PARECER_com_numero__2_': {
                'titulo': 'Edital PEIEX - Corrigido após Parecer',
                'entidade_principal': 'PEIEX - Programa de Extensão Industrial e Exportação',
                'numero_edital': 'PEIEX 2',
            },
        }
        
        # Check if we have a known mapping
        base_name = name.replace(' ', '_').replace('-', '_')
        # Normalize multiple underscores
        while '__' in base_name:
            base_name = base_name.replace('__', '_')
        
        # Try exact match first
        if base_name in known_editais:
            return known_editais[base_name]
        
        # Try partial matches - check if key is contained in filename or vice versa
        for key, info in known_editais.items():
            # Normalize both for comparison
            key_normalized = key.lower().replace('_', '').replace('-', '').replace(' ', '')
            base_normalized = base_name.lower().replace('_', '').replace('-', '').replace(' ', '')
            
            # Check if significant parts match
            if key_normalized in base_normalized or base_normalized in key_normalized:
                return info
            
            # Also check if key words match (at least 2 significant words)
            key_words = set([w for w in key.lower().split('_') if len(w) > 2])
            base_words = set([w for w in base_name.lower().split('_') if len(w) > 2])
            if len(key_words.intersection(base_words)) >= 2:
                return info
            
            # Check for specific keywords
            if 'centelha' in base_name.lower() and 'centelha' in key.lower():
                return info
            if 'peiex' in base_name.lower() and 'peiex' in key.lower():
                return info
        
        # Fallback: Try to extract from filename patterns
        numero_match = re.search(r'(\d+[/_]\d+|N[°º]?\s*(\d+)|Edital[_\s]*(\d+))', name, re.IGNORECASE)
        numero_edital = None
        if numero_match:
            numero_edital = numero_match.group(0).replace('_', '/').replace('N°', '').replace('Nº', '').strip()
        
        # Extract entity/agency from common patterns
        entities = {
            'FAPEG': 'FAPEG - Fundação de Amparo à Pesquisa do Estado de Goiás',
            'FIP': 'FIP - Fundo de Investimento em Pesquisa',
            'PEIEX': 'PEIEX - Programa de Extensão Industrial e Exportação',
            'PAPIG': 'PAPIG - Programa de Apoio à Pesquisa e Inovação',
            'Centelha': 'Programa Centelha',
            'CONFAP': 'CONFAP - Conselho Nacional das Fundações Estaduais de Amparo à Pesquisa',
            'ERC': 'ERC - European Research Council',
            'Pro-Amazonia': 'Programa Pro-Amazônia',
            'Pro-Amazônia': 'Programa Pro-Amazônia',
        }
        
        entidade_principal = None
        for key, value in entities.items():
            if key.lower() in name.lower():
                entidade_principal = value
                break
        
        # Clean title - remove common prefixes and normalize
        titulo = name
        # Remove common prefixes
        titulo = re.sub(r'^(EDITAL|CHAMADA|Edital|Chamada)[_\s]*', '', titulo, flags=re.IGNORECASE)
        titulo = re.sub(r'___+', ' - ', titulo)  # Replace multiple underscores with dash
        titulo = re.sub(r'_+', ' ', titulo)  # Replace single underscores with spaces
        titulo = re.sub(r'\s+', ' ', titulo)  # Normalize spaces
        titulo = titulo.strip()
        
        # Capitalize properly (preserve acronyms)
        words = titulo.split()
        capitalized_words = []
        for word in words:
            if word.isupper() and len(word) > 1:
                capitalized_words.append(word)  # Keep acronyms as-is
            else:
                capitalized_words.append(word.capitalize())
        titulo = ' '.join(capitalized_words)
        
        return {
            'numero_edital': numero_edital,
            'titulo': titulo,
            'entidade_principal': entidade_principal or 'Entidade não identificada',
        }

    def handle(self, *args, **options):
        base_path = Path(options['base_path'])
        
        if not base_path.exists():
            self.stdout.write(self.style.ERROR(f"Path '{base_path}' does not exist."))
            return
        
        # Get all PDF files
        pdf_files = list(base_path.glob('*.pdf'))
        
        if not pdf_files:
            self.stdout.write(self.style.WARNING(f"No PDF files found in '{base_path}'."))
            return
        
        # Get or create a default user for created_by
        user, _ = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@unirv.edu.br',
                'is_staff': True,
                'is_superuser': False,
            }
        )
        
        created_count = 0
        updated_count = 0
        
        for pdf_file in pdf_files:
            # Skip the manual PDF
            if 'Manual' in pdf_file.name or 'manual' in pdf_file.name:
                continue
            
            info = self.extract_info_from_filename(pdf_file.name)
            
            # Create URL pointing to the PDF file
            # Use a relative path that can be accessed - similar to hhdfh structure
            # In production, these should be served from a proper media/static directory
            url = f"http://127.0.0.1:8000/edital/1/"  # Placeholder URL - similar to hhdfh, to be updated manually
            
            # Default values similar to existing editais (following hhdfh structure)
            # Structure with HTML like the reference edital
            objetivo_html = f"""<h3>1. Objetivo do Edital</h3>
<p>Este edital tem como objetivo principal fomentar projetos de pesquisa e inovação na área de {info['titulo']}.</p>
<p>Consulte o documento oficial para informações detalhadas sobre os objetivos específicos deste edital.</p>"""
            
            analise_html = f"""<p><strong>Análise do Edital</strong></p>
<p>Este edital foi importado automaticamente do arquivo PDF. Por favor, complete as informações detalhadas consultando o documento oficial.</p>
<ul>
<li><strong>Entidade:</strong> {info['entidade_principal']}</li>
<li><strong>Número:</strong> {info['numero_edital'] or 'Não informado'}</li>
<li><strong>Status:</strong> Aberto para submissão</li>
</ul>
<p>É necessário revisar e completar as seguintes seções:</p>
<ul>
<li>Etapas do edital</li>
<li>Recursos disponíveis</li>
<li>Itens financiáveis</li>
<li>Critérios de elegibilidade</li>
<li>Critérios de avaliação</li>
<li>Itens essenciais e observações</li>
<li>Pontos específicos para a UniRV</li>
</ul>"""
            
            defaults = {
                'numero_edital': info['numero_edital'],
                'url': url,
                'entidade_principal': info['entidade_principal'],
                'status': 'aberto',  # Default status
                'objetivo': objetivo_html,
                'analise': analise_html,
                'etapas': '<h3>2. Etapas do Edital</h3><p>As etapas deste edital serão definidas após análise do documento oficial.</p>',
                'recursos': '<h3>3. Recursos Disponíveis</h3><p>Os recursos disponíveis serão informados após análise do documento oficial.</p>',
                'itens_financiaveis': '<h4>Itens Financiáveis</h4><p>Consulte o documento oficial para a lista completa de itens financiáveis.</p>',
                'criterios_elegibilidade': '<h4>Critérios de Elegibilidade</h4><p>Consulte o documento oficial para os critérios de elegibilidade.</p>',
                'criterios_avaliacao': '<h4>Critérios de Avaliação</h4><p>Consulte o documento oficial para os critérios de avaliação.</p>',
                'itens_essenciais_observacoes': '<h3>5. Itens Essenciais e Observações</h3><p>Consulte o documento oficial para informações sobre itens essenciais e observações importantes.</p>',
                'detalhes_unirv': '<h3>6. Pontos para a UniRV</h3><p>Informações específicas para a UniRV serão adicionadas após análise detalhada do edital.</p>',
                'created_by': user,
                'updated_by': user,
            }
            
            # Try to get or create edital by title
            edital, created = Edital.objects.get_or_create(
                titulo=info['titulo'],
                defaults=defaults,
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Criado: {info['titulo']}"))
                
                # Create a default valor (can be updated later)
                EditalValor.objects.create(
                    edital=edital,
                    valor_total=None,  # To be filled manually
                    moeda='BRL',
                )
                
                # Create a default cronograma
                Cronograma.objects.create(
                    edital=edital,
                    data_inicio=None,  # To be filled manually
                    data_fim=None,  # To be filled manually
                    descricao="Cronograma a ser definido",
                )
            else:
                # Update if exists but missing key info
                updated = False
                if (not edital.numero_edital or edital.numero_edital == '') and info.get('numero_edital'):
                    edital.numero_edital = info['numero_edital']
                    updated = True
                if (not edital.entidade_principal or edital.entidade_principal == '') and info.get('entidade_principal'):
                    edital.entidade_principal = info['entidade_principal']
                    updated = True
                
                if updated:
                    edital.updated_by = user
                    try:
                        edital.save()
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(f"↻ Atualizado: {info['titulo']}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"✗ Erro ao atualizar {info['titulo']}: {e}"))
                else:
                    self.stdout.write(self.style.WARNING(f"- Já existe: {info['titulo']}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ População concluída: {created_count} novo(s) edital(is) criado(s), {updated_count} atualizado(s)."
        ))

