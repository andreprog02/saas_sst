from django.core.management.base import BaseCommand
from core.models import TamanhoEPI, MarcaEPI, Empresa, Localizacao

class Command(BaseCommand):
    help = 'Popula Tamanhos, Marcas e Locais básicos'

    def handle(self, *args, **kwargs):
        tamanhos = ['Único', 'P', 'M', 'G', 'GG', 'XG', '7', '8', '9', '10', '35', '36', '37', '38', '39', '40', '41', '42', '43', '44']
        marcas = ['3M', 'Danny', 'Volk', 'Marluvas', 'Bracol', 'Delta Plus', 'MSA', 'Honeywell']
        locais = ['Almoxarifado Central', 'Armário SST', 'Recepção']

        empresas = Empresa.objects.all()

        for empresa in empresas:
            self.stdout.write(f'Populando para {empresa.nome_fantasia}...')
            
            for tam in tamanhos:
                TamanhoEPI.objects.get_or_create(empresa=empresa, nome=tam)
            
            for marca in marcas:
                MarcaEPI.objects.get_or_create(empresa=empresa, nome=marca.upper())

            for local in locais:
                Localizacao.objects.get_or_create(empresa=empresa, nome=local)

        self.stdout.write(self.style.SUCCESS('Dados auxiliares criados com sucesso!'))