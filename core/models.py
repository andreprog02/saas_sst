import os
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone

# 1. EMPRESA
class Empresa(models.Model):
    nome_fantasia = models.CharField(max_length=255)
    razao_social = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    telefone = models.CharField(max_length=20)
    email_contato = models.EmailField()
    endereco = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self): return self.nome_fantasia

# 2. PERFIL DE USUÁRIO
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')
    is_admin = models.BooleanField(default=False)

    def __str__(self): return f"{self.usuario.username} - {self.empresa.nome_fantasia}"

# 3. NORMAS E VACINAS (Cadastros Básicos)
class NormaRegulamentadora(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.codigo} - {self.titulo}"

class Vacina(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome da Vacina")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    meses_reforco = models.IntegerField(default=0, verbose_name="Reforço em (meses)", help_text="0 para dose única ou sem reforço automático")

    def __str__(self): return self.nome

# 4. SETOR (Ambiente de Trabalho)
class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    
    # Relacionamentos M2M (Muitos para Muitos)
    nrs_obrigatorias = models.ManyToManyField(NormaRegulamentadora, blank=True, verbose_name="NRs Aplicáveis")
    vacinas_padrao = models.ManyToManyField(Vacina, blank=True, verbose_name="Vacinas Obrigatórias")
    
    # MUDANÇA: EPIs agora são selecionáveis (ligado a TipoEPI)
    epis_obrigatorios = models.ManyToManyField('TipoEPI', blank=True, verbose_name="EPIs Obrigatórios por Tipo")
    
    # Campos de Texto Livre
    treinamentos = models.TextField(verbose_name="Treinamentos", blank=True)

    def __str__(self): return self.nome

# 5. FUNCIONÁRIO
class Funcionario(models.Model):
    # Opções de Situação
    SITUACAO_CHOICES = [
        ('ATIVO', '✅ Em Exercício'),
        ('FERIAS', '🏖️ Férias'),
        ('AFASTADO', '🏥 Afastado (INSS/Médico)'),
        ('LICENCA', '👶 Licença Maternidade/Paternidade'),
        ('SUSPENSO', '⚠️ Suspenso'),
        ('DESLIGADO', '❌ Desligado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    cargo = models.CharField(max_length=100)
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Setor de Trabalho")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    
    # NOVOS CAMPOS DE SITUAÇÃO
    situacao = models.CharField(
        max_length=20, 
        choices=SITUACAO_CHOICES, 
        default='ATIVO', 
        verbose_name="Situação Atual"
    )
    motivo_afastamento = models.TextField(
        blank=True, 
        verbose_name="Detalhes do Afastamento/Desligamento",
        help_text="Preencher apenas se estiver afastado ou desligado."
    )
    
    # Mantemos o 'ativo' para lógica interna do sistema (ex: login), mas a 'situacao' é o que manda no RH
    ativo = models.BooleanField(default=True, verbose_name="Cadastro Ativo no Sistema?")

    def __str__(self): return f"{self.nome} - {self.cargo}"
    
    @property
    def cor_status(self):
        """Retorna a classe de cor do Bootstrap baseada na situação"""
        mapping = {
            'ATIVO': 'success',    # Verde
            'FERIAS': 'info',      # Azul claro
            'AFASTADO': 'warning', # Amarelo
            'LICENCA': 'primary',  # Azul
            'SUSPENSO': 'dark',    # Preto
            'DESLIGADO': 'danger'  # Vermelho
        }
        return mapping.get(self.situacao, 'secondary')

# 6. ESTOQUE DE EPIs
class TipoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Tipo")
    def __str__(self): return self.nome

class Localizacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Local")
    def __str__(self): return self.nome

class EPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoEPI, on_delete=models.PROTECT, verbose_name="Tipo de EPI")
    local = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Localização")
    codigo_unico = models.CharField(max_length=50, verbose_name="Código Interno")
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho")
    ca = models.CharField(max_length=50, verbose_name="C.A.")
    quantidade = models.IntegerField(default=0)
    data_validade = models.DateField(null=True, blank=True, verbose_name="Validade")

    def __str__(self): return f"{self.tipo.nome} - {self.tamanho}"

# 7. ADVERTÊNCIAS
class TipoAdvertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, verbose_name="Motivo da Falta")
    descricao_padrao = models.TextField(verbose_name="Texto Padrão", blank=True)

    def __str__(self): return self.titulo

class Advertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='advertencias')
    tipo = models.ForeignKey(TipoAdvertencia, on_delete=models.PROTECT, verbose_name="Motivo")
    data_incidente = models.DateField(verbose_name="Data do Ocorrido")
    detalhes = models.TextField(verbose_name="Observações", blank=True)
    reincidente = models.BooleanField(default=False, verbose_name="É reincidente?")
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            historico = Advertencia.objects.filter(funcionario=self.funcionario, tipo=self.tipo).exists()
            if historico: self.reincidente = True
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.funcionario.nome} - {self.tipo.titulo}"

