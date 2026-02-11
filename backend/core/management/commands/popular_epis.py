from django.core.management.base import BaseCommand
from core.models import CategoriaEPI, TipoEPI, Empresa

class Command(BaseCommand):
    help = 'Cria Categorias e Tipos de EPI Padrão (NR-6)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Verificando categorias e tipos...')

        # Dados Padrão NR-6
        dados = {
            'Proteção da Cabeça': ['Capacete', 'Capuz', 'Balaclava', 'Boné'],
            'Proteção Auditiva': ['Protetor Concha', 'Protetor Plug', 'Protetor Espuma'],
            'Proteção Respiratória': ['Máscara PFF1', 'Máscara PFF2', 'Respirador Facial'],
            'Proteção Visual': ['Óculos Incolor', 'Óculos Escuro', 'Protetor Facial', 'Máscara Solda'],
            'Proteção das Mãos': ['Luva Vaqueta', 'Luva Raspa', 'Luva Látex', 'Luva Nitrílica', 'Luva Malha'],
            'Proteção dos Pés': ['Botina Biqueira Aço', 'Botina Biqueira Plástico', 'Bota PVC', 'Sapato'],
            'Proteção do Corpo': ['Avental', 'Macacão', 'Capa de Chuva', 'Colete'],
            'Proteção em Altura': ['Cinto Paraquedista', 'Talabarte', 'Trava-quedas']
        }

        empresas = Empresa.objects.all()
        
        if not empresas.exists():
            self.stdout.write(self.style.WARNING('Nenhuma empresa encontrada! Cadastre uma empresa primeiro.'))
            return

        for empresa in empresas:
            for cat_nome, tipos_lista in dados.items():
                # 1. Garante a Categoria
                cat_obj, _ = CategoriaEPI.objects.get_or_create(
                    empresa=empresa, 
                    nome=cat_nome
                )
                
                # 2. Garante os Tipos vinculados
                for tipo_nome in tipos_lista:
                    TipoEPI.objects.get_or_create(
                        empresa=empresa,
                        nome=tipo_nome,
                        defaults={'categoria': cat_obj}
                    )

        self.stdout.write(self.style.SUCCESS('Concluído! Categorias restauradas.'))