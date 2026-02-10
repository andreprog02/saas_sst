from django.core.management.base import BaseCommand
from core.models import RiscoOcupacional, Empresa

class Command(BaseCommand):
    help = 'Popula a tabela de Riscos Ocupacionais com a lista padrão completa'

    def handle(self, *args, **kwargs):
        # Mapeamento da lista fornecida
        lista_riscos = [
            # === RISCOS FÍSICOS ===
            ('FISICO', [
                'Ruído contínuo', 'Ruído intermitente', 'Ruído de impacto',
                'Vibração de mãos e braços', 'Vibração de corpo inteiro',
                'Calor radiante', 'Calor por convecção', 'Frio intenso',
                'Umidade excessiva', 'Radiação não ionizante UV', 'Radiação não ionizante IV',
                'Radiação não ionizante micro-ondas', 'Radiação ionizante (raios X)',
                'Radiação ionizante (gama)', 'Pressão hiperbárica', 'Pressão hipobárica',
                'Iluminação insuficiente', 'Iluminação excessiva', 'Ofuscamento',
                'Ventilação inadequada', 'Qualidade do ar deficiente',
                'Campos eletromagnéticos', 'Descargas atmosféricas', 'Eletricidade estática'
            ]),

            # === RISCOS QUÍMICOS ===
            ('QUIMICO', [
                'Poeira mineral', 'Poeira vegetal', 'Poeira metálica',
                'Fumos metálicos', 'Fumos de solda', 'Névoa de óleo', 'Névoa química',
                'Neblina de tinta', 'Gases asfixiantes', 'Gases tóxicos',
                'Vapores orgânicos', 'Vapores inorgânicos', 'Solventes orgânicos',
                'Hidrocarbonetos', 'Ácidos', 'Álcalis', 'Produtos corrosivos',
                'Produtos irritantes', 'Produtos alergênicos', 'Produtos cancerígenos',
                'Produtos mutagênicos', 'Produtos teratogênicos', 'Combustíveis líquidos',
                'Inflamáveis', 'Explosivos químicos', 'Produtos oxidantes',
                'Contato dérmico com químicos', 'Inalação de agentes químicos',
                'Ingestão acidental de químicos'
            ]),

            # === RISCOS BIOLÓGICOS ===
            ('BIOLOGICO', [
                'Vírus', 'Bactérias', 'Fungos', 'Bacilos', 'Protozoários',
                'Parasitas', 'Príons', 'Material biológico contaminado',
                'Sangue contaminado', 'Secreções contaminadas', 'Resíduos hospitalares',
                'Resíduos orgânicos', 'Esgoto in natura', 'Água contaminada',
                'Solo contaminado', 'Animais peçonhentos', 'Insetos vetores',
                'Roedores', 'Picadas e mordidas', 'Mofo e bolor', 'Ambientes insalubres'
            ]),

            # === RISCOS ERGONÔMICOS ===
            ('ERGONOMICO', [
                'Postura inadequada em pé', 'Postura inadequada sentado', 'Postura curvada',
                'Torção de tronco', 'Flexão repetida de coluna', 'Levantamento manual de carga',
                'Transporte manual de carga', 'Empurrar e puxar cargas',
                'Movimentos repetitivos de membros superiores', 'Movimentos repetitivos de membros inferiores',
                'Esforço físico intenso', 'Ritmo excessivo de trabalho', 'Metas abusivas',
                'Jornada prolongada', 'Trabalho noturno', 'Turnos alternados',
                'Monotonia', 'Repetitividade', 'Falta de pausas', 'Estresse ocupacional',
                'Pressão psicológica', 'Assédio moral', 'Trabalho isolado',
                'Atenção constante', 'Uso excessivo de computador', 'Trabalho estático prolongado'
            ]),

            # === RISCOS DE ACIDENTES ===
            ('ACIDENTE', [
                'Queda no mesmo nível', 'Queda de altura', 'Queda em desnível',
                'Choque elétrico direto', 'Choque elétrico indireto', 'Arco elétrico',
                'Incêndio', 'Explosão', 'Projeção de partículas', 'Projeção de cavacos',
                'Projeção de fagulhas', 'Cortes', 'Perfurações', 'Lacerações',
                'Aprisionamento', 'Esmagamento', 'Tombamento de carga', 'Queda de objetos',
                'Máquinas sem proteção', 'Partes móveis expostas', 'Ferramentas defeituosas',
                'Ferramentas inadequadas', 'Piso escorregadio', 'Piso irregular',
                'Falta de guarda-corpo', 'Falta de corrimão', 'Espaço confinado',
                'Trabalho em altura', 'Trabalho em eletricidade', 'Trabalho a quente (solda/corte)',
                'Trânsito de veículos internos', 'Atropelamento', 'Colisão',
                'Falta de sinalização', 'Desorganização do ambiente', 'Armazenamento inadequado',
                'Falta de EPC', 'Falha de procedimento', 'Acesso difícil'
            ])
        ]

        # Pega a primeira empresa para associar (ajuste se tiver lógica de multi-empresa)
        empresa = Empresa.objects.first()
        
        if not empresa:
            self.stdout.write(self.style.ERROR('ERRO: Nenhuma empresa cadastrada. Cadastre uma empresa antes.'))
            return

        total_criados = 0
        
        for tipo_banco, agentes in lista_riscos:
            for agente_nome in agentes:
                obj, created = RiscoOcupacional.objects.get_or_create(
                    empresa=empresa,
                    tipo=tipo_banco,
                    agente=agente_nome,
                    defaults={
                        'intensidade': 'PEQUENA',  # Valor padrão
                        'possiveis_danos': 'A ser avaliado no PGR' # Texto padrão
                    }
                )
                if created:
                    total_criados += 1

        self.stdout.write(self.style.SUCCESS(f'Sucesso! {total_criados} novos riscos foram cadastrados na base de dados.'))