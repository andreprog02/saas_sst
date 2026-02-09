from django.core.management.base import BaseCommand
from core.models import NormaRegulamentadora

class Command(BaseCommand):
    help = 'Popula o banco de dados com as NRs'

    def handle(self, *args, **kwargs):
        nrs = [
            ("NR-01", "Disposições Gerais e Gerenciamento de Riscos Ocupacionais"),
            ("NR-03", "Embargo ou Interdição"),
            ("NR-04", "SESMT"),
            ("NR-05", "CIPA"),
            ("NR-06", "Equipamento de Proteção Individual - EPI"),
            ("NR-07", "PCMSO"),
            ("NR-09", "Avaliação e Controle de Exposições Ocupacionais"),
            ("NR-10", "Segurança em Instalações e Serviços em Eletricidade"),
            ("NR-12", "Segurança em Máquinas e Equipamentos"),
            ("NR-18", "Indústria da Construção"),
            ("NR-20", "Inflamáveis e Combustíveis"),
            ("NR-23", "Proteção Contra Incêndios"),
            ("NR-33", "Espaços Confinados"),
            ("NR-35", "Trabalho em Altura"),
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
