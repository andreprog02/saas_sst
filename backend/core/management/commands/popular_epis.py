from django.core.management.base import BaseCommand
from core.models import CategoriaEPI, TipoEPI, Empresa

class Command(BaseCommand):
    help = 'Atualiza Categorias e Tipos de EPI sem apagar dados históricos (Seguro)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando atualização inteligente de EPIs...')

        # Dicionário de Dados Padrão
        dados_epi = {
            'Proteção da Cabeça': [
                'Capacete aba frontal', 'Capacete aba total', 'Capuz/Balaclava', 
                'Boné com proteção'
            ],
            'Proteção Auditiva': [
                'Protetor tipo Concha', 'Protetor tipo Plug (Silicone)', 
                'Protetor de Espuma', 'Protetor acoplado ao capacete'
            ],
            'Proteção Respiratória': [
                'Máscara PFF1', 'Máscara PFF2 (N95)', 'Respirador Facial', 
                'Máscara Semifacial', 'Respirador Motorizado'
            ],
            'Proteção Visual e Facial': [
                'Óculos Incolor', 'Óculos Escuro', 'Protetor Facial (Face Shield)', 
                'Máscara de Solda', 'Óculos de sobreposição'
            ],
            'Proteção das Mãos': [
                'Luva de Vaqueta', 'Luva de Raspa', 'Luva Nitrílica', 
                'Luva de Látex', 'Luva Tátil', 'Luva de Malha', 'Luva de PVC',
                'Luva Isolante'
            ],
            'Proteção dos Pés': [
                'Botina Biqueira de Aço', 'Botina Biqueira de Composite', 
                'Bota de PVC (Galocha)', 'Sapato Social Segurança', 'Perneira'
            ],
            'Proteção do Corpo': [
                'Avental de Raspa', 'Avental de PVC', 'Capa de Chuva', 
                'Colete Reflexivo', 'Macacão Tyvek'
            ],
            'Proteção em Altura': [
                'Cinto Paraquedista', 'Talabarte em Y', 'Trava-quedas',
                'Talabarte de Posicionamento'
            ],
            'Cremes e Outros': [
                'Creme Protetor Solar', 'Creme Luva Química', 'Repelente'
            ]
        }

        empresas = Empresa.objects.all()
        total_cats = 0
        total_tipos = 0

        for empresa in empresas:
            self.stdout.write(f'Processando empresa: {empresa.nome_fantasia}...')
            
            for nome_cat, lista_tipos in dados_epi.items():
                # 1. Busca ou Cria a Categoria (Não deleta!)
                cat_obj, created_cat = CategoriaEPI.objects.get_or_create(
                    empresa=empresa, 
                    nome=nome_cat
                )
                if created_cat: total_cats += 1
                
                for nome_tipo in lista_tipos:
                    # 2. Busca ou Cria o Tipo vinculado à Categoria
                    tipo_obj, created_tipo = TipoEPI.objects.get_or_create(
                        empresa=empresa, 
                        nome=nome_tipo,
                        defaults={'categoria': cat_obj} # Só usa isso se for criar novo
                    )
                    
                    # 3. Se o tipo já existia mas estava sem categoria (ou errada), corrige
                    if not created_tipo and tipo_obj.categoria != cat_obj:
                        tipo_obj.categoria = cat_obj
                        tipo_obj.save()
                        self.stdout.write(f'  -> Corrigido vínculo: {nome_tipo}')

                    if created_tipo: total_tipos += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído! {total_cats} categorias e {total_tipos} tipos novos adicionados/verificados.'))