# 8. NOVOS MODELOS: PRONTUÁRIO DO FUNCIONÁRIO (VACINAS, EPIs, TREINAMENTOS)

# 8.1 CONTROLE DE VACINAS
class ControleVacina(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='vacinas')
    vacina = models.ForeignKey(Vacina, on_delete=models.PROTECT)
    data_aplicacao = models.DateField(verbose_name="Data da Aplicação")
    data_proximo_reforco = models.DateField(null=True, blank=True, verbose_name="Próximo Reforço")
    comprovante = models.FileField(upload_to='vacinas_comprovantes/', blank=True, null=True, verbose_name="Comprovante (Foto/PDF)")
    
    def save(self, *args, **kwargs):
        # Calcula o reforço automaticamente se não for informado e a vacina tiver periodicidade
        if not self.data_proximo_reforco and self.vacina.meses_reforco > 0:
            self.data_proximo_reforco = self.data_aplicacao + timedelta(days=self.vacina.meses_reforco * 30)
        super().save(*args, **kwargs)

    @property
    def status(self):
        if not self.data_proximo_reforco: return "Dia"
        hj = date.today()
        if self.data_proximo_reforco < hj: return "Vencida"
        if (self.data_proximo_reforco - hj).days <= 30: return "A vencer"
        return "Em dia"

# 8.2 ENTREGA DE EPIs (FICHA DE EPI)
class EntregaEPI(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='epis_entregues')
    epi = models.ForeignKey(EPI, on_delete=models.PROTECT, verbose_name="Item do Estoque")
    data_entrega = models.DateField(default=timezone.now)
    quantidade = models.IntegerField(default=1)
    
    # Snapshoot (Foto) dos dados no momento da entrega
    ca_registrado = models.CharField(max_length=50, verbose_name="CA na Entrega")
    validade_ca = models.DateField(verbose_name="Validade do CA")
    
    data_devolucao = models.DateField(null=True, blank=True, verbose_name="Data de Devolução/Troca")
    termo_assinado = models.FileField(upload_to='epis_termos/', blank=True, null=True, verbose_name="Ficha Assinada")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.ca_registrado = self.epi.ca
            if self.epi.data_validade:
                self.validade_ca = self.epi.data_validade
        super().save(*args, **kwargs)

# 8.3 TREINAMENTOS E CERTIFICADOS
class TreinamentoFuncionario(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='treinamentos')
    nome_treinamento = models.CharField(max_length=200, verbose_name="Nome do Curso/Treinamento")
    data_realizacao = models.DateField(verbose_name="Data Realização")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Validade")
    certificado = models.FileField(upload_to='treinamentos_certificados/', blank=True, null=True, verbose_name="Certificado (PDF/Foto)")
    
    def __str__(self): return self.nome_treinamento

    @property
    def vencido(self):
        if not self.data_validade: return False
        return self.data_validade < date.today()


