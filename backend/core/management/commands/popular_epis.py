from django.core.management.base import BaseCommand
from core.models import CategoriaEPI, TipoEPI, Empresa

class Command(BaseCommand):
    help = 'LIMPA e depois POPULA as tabelas de Categorias e Tipos de EPI para todas as empresas'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando limpeza da base de Tipos de EPI...'))
        
        # 1. Apaga dados antigos para evitar duplicidade ou lixo
        deleted_tipos, _ = TipoEPI.objects.all().delete()
        deleted_cats, _ = CategoriaEPI.objects.all().delete()
        
        self.stdout.write(f'Removidos: {deleted_tipos} Tipos de EPI e {deleted_cats} Categorias antigas.')

        # 2. Dados Padrão
        dados_epi = {
            'Proteção da Cabeça': [
                'Capacete de segurança aba frontal',
                'Capacete de segurança aba total',
                'Capuz ou balaclava para proteção térmica',
                'Boné com proteção rígida (casquete)'
            ],
            'Proteção Auditiva': [
                'Protetor auditivo circum-auricular (tipo concha)',
                'Protetor auditivo de inserção (plug de silicone)',
                'Protetor auditivo de inserção (plug de espuma moldável)',
                'Protetor auditivo acoplado ao capacete'
            ],
            'Proteção Respiratória': [
                'Respirador purificador de ar não motorizado (PFF1)',
                'Respirador purificador de ar não motorizado (PFF2/N95)',
                'Respirador purificador de ar não motorizado (PFF3)',
                'Respirador semi-facial com cartucho químico',
                'Respirador facial inteiro',
                'Máscara cirúrgica descartável'
            ],
            'Proteção Visual e Facial': [
                'Óculos de segurança incolor (contra impactos)',
                'Óculos de segurança escuro (contra luminosidade)',
                'Óculos de segurança ampla visão (google)',
                'Protetor facial (face shield)',
                'Máscara de solda (escudo ou automática)',
                'Óculos para maçariqueiro'
            ],
            'Proteção das Mãos': [
                'Luva de vaqueta',
                'Luva de raspa',
                'Luva de malha pigmentada',
                'Luva nitrílica (proteção química)',
                'Luva de látex natural',
                'Luva de PVC',
                'Luva tátil (poliamida/PU)',
                'Luva isolante de borracha (alta tensão)',
                'Luva de proteção contra corte (fios de aço/kevlar)',
                'Luva térmica (alta/baixa temperatura)'
            ],
            'Proteção dos Pés': [
                'Botina de segurança com biqueira de aço',
                'Botina de segurança com biqueira de composite/plástico',
                'Sapato de segurança ocupacional',
                'Bota de PVC (galocha) impermeável',
                'Bota de PVC cano longo',
                'Perneira de segurança (raspa ou sintética)'
            ],
            'Proteção do Corpo': [
                'Avental de raspa',
                'Avental de PVC impermeável',
                'Macacão de segurança (tipo Tyvek)',
                'Vestimenta de proteção contra arco elétrico',
                'Capa de chuva',
                'Colete reflexivo',
                'Manguito de proteção'
            ],
            'Proteção Contra Quedas': [
                'Cinturão de segurança tipo paraquedista',
                'Cinturão abdominal',
                'Talabarte em Y com absorvedor de energia',
                'Talabarte de posicionamento',
                'Trava-quedas deslizante',
                'Trava-quedas retrátil'
            ],
            'Cremes Protetores': [
                'Creme protetor solar (Fator 30+)',
                'Creme protetor solar (Fator 60+)',
                'Creme de proteção contra agentes químicos (Luva química)',
                'Repelente de insetos'
            ]
        }

        empresas = Empresa.objects.all()
        if not empresas.exists():
             self.stdout.write(self.style.ERROR('Nenhuma empresa cadastrada no sistema.'))
             return

        total_geral = 0
        
        self.stdout.write('Recriando EPIs para todas as empresas...')
        
        for empresa in empresas:
            for nome_categoria, lista_tipos in dados_epi.items():
                # Cria Categoria
                CategoriaEPI.objects.get_or_create(empresa=empresa, nome=nome_categoria)
                
                # Cria Tipos
                for nome_tipo in lista_tipos:
                    TipoEPI.objects.create(empresa=empresa, nome=nome_tipo)
                    total_geral += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído! {total_geral} tipos de EPI foram recriados e vinculados.'))