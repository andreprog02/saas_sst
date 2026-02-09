import os

# Define os caminhos
core_path = os.path.join(os.getcwd(), 'core')
mgmt_path = os.path.join(core_path, 'management')
cmd_path = os.path.join(mgmt_path, 'commands')

# 1. Cria as pastas se não existirem
os.makedirs(cmd_path, exist_ok=True)
print(f"Pastas verificadas: {cmd_path}")

# 2. Cria os arquivos __init__.py obrigatórios
with open(os.path.join(mgmt_path, '__init__.py'), 'w') as f: pass
with open(os.path.join(cmd_path, '__init__.py'), 'w') as f: pass
print("Arquivos __init__.py criados.")

# 3. Escreve o código do comando popular_nrs.py
codigo_comando = """from django.core.management.base import BaseCommand
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
"""

arquivo_final = os.path.join(cmd_path, 'popular_nrs.py')
with open(arquivo_final, 'w', encoding='utf-8') as f:
    f.write(codigo_comando)

print(f"SUCESSO! Arquivo de comando criado em: {arquivo_final}")
print("Agora você pode rodar: python manage.py popular_nrs")