# 10. GESTÃO DE EXTINTORES
class Extintor(models.Model):
    CLASSES_INCENDIO = [
        ('A', 'Classe A'), ('B', 'Classe B'), ('C', 'Classe C'), 
        ('D', 'Classe D'), ('K', 'Classe K'), 
        ('BC', 'Classes B/C'), ('ABC', 'Classes A/B/C')
    ]
    AGENTES = [
        ('AGUA', 'Água Pressurizada'), ('PQS', 'Pó Químico Seco (PQS)'), 
        ('CO2', 'Gás Carbônico (CO2)'), ('ESPUMA', 'Espuma Mecânica'), 
        ('ACETATO', 'Acetato de Potássio')
    ]
    SITUACAO = [
        ('ATIVO', 'Ativo'), ('MANUTENCAO', 'Em Manutenção'), 
        ('RESERVA', 'Reserva'), ('CONDENADO', 'Condenado')
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # Identificação
    codigo_patrimonial = models.CharField(max_length=50, verbose_name="Cód. Patrimonial", help_text="Ex: EXT-01")
    numero_serie = models.CharField(max_length=100, verbose_name="Nº de Série Cilindro")
    classe = models.CharField(max_length=5, choices=CLASSES_INCENDIO, verbose_name="Classe")
    agente = models.CharField(max_length=20, choices=AGENTES, verbose_name="Agente Extintor")
    capacidade = models.IntegerField(verbose_name="Capacidade (kg/L)")
    
    # Localização
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Local Físico")
    classe_risco = models.CharField(max_length=100, verbose_name="Risco do Local", help_text="Ex: Risco Leve, Risco de Elétrica")

    # Manutenção
    data_ultima_manutencao = models.DateField(verbose_name="Última Recarga")
    data_proxima_manutencao = models.DateField(verbose_name="Vencimento Recarga")
    data_teste_hidrostatico = models.DateField(verbose_name="Vencimento Teste Hidrostático (5 anos)")
    empresa_mantenedora = models.CharField(max_length=200, blank=True)
    numero_lacre = models.CharField(max_length=50, blank=True)

    # Operacional
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='ATIVO', verbose_name="Situação Atual")
    altura_instalacao = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Altura (m)")
    sinalizacao_ok = models.BooleanField(default=True, verbose_name="Sinalização OK?")
    acesso_livre = models.BooleanField(default=True, verbose_name="Acesso Desobstruído?")

    qrcode_imagem = models.ImageField(upload_to='qrcodes_extintores/', blank=True, null=True, verbose_name="QR Code Registrado")

    def __str__(self):
        return f"{self.codigo_patrimonial} ({self.get_agente_display()})"

    @property
    def alerta_manutencao(self):
        """Retorna True se faltar 30 dias ou menos para recarga"""
        if not self.data_proxima_manutencao: return False
        return (self.data_proxima_manutencao - date.today()).days <= 30

    @property
    def alerta_hidrostatico(self):
        """Retorna True se faltar 30 dias ou menos para teste hidrostático"""
        if not self.data_teste_hidrostatico: return False
        return (self.data_teste_hidrostatico - date.today()).days <= 30

# 11. HISTÓRICO DE INSPEÇÕES MENSAIS
class InspecaoExtintor(models.Model):
    extintor = models.ForeignKey(Extintor, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    
    # Itens do Checklist Simplificado
    lacre_intacto = models.BooleanField(default=True, verbose_name="Lacre Intacto?")
    manometro_pressao_ok = models.BooleanField(default=True, verbose_name="Pressão OK?")
    sinalizacao_visivel = models.BooleanField(default=True, verbose_name="Sinalização Visível?")
    acesso_livre = models.BooleanField(default=True, verbose_name="Acesso Livre?")
    mangueira_integra = models.BooleanField(default=True, verbose_name="Mangueira Íntegra?")
    
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Inspeção {self.extintor.codigo_patrimonial} em {self.data_inspecao}"
    
class FotoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoExtintor, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='inspecoes_extintores/', verbose_name="Foto")
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto da inspeção {self.inspecao.id}"
    

