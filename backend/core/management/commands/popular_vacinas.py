from django.core.management.base import BaseCommand
from core.models import Vacina, Empresa

class Command(BaseCommand):
    help = 'Popula a tabela de Vacinas com o calendário ocupacional padrão'

    def handle(self, *args, **kwargs):
        # Pega a primeira empresa para associar os dados
        empresa = Empresa.objects.first()
        
        if not empresa:
            self.stdout.write(self.style.ERROR('ERRO: Nenhuma empresa cadastrada. Cadastre uma empresa no sistema antes de rodar este comando.'))
            return

        # Lista de Vacinas Ocupacionais Comuns
        # Formato: (Nome, Meses para Reforço, Descrição/Esquema de Doses)
        # Obs: 0 meses indica que não há reforço automático ou é dose única permanente
        
        lista_vacinas = [
            (
                'Antitetânica (dT)', 
                120, 
                'Proteção contra Tétano e Difteria. Esquema básico de 3 doses. Reforço obrigatório a cada 10 anos.'
            ),
            (
                'Hepatite B', 
                0, 
                'Proteção contra Hepatite B. Esquema padrão de 3 doses (0, 1 e 6 meses). Exige exame Anti-HBs para confirmar imunidade.'
            ),
            (
                'Influenza (Gripe)', 
                12, 
                'Proteção contra o vírus da gripe. Dose única anual (Campanha de Inverno).'
            ),
            (
                'Tríplice Viral (SCR)', 
                0, 
                'Proteção contra Sarampo, Caxumba e Rubéola. Geralmente 2 doses até 29 anos ou 1 dose de 30 a 49 anos.'
            ),
            (
                'Febre Amarela', 
                0, 
                'Indicada para trabalhadores em áreas de risco ou que viajam. Atualmente considera-se dose única (sem reforço), salvo exigências específicas.'
            ),
            (
                'Hepatite A', 
                0, 
                'Recomendada para manipuladores de alimentos e trabalhadores de saneamento. Esquema de 2 doses (0 e 6 meses).'
            ),
            (
                'Raiva', 
                0, 
                'Indicada para veterinários, zootecnistas e manejo de animais. Esquema pré-exposição (Profilaxia).'
            ),
            (
                'COVID-19', 
                0, 
                'Conforme calendário vigente do Ministério da Saúde e PNI.'
            ),
            (
                'Meningocócica C', 
                0, 
                'Dose única. Indicada em casos de surto ou risco biológico específico.'
            ),
            (
                'Varicela (Catapora)', 
                0, 
                'Indicada para profissionais de saúde não imunes. Duas doses com intervalo de 4 a 8 semanas.'
            )
        ]

        total_criados = 0
        
        for nome, reforco, desc in lista_vacinas:
            # get_or_create evita duplicidade se você rodar o comando duas vezes
            obj, created = Vacina.objects.get_or_create(
                empresa=empresa,
                nome=nome,
                defaults={
                    'meses_reforco': reforco,
                    'descricao': desc
                }
            )
            if created:
                total_criados += 1

        if total_criados > 0:
            self.stdout.write(self.style.SUCCESS(f'Sucesso! {total_criados} novas vacinas foram cadastradas para a empresa "{empresa.nome_fantasia}".'))
        else:
            self.stdout.write(self.style.WARNING('As vacinas já existiam no banco de dados. Nenhuma nova foi criada.'))