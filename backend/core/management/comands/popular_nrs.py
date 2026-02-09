from django.core.management.base import BaseCommand
from core.models import NormaRegulamentadora

class Command(BaseCommand):
    help = 'Popula o banco de dados com as Normas Regulamentadoras (NRs)'

    def handle(self, *args, **kwargs):
        nrs = [
            ("NR-01", "Disposições Gerais e Gerenciamento de Riscos Ocupacionais"),
            ("NR-02", "Inspeção Prévia (Revogada)"),
            ("NR-03", "Embargo ou Interdição"),
            ("NR-04", "SESMT"),
            ("NR-05", "CIPA"),
            ("NR-06", "Equipamento de Proteção Individual - EPI"),
            ("NR-07", "PCMSO"),
            ("NR-08", "Edificações"),
            ("NR-09", "Avaliação e Controle de Exposições Ocupacionais"),
            ("NR-10", "Segurança em Instalações e Serviços em Eletricidade"),
            ("NR-11", "Transporte, Movimentação, Armazenagem de Materiais"),
            ("NR-12", "Segurança em Máquinas e Equipamentos"),
            ("NR-13", "Caldeiras, Vasos de Pressão e Tubulações"),
            ("NR-14", "Fornos"),
            ("NR-15", "Atividades e Operações Insalubres"),
            ("NR-16", "Atividades e Operações Perigosas"),
            ("NR-17", "Ergonomia"),
            ("NR-18", "Indústria da Construção"),
            ("NR-19", "Explosivos"),
            ("NR-20", "Inflamáveis e Combustíveis"),
            ("NR-21", "Trabalhos a Céu Aberto"),
            ("NR-22", "Segurança e Saúde na Mineração"),
            ("NR-23", "Proteção Contra Incêndios"),
            ("NR-24", "Condições Sanitárias e de Conforto"),
            ("NR-25", "Resíduos Industriais"),
            ("NR-26", "Sinalização de Segurança"),
            ("NR-28", "Fiscalização e Penalidades"),
            ("NR-32", "Segurança em Serviços de Saúde"),
            ("NR-33", "Espaços Confinados"),
            ("NR-35", "Trabalho em Altura"),
            ("NR-38", "Limpeza Urbana e Resíduos Sólidos"),
            # Adicione outras se quiser...
        ]

        for codigo, titulo in nrs:
            obj, created = NormaRegulamentadora.objects.get_or_create(
                codigo=codigo,
                defaults={'titulo': titulo}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Criada: {codigo}'))
            else:
                self.stdout.write(f'Já existe: {codigo}')