class Equipamento(models.Model):
    TIPOS_EQUIPAMENTO = [
        ('HIDRANTE', 'Hidrante'),
        ('MANGUEIRA', 'Mangueira de Incêndio'),
        ('ALARME', 'Alarme / Botoeira'),
        ('LUZ', 'Iluminação de Emergência'),
        ('PLACA', 'Sinalização / Placa'),
        ('PORTA', 'Porta Corta-Fogo'),
        ('OUTRO', 'Outros'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS_EQUIPAMENTO, verbose_name="Tipo de Equipamento")
    nome = models.CharField(max_length=100, verbose_name="Identificação", help_text="Ex: Hidrante 01, Luz do Corredor")
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Localização")
    
    # Dados de Validade/Manutenção
    data_instalacao = models.DateField(null=True, blank=True, verbose_name="Data de Instalação")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Validade / Próxima Manutenção")
    
    # Detalhes Técnicos (Campos genéricos que servem para vários tipos)
    especificacao = models.CharField(max_length=255, blank=True, verbose_name="Especificação", help_text="Ex: 15 metros (para mangueira), 30 LEDs (para luz)")
    ativo = models.BooleanField(default=True, verbose_name="Ativo?")
    
    imagem = models.ImageField(upload_to='outros_equipamentos/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome}"

    @property
    def status_validade(self):
        """Retorna alerta se estiver vencendo em 30 dias"""
        if not self.data_validade:
            return "ok"
        dias = (self.data_validade - date.today()).days
        if dias < 0: return "vencido"
        if dias <= 30: return "alerta"
        return "ok"

# Modelo de Inspeção para esses equipamentos
class InspecaoEquipamento(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    
    # Checklist genérico (aplica-se a quase tudo)
    item_integro = models.BooleanField(default=True, verbose_name="Item Íntegro/Sem Danos?")
    acesso_livre = models.BooleanField(default=True, verbose_name="Acesso Livre?")
    sinalizacao_ok = models.BooleanField(default=True, verbose_name="Sinalização OK?")
    teste_funcional = models.BooleanField(default=True, verbose_name="Teste de Funcionamento OK?")
    
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Inspeção {self.equipamento} em {self.data_inspecao}"
    
class ArquivoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoEquipamento, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.FileField(upload_to='inspecoes_equipamentos/', verbose_name="Arquivo/Foto")
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Arquivo da inspeção {self.inspecao.id}"

    @property
    def eh_imagem(self):
        """Retorna True se a extensão for de imagem"""
        ext = os.path.splitext(self.arquivo.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    

# 9. HISTÓRICO DE AFASTAMENTOS
class Afastamento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='afastamentos')
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_retorno = models.DateField(null=True, blank=True, verbose_name="Data de Retorno (Previsão ou Real)")
    motivo = models.TextField(verbose_name="Motivo / CID")
    laudo = models.FileField(upload_to='afastamentos_laudos/', blank=True, null=True, verbose_name="Laudo Médico (PDF/Foto)")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Afastamento {self.funcionario.nome} - {self.data_inicio}"

    @property
    def dias_afastado(self):
        if self.data_retorno:
            return (self.data_retorno - self.data_inicio).days
        return (date.today() - self.data_inicio).days

# 10. HISTÓRICO DE ACIDENTES DE TRABALHO
class AcidenteTrabalho(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='acidentes')
    data_acidente = models.DateField(verbose_name="Data do Acidente")
    hora_acidente = models.TimeField(verbose_name="Hora")
    local = models.CharField(max_length=255, verbose_name="Local do Acidente")
    descricao_motivo = models.TextField(verbose_name="Descrição do Ocorrido / Motivo")
    arquivo_evidencia = models.FileField(upload_to='acidentes_arquivos/', blank=True, null=True, verbose_name="Fotos/CAT")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Acidente {self.funcionario.nome} em {self.data_acidente}"
    

class ProdutoQuimico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200, verbose_name="Nome do Produto")
    fabricante = models.CharField(max_length=200, verbose_name="Fabricante/Fornecedor")
    
    # Dados de Segurança
    riscos = models.TextField(verbose_name="Riscos e Perigos", help_text="Ex: Inflamável, Corrosivo, Tóxico...")
    telefone_emergencia = models.CharField(max_length=50, verbose_name="Tel. Emergência (Vazamentos)")
    
    # Controle
    lote = models.CharField(max_length=50, blank=True, verbose_name="Nº do Lote")
    data_fabricacao = models.DateField(null=True, blank=True, verbose_name="Data de Fabricação")
    data_validade = models.DateField(verbose_name="Data de Validade")
    
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Local de Armazenamento")
    quantidade = models.CharField(max_length=50, verbose_name="Quantidade Atual", help_text="Ex: 50 Litros, 10 Caixas")
    
    # Documentação
    fispq = models.FileField(upload_to='produtos_quimicos_fispq/', blank=True, null=True, verbose_name="FISPQ (PDF)")
    foto_rotulo = models.ImageField(upload_to='produtos_quimicos_fotos/', blank=True, null=True, verbose_name="Foto do Rótulo")
    
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    @property
    def status_validade(self):
        """Retorna o status para colorir o badge no template"""
        dias = (self.data_validade - date.today()).days
        if dias < 0: return "vencido" # Vermelho
        if dias <= 30: return "alerta" # Amarelo
        return "ok" # Verde
    
class TipoEspecialidade(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

# DEPOIS O HOSPITAL (que usa o tipo)
class Hospital(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=50)
    endereco = models.CharField(max_length=255)
    horario_atendimento = models.CharField(max_length=100, default="24 Horas")
    especialidades = models.ManyToManyField(TipoEspecialidade) # Referência direta agora funciona
    mapa_link = models.URLField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.nome