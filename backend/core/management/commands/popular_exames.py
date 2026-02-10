from django.core.management.base import BaseCommand
from core.models import TipoExame, Empresa

class Command(BaseCommand):
    help = 'Popula a tabela de Tipos de Exame com códigos TUSS padrão'

    def handle(self, *args, **kwargs):
        # Lista dos principais exames ocupacionais e seus códigos TUSS
        exames_padrao = [
            ("Audiometria Ocupacional", "40103661", "Avaliação da capacidade auditiva."),
            ("Espirometria (Prova de Função Pulmonar)", "40105036", "Avaliação da capacidade pulmonar."),
            ("Raio-X de Tórax PA (Padrão OIT)", "40805018", "Radiografia para poeiras minerais."),
            ("Acuidade Visual", "41401066", "Teste de visão básico."),
            ("Hemograma Completo", "40304361", "Análise sanguínea geral."),
            ("Glicemia de Jejum", "40302040", "Nível de açúcar no sangue."),
            ("Eletrocardiograma (ECG)", "40101010", "Avaliação cardíaca em repouso."),
            ("Eletroencefalograma (EEG)", "40103017", "Avaliação da atividade elétrica cerebral."),
            ("Avaliação Psicossocial", "00000001", "Para espaços confinados e altura (sem TUSS específico, código interno)."),
            ("Consulta Clínica Ocupacional (ASO)", "10101012", "Exame clínico geral."),
            ("Audiometria Tonal Limiar", "40103181", "Exame detalhado de audição."),
            ("Dosagem de Chumbo (Sangue)", "40301460", "Para expostos a chumbo."),
            ("Dosagem de Mercúrio (Urina)", "40313212", "Para expostos a mercúrio."),
            ("Retalhos de Coluna", "40804054", "Raio-X de coluna lombo-sacra."),
            ("Vectoeletronistagmografia", "40103637", "Exame de labirinto (trabalho em altura)."),
        ]

        # Tenta pegar a primeira empresa (ajuste se tiver lógica de multi-empresa)
        empresa = Empresa.objects.first()
        
        if not empresa:
            self.stdout.write(self.style.ERROR('ERRO: Nenhuma empresa cadastrada. Cadastre uma empresa antes de rodar este comando.'))
            return

        count = 0
        for nome, tuss, desc in exames_padrao:
            obj, created = TipoExame.objects.get_or_create(
                empresa=empresa,
                codigo_tuss=tuss,
                defaults={'nome': nome, 'descricao': desc}
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Sucesso! {count} novos exames foram cadastrados para a empresa "{empresa.nome_fantasia}".'))