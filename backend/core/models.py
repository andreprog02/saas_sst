import os
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone
from django.core.validators import MinValueValidator

# ==============================================================================
# 1. EMPRESA E PERFIL
# ==============================================================================
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

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')
    is_admin = models.BooleanField(default=False)

    def __str__(self): return f"{self.usuario.username} - {self.empresa.nome_fantasia}"

# ==============================================================================
# 2. CADASTROS BÁSICOS (NORMAS, RISCOS, VACINAS)
# ==============================================================================

class NormaRegulamentadora(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.codigo} - {self.titulo}"

class RiscoOcupacional(models.Model):
    TIPO_RISCO = [
        ('FISICO', 'Físico'),
        ('QUIMICO', 'Químico'),
        ('BIOLOGICO', 'Biológico'),
        ('ERGONOMICO', 'Ergonômico'),
        ('ACIDENTE', 'Acidente/Mecânico'),
    ]
    INTENSIDADES = [
        ('PEQUENA', 'Pequena'),
        ('MEDIA', 'Média'),
        ('GRANDE', 'Grande'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_RISCO)
    agente = models.CharField(max_length=100, help_text="Ex: Ruído, Calor, Poeira, Vírus...")
    fonte_geradora = models.CharField(max_length=100, blank=True, null=True)
    intensidade = models.CharField(max_length=20, choices=INTENSIDADES, default='PEQUENA')
    possiveis_danos = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.agente}"

class Vacina(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome da Vacina")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    meses_reforco = models.IntegerField(default=0, verbose_name="Reforço em (meses)", help_text="0 para dose única ou sem reforço automático")

    def __str__(self): return self.nome

# ==============================================================================
# 3. SETOR E FUNCIONÁRIO
# ==============================================================================

class TipoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Tipo")
    def __str__(self): return self.nome

class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    responsavel = models.CharField(max_length=100, null=True, blank=True)
    
    normas = models.ManyToManyField(NormaRegulamentadora, blank=True)
    riscos = models.ManyToManyField(RiscoOcupacional, blank=True)

    def __str__(self):
        return self.nome

class Funcionario(models.Model):
    # --- OPÇÕES DE SELECT (CHOICES) ---
    
    SITUACAO_CHOICES = [
        ('ATIVO', '✅ Em Exercício'),
        ('FERIAS', '🏖️ Férias'),
        ('AFASTADO', '🏥 Afastado (INSS/Médico)'),
        ('LICENCA', '👶 Licença Maternidade/Paternidade'),
        ('SUSPENSO', '⚠️ Suspenso'),
        ('DESLIGADO', '❌ Desligado'),
    ]

    OPCOES_TURNO = [
        ('TURNO_1', '1º Turno (06h - 14h)'),
        ('TURNO_2', '2º Turno (14h - 22h)'),
        ('TURNO_3', '3º Turno (22h - 06h)'),
        ('ADM', 'Administrativo (08h - 18h)'),
    ]

    TIPO_SANGUINEO_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    # --- VÍNCULO PRINCIPAL ---
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    # --- 1. IDENTIFICAÇÃO CIVIL ---
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14)
    rg = models.CharField(max_length=20, null=True, blank=True, verbose_name="RG")
    data_nascimento = models.DateField(null=True, blank=True)
    
    # --- 2. CONTATO ---
    telefone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    # --- 3. ENDEREÇO RESIDENCIAL ---
    cep = models.CharField(max_length=9, null=True, blank=True, verbose_name="CEP")
    endereco = models.CharField(max_length=255, null=True, blank=True, verbose_name="Logradouro")
    numero = models.CharField(max_length=20, null=True, blank=True, verbose_name="Número")
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True, verbose_name="UF")

    # --- 4. DADOS CONTRATUAIS E PROFISSIONAIS ---
    matricula = models.CharField(max_length=20, null=True, blank=True, verbose_name="Matrícula")
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    funcao = models.ForeignKey(Funcao, on_delete=models.SET_NULL, null=True, blank=True)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True)
    
    turno = models.CharField(max_length=20, choices=OPCOES_TURNO, default='ADM', verbose_name="Turno")
    supervisor = models.CharField(max_length=100, verbose_name="Supervisor", null=True, blank=True)
    data_admissao = models.DateField(verbose_name="Data de Admissão")

    # --- 5. SAÚDE E SEGURANÇA (NOVO) ---
    tipo_sanguineo = models.CharField(max_length=5, choices=TIPO_SANGUINEO_CHOICES, null=True, blank=True, verbose_name="Tipo Sanguíneo")
    alergias = models.TextField(null=True, blank=True, verbose_name="Alergias Conhecidas")
    medicamentos = models.TextField(null=True, blank=True, verbose_name="Medicamentos em Uso")
    observacoes_saude = models.TextField(null=True, blank=True, verbose_name="Observações de Saúde")

    # --- 6. MÍDIA E STATUS ---
    foto = models.ImageField(upload_to='funcionarios/', null=True, blank=True)
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default='ATIVO')
    motivo_afastamento = models.CharField(max_length=255, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome
        
    @property
    def cor_status(self):
        """Retorna a cor do badge para o template (Bootstrap classes)"""
        if self.situacao == 'ATIVO': return 'success'
        if self.situacao == 'FERIAS': return 'info'
        if self.situacao == 'AFASTADO': return 'warning'
        if self.situacao == 'LICENCA': return 'primary'
        if self.situacao == 'SUSPENSO': return 'danger'
        if self.situacao == 'DESLIGADO': return 'dark'
        return 'secondary'
# ==============================================================================
# 4. ESTOQUE DE EPIs
# ==============================================================================

class Localizacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Local")
    def __str__(self): return self.nome

class CategoriaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Categoria")
    def __str__(self): return self.nome

class MarcaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Marca")
    def __str__(self): return self.nome

class TamanhoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho")
    def __str__(self): return self.tamanho

class EPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaEPI, on_delete=models.PROTECT, null=True, blank=True)
    marca = models.ForeignKey(MarcaEPI, on_delete=models.PROTECT, null=True, blank=True)
    tamanho = models.ForeignKey(TamanhoEPI, on_delete=models.PROTECT, null=True, blank=True)
    
    modelo = models.CharField(max_length=150, null=True, blank=True)
    ca = models.PositiveIntegerField(default=0)
    quantidade = models.PositiveIntegerField(default=0)
    quantidade_minima = models.PositiveIntegerField(default=5)
    data_validade = models.DateField(null=True, blank=True)
    local = models.ForeignKey(Localizacao, on_delete=models.PROTECT, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self): 
        cat = self.categoria.nome if self.categoria else "Indefinido"
        return f"{cat} {self.modelo} (CA: {self.ca})"
    
    @property
    def status_estoque(self):
        if self.quantidade <= self.quantidade_minima:
            return {'cor': 'danger', 'texto': 'Crítico', 'icon': '⚠️'}
        elif self.quantidade <= (self.quantidade_minima * 1.2):
            return {'cor': 'warning', 'texto': 'Baixo', 'icon': '⚡'}
        return {'cor': 'success', 'texto': 'OK', 'icon': '✅'}

class MovimentacaoEstoque(models.Model):
    TIPO_MOVIMENTO = [('ENTRADA', '➕ Entrada'), ('SAIDA', '➖ Saída')]
    epi = models.ForeignKey(EPI, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMENTO)
    quantidade = models.PositiveIntegerField()
    data_movimento = models.DateField(default=timezone.now)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.tipo == 'ENTRADA': self.epi.quantidade += self.quantidade
            elif self.tipo == 'SAIDA': self.epi.quantidade -= self.quantidade
            self.epi.save()
        super().save(*args, **kwargs)

# ==============================================================================
# 5. ADVERTÊNCIAS
# ==============================================================================
class TipoAdvertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    descricao_padrao = models.TextField(blank=True)
    def __str__(self): return self.titulo

class Advertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='advertencias')
    tipo = models.ForeignKey(TipoAdvertencia, on_delete=models.PROTECT)
    data_incidente = models.DateField()
    detalhes = models.TextField(blank=True)
    reincidente = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if Advertencia.objects.filter(funcionario=self.funcionario, tipo=self.tipo).exists():
                self.reincidente = True
        super().save(*args, **kwargs)

# ==============================================================================
# 6. PRONTUÁRIO
# ==============================================================================
class ControleVacina(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='vacinas')
    vacina = models.ForeignKey(Vacina, on_delete=models.PROTECT)
    data_aplicacao = models.DateField()
    data_proximo_reforco = models.DateField(null=True, blank=True)
    comprovante = models.FileField(upload_to='vacinas_comprovantes/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.data_proximo_reforco and self.vacina.meses_reforco > 0:
            self.data_proximo_reforco = self.data_aplicacao + timedelta(days=self.vacina.meses_reforco * 30)
        super().save(*args, **kwargs)

class EntregaEPI(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='epis_entregues')
    epi = models.ForeignKey(EPI, on_delete=models.PROTECT)
    data_entrega = models.DateField(default=timezone.now)
    quantidade = models.IntegerField(default=1)
    ca_registrado = models.CharField(max_length=50)
    validade_ca = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    termo_assinado = models.FileField(upload_to='epis_termos/', blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new:
            self.ca_registrado = str(self.epi.ca)
            if self.epi.data_validade: self.validade_ca = self.epi.data_validade
        super().save(*args, **kwargs)
        if is_new:
             MovimentacaoEstoque.objects.create(
                epi=self.epi, tipo='SAIDA', quantidade=self.quantidade,
                data_movimento=self.data_entrega, funcionario=self.funcionario,
                observacao="Entrega ao funcionário"
            )

class TreinamentoFuncionario(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='treinamentos')
    nome_treinamento = models.CharField(max_length=200)
    data_realizacao = models.DateField()
    data_validade = models.DateField(null=True, blank=True)
    certificado = models.FileField(upload_to='treinamentos_certificados/', blank=True, null=True)
    
    @property
    def vencido(self):
        if not self.data_validade: return False
        return self.data_validade < date.today()

# ==============================================================================
# 7. EXTINTORES E EQUIPAMENTOS
# ==============================================================================
class Extintor(models.Model):
    # --- SUAS OPÇÕES ORIGINAIS (MANTIDAS) ---
    CLASSES = [
        ('A', 'Classe A (Sólidos: Papel, Madeira, Tecido)'),
        ('B', 'Classe B (Líquidos Inflamáveis)'),
        ('C', 'Classe C (Equipamentos Elétricos)'),
        ('D', 'Classe D (Metais Combustíveis)'),
        ('K', 'Classe K (Óleos e Gorduras)'),
        ('BC', 'Classes B/C (Líquidos e Elétricos)'),
        ('ABC', 'Classes A/B/C (Universal)'),
    ]

    AGENTES = [
        ('AGUA', 'Água Pressurizada (AP)'),
        ('PQS_BC', 'Pó Químico Seco (BC) - Bicarbonato'),
        ('PQS_ABC', 'Pó Químico Seco (ABC) - Monofosfato'),
        ('CO2', 'Gás Carbônico (CO2)'),
        ('ESPUMA', 'Espuma Mecânica'),
        ('HALON', 'Agentes Limpos (Halogenados/Fe-36)'),
        ('METAL', 'Pó Especial (Classe D)'),
        ('ACETATO', 'Acetato de Potássio (Classe K)'),
    ]

    SITUACAO = [
        ('ATIVO', '✅ Ativo / Operante'),
        ('MANUTENCAO', '🛠️ Em Manutenção'),
        ('DESCARREGADO', '⚠️ Descarregado / Vazio'),
        ('VENCIDO', '❌ Vencido')
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # --- IDENTIFICAÇÃO ---
    codigo_patrimonial = models.CharField(max_length=50, verbose_name="Código/Patrimônio")
    numero_serie = models.CharField(max_length=100, verbose_name="Número de Série")
    
    # Seus campos técnicos originais
    classe = models.CharField(max_length=5, choices=CLASSES, verbose_name="Classe de Fogo")
    agente = models.CharField(max_length=20, choices=AGENTES, verbose_name="Agente Extintor")
    capacidade = models.IntegerField(verbose_name="Capacidade (kg/L)", help_text="Ex: 6 para 6kg")
    
    # === NOVOS CAMPOS (Que estavam faltando e causando erro) ===
    fabricante = models.CharField(max_length=150, verbose_name="Fabricante", null=True, blank=True)
    data_fabricacao = models.DateField(verbose_name="Data de Fabricação", null=True, blank=True)

    # --- LOCALIZAÇÃO ---
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Localização")
    classe_risco = models.CharField(max_length=100, verbose_name="Risco do Local", blank=True)
    
    # === NOVOS CAMPOS DE LOCALIZAÇÃO ===
    andar = models.CharField(max_length=50, verbose_name="Andar/Pavimento", null=True, blank=True)
    setor = models.CharField(max_length=100, verbose_name="Setor Específico", null=True, blank=True)
    
    altura_instalacao = models.DecimalField(max_digits=4, decimal_places=2, default=1.60, verbose_name="Altura (m)")
    sinalizacao_ok = models.BooleanField(default=True, verbose_name="Sinalização OK?")
    acesso_livre = models.BooleanField(default=True, verbose_name="Acesso Livre?")

    # --- MANUTENÇÃO E DATAS ---
    data_ultima_manutencao = models.DateField(verbose_name="Última Recarga")
    data_proxima_manutencao = models.DateField(verbose_name="Próxima Recarga")
    data_teste_hidrostatico = models.DateField(verbose_name="Teste Hidrostático (5 anos)")
    
    # === NOVOS CAMPOS DE MANUTENÇÃO ===
    data_instalacao = models.DateField(verbose_name="Data de Instalação", null=True, blank=True)
    data_ultima_inspecao = models.DateField(verbose_name="Última Inspeção Visual", null=True, blank=True)
    observacoes = models.TextField(verbose_name="Observações", blank=True)

    # --- STATUS ---
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='ATIVO')
    qrcode_imagem = models.ImageField(upload_to='qrcodes_extintores/', blank=True, null=True)

    def __str__(self): return f"{self.codigo_patrimonial} - {self.get_agente_display()}"
    
class InspecaoExtintor(models.Model):
    extintor = models.ForeignKey(Extintor, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    
    # Campos booleanos de check-list
    lacre_intacto = models.BooleanField(default=True)
    manometro_pressao_ok = models.BooleanField(default=True)
    mangueira_integra = models.BooleanField(default=True)
    
    observacoes = models.TextField(blank=True)

class FotoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoExtintor, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='inspecoes_extintores/')

class Equipamento(models.Model):
    # Opções baseadas no arquivo React enviado
    TIPOS = [
        ('HIDRANTE', 'Hidrante'),
        ('MANGUEIRA', 'Mangueira de Incêndio'),
        ('SPRINKLER', 'Sprinkler'),
        ('ALARME', 'Alarme de Incêndio'),
        ('DETECTOR', 'Detector de Fumaça'),
        ('ILUMINACAO', 'Iluminação de Emergência'),
        ('PORTA', 'Porta Corta-Fogo'),
        ('BOMBA', 'Bomba de Incêndio'),
        ('CENTRAL', 'Central de Alarme'),
        ('OUTRO', 'Outro'),
    ]

    SITUACAO = [
        ('OPERANTE', '✅ Operante'),
        ('MANUTENCAO', '🛠️ Em Manutenção'),
        ('DEFEITO', '⚠️ Com Defeito'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # --- 1. Identificação ---
    codigo = models.CharField(max_length=50, verbose_name="Código", help_text="Ex: HID-001")
    nome = models.CharField(max_length=100, verbose_name="Nome/Identificação", help_text="Ex: Hidrante Bloco A")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='HIDRANTE')
    fabricante = models.CharField(max_length=150, null=True, blank=True)
    capacidade = models.CharField(max_length=100, null=True, blank=True, verbose_name="Capacidade/Especificação", help_text="Ex: 2.5 pol, 30m")
    
    # --- 2. Localização ---
    # Mantemos a FK para Localização (Setor), mas adicionamos o campo texto "pavimento" do React
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Localização (Setor)") 
    pavimento = models.CharField(max_length=50, null=True, blank=True, verbose_name="Pavimento/Andar", help_text="Ex: Térreo")
    
    # --- 3. Manutenção e Datas ---
    data_instalacao = models.DateField(null=True, blank=True, verbose_name="Data de Instalação")
    data_ultima_manutencao = models.DateField(null=True, blank=True, verbose_name="Última Manutenção")
    data_proxima_manutencao = models.DateField(null=True, blank=True, verbose_name="Próxima Manutenção")
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='OPERANTE')
    imagem = models.ImageField(upload_to='equipamentos_incendio/', null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    
class InspecaoEquipamento(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    status = models.CharField(max_length=20, default='OK')
    observacoes = models.TextField(blank=True)

class ArquivoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoEquipamento, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.FileField(upload_to='inspecoes_equipamentos/')

# ==============================================================================
# 8. OUTROS (AFASTAMENTO, ACIDENTES)
# ==============================================================================
class Afastamento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='afastamentos')
    data_inicio = models.DateField()
    data_retorno = models.DateField(null=True, blank=True)
    motivo = models.TextField()
    laudo = models.FileField(upload_to='afastamentos_laudos/', blank=True, null=True)

class AcidenteTrabalho(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='acidentes')
    data_acidente = models.DateField(verbose_name="Data do Acidente")
    hora_acidente = models.TimeField(verbose_name="Hora", null=True, blank=True)
    local = models.CharField(max_length=255, verbose_name="Local do Acidente", null=True, blank=True)
    arquivo_evidencia = models.FileField(upload_to='acidentes_arquivos/', blank=True, null=True, verbose_name="Arquivo/Evidência")
    descricao_motivo = models.TextField(verbose_name="Descrição do Ocorrido")
    cat_emitida = models.BooleanField(default=False, verbose_name="CAT Emitida?")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Acidente - {self.funcionario.nome}"

# ==============================================================================
# 9. QUIMICOS E HOSPITAIS (NOVA ESTRUTURA PARA SAAS)
# ==============================================================================

# Em core/models.py

class ProdutoQuimico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    cas_number = models.CharField(max_length=20, verbose_name="Número CAS", help_text="Ex: 7664-93-9")
    concentracao = models.CharField(max_length=50, help_text="Ex: 98%, 50mg/L")
    fabricante = models.CharField(max_length=200, blank=True)
    classificacao_ghs = models.CharField(max_length=200, verbose_name="Classificação GHS (Códigos)")
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True)
    localizacao = models.CharField(max_length=100)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    unidade = models.CharField(max_length=10, choices=[('L', 'Litros'), ('mL', 'Mililitros'), ('kg', 'Quilos'), ('g', 'Gramas')])
    data_validade_fispq = models.DateField(verbose_name="Validade da FISPQ")
    fispq = models.FileField(upload_to='produtos_quimicos_fispq/', blank=True, null=True)
    observacoes = models.TextField(blank=True)

    def __str__(self): return self.nome

    @property
    def status_fispq(self):
        hoje = date.today()
        if self.data_validade_fispq < hoje: return 'vencida'
        elif self.data_validade_fispq <= hoje + timedelta(days=30): return 'proxima'
        return 'valida'

    # --- PROPRIEDADE IMPORTANTE PARA COMPATIBILIDADE ---
    @property
    def lista_ghs(self):
        """Retorna apenas a lista de códigos (usada por views antigas)"""
        if self.classificacao_ghs:
            return [x.strip() for x in self.classificacao_ghs.split(',')]
        return []

    # --- PROPRIEDADE NOVA PARA O DASHBOARD BONITO ---
    @property
    def ghs_detalhado(self):
        """
        Converte os códigos (H315, H220) em objetos com Ícone, Cor e Descrição.
        """
        # DICIONÁRIO DE MAPEAMENTO (Adicione quantos códigos precisar aqui)
        GHS_MAP = {
            # Físicos (Inflamável, Explosivo) - Ícone Fogo/Explosão
            'H220': {'desc': 'Gás extremamente inflamável', 'tipo': 'fogo', 'cor': 'danger'},
            'H224': {'desc': 'Líquido e vapor extremamente inflamáveis', 'tipo': 'fogo', 'cor': 'danger'},
            'H225': {'desc': 'Líquido e vapor facilmente inflamáveis', 'tipo': 'fogo', 'cor': 'danger'},
            'H226': {'desc': 'Líquido e vapor inflamáveis', 'tipo': 'fogo', 'cor': 'danger'},
            'INFLAMAVEL': {'desc': 'Inflamável', 'tipo': 'fogo', 'cor': 'danger'},
            'H270': {'desc': 'Pode provocar ou agravar incêndios; comburente', 'tipo': 'oxidante', 'cor': 'info'},
            'OXIDANTE': {'desc': 'Oxidante', 'tipo': 'oxidante', 'cor': 'info'},

            # Saúde (Tóxico, Corrosivo, Irritante)
            'H300': {'desc': 'Mortal por ingestão', 'tipo': 'toxico', 'cor': 'dark'},
            'H301': {'desc': 'Tóxico por ingestão', 'tipo': 'toxico', 'cor': 'dark'},
            'H304': {'desc': 'Pode ser fatal se ingerido e penetrar nas vias respiratórias', 'tipo': 'toxico', 'cor': 'dark'},
            'H314': {'desc': 'Provoca queimaduras na pele e lesões oculares graves', 'tipo': 'corrosivo', 'cor': 'purple'},
            'H315': {'desc': 'Provoca irritação cutânea', 'tipo': 'irritante', 'cor': 'warning'},
            'H316': {'desc': 'Provoca irritação cutânea leve', 'tipo': 'irritante', 'cor': 'warning'},
            'H317': {'desc': 'Pode provocar uma reação alérgica na pele', 'tipo': 'irritante', 'cor': 'warning'},
            'H318': {'desc': 'Provoca lesões oculares graves', 'tipo': 'corrosivo', 'cor': 'purple'},
            'H319': {'desc': 'Provoca irritação ocular grave', 'tipo': 'irritante', 'cor': 'warning'},
            'H335': {'desc': 'Pode provocar irritação das vias respiratórias', 'tipo': 'irritante', 'cor': 'warning'},
            'H336': {'desc': 'Pode provocar sonolência ou tonturas', 'tipo': 'irritante', 'cor': 'warning'},
            'H350': {'desc': 'Pode provocar cancro', 'tipo': 'perigo_saude', 'cor': 'dark'},
            'H351': {'desc': 'Carcinogenicidade - Pode provocar câncer', 'tipo': 'perigo_saude', 'cor': 'dark'},
            'H373': {'desc': 'Pode provocar danos aos órgãos por exposição repetida ou prolongada.', 'tipo': 'perigo_saude', 'cor': 'dark'},

            'CORROSIVO': {'desc': 'Corrosivo', 'tipo': 'corrosivo', 'cor': 'purple'},
            'TOXICO': {'desc': 'Tóxico', 'tipo': 'toxico', 'cor': 'dark'},

            # Meio Ambiente
            'H400': {'desc': 'Muito tóxico para os organismos aquáticos', 'tipo': 'ambiente', 'cor': 'success'},
            'H401': {'desc': 'Tóxico para os organismos aquáticos', 'tipo': 'ambiente', 'cor': 'success'},
            'H411': {'desc': 'Tóxico para os organismos aquáticos com efeitos duradouros', 'tipo': 'ambiente', 'cor': 'success'},
        }

        # Separa a string "H315, H411" em lista
        if not self.classificacao_ghs:
            return []

        codigos_limpos = [x.strip().upper() for x in self.classificacao_ghs.split(',')]
        resultado = []

        for codigo in codigos_limpos:
            # Busca no dicionário ou retorna genérico se não achar
            dados = GHS_MAP.get(codigo)
            
            if dados:
                resultado.append({
                    'codigo': codigo,
                    'descricao': dados['desc'],
                    'tipo': dados['tipo'], # Para escolher o SVG
                    'cor': dados['cor']    # Para classe CSS (text-danger, etc)
                })
            else:
                # Caso digite um código que não está no dicionário
                resultado.append({
                    'codigo': codigo,
                    'descricao': 'Perigo não especificado',
                    'tipo': 'generico',
                    'cor': 'secondary'
                })
        
        return resultado

# AGORA SIM, EXPOSIÇÃO PODE SER DEFINIDA (POIS FUNCIONARIO JÁ EXISTE)
class ExposicaoOcupacional(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    produto_quimico = models.ForeignKey(ProdutoQuimico, on_delete=models.CASCADE)
    limite_tolerancia = models.CharField(max_length=50, help_text="Ex: 1 mg/m³ (NR-15)")
    medicao_atual = models.CharField(max_length=50, help_text="Ex: 0.3 mg/m³")
    percentual_exposicao = models.IntegerField(help_text="Porcentagem em relação ao limite")
    data_medicao = models.DateField(default=timezone.now)

    @property
    def status(self):
        if self.percentual_exposicao > 100: return 'critico'
        if self.percentual_exposicao > 75: return 'atencao'
        return 'seguro'

class TipoEspecialidade(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class Hospital(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=50)
    endereco = models.CharField(max_length=255)
    horario_atendimento = models.CharField(max_length=100)
    especialidades = models.ManyToManyField(TipoEspecialidade)
    mapa_link = models.URLField(blank=True, null=True)


class Exame(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='exames')
    tipo = models.CharField(max_length=100, verbose_name="Tipo de Exame", help_text="Ex: Admissional, Audiometria, Hemograma")
    data_realizacao = models.DateField(verbose_name="Data de Realização")
    data_vencimento = models.DateField(verbose_name="Vencimento", null=True, blank=True)
    observacoes = models.TextField(verbose_name="Observações", blank=True)
    arquivo = models.FileField(upload_to='exames_laudos/', verbose_name="Laudo/Documento", null=True, blank=True)

    def __str__(self):
        return f"{self.tipo} - {self.funcionario.nome}"

    @property
    def status(self):
        from datetime import date
        if not self.data_vencimento:
            return 'indefinido'
        if self.data_vencimento < date.today():
            return 'vencido'
        return 'valido'
    

# --- PMOC: AR CONDICIONADO ---
class ArCondicionado(models.Model):
    TIPOS = [
        ('split', 'Split'),
        ('janela', 'Janela'),
        ('cassete', 'Cassete'),
        ('piso_teto', 'Piso Teto'),
        ('multi_split', 'Multi Split'),
        ('central', 'Central'),
        ('fan_coil', 'Fan Coil'),
        ('outro', 'Outro'),
    ]
    
    STATUS = [
        ('ativo', '✅ Ativo'),
        ('manutencao', '🛠️ Em Manutenção'),
        ('inativo', '❌ Inativo'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome/Identificação")
    codigo = models.CharField(max_length=50, verbose_name="Código Tag")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='split')
    
    marca = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    capacidade_btu = models.CharField(max_length=50, null=True, blank=True, verbose_name="Capacidade (BTU)")
    gas_refrigerante = models.CharField(max_length=50, null=True, blank=True, verbose_name="Gás Refrigerante")
    
    localizacao = models.CharField(max_length=150, null=True, blank=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    responsavel_tecnico = models.CharField(max_length=100, null=True, blank=True)
    
    # Datas de Controle
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    data_proxima_manutencao = models.DateField(null=True, blank=True)
    data_ultima_inspecao = models.DateField(null=True, blank=True)
    data_proxima_inspecao = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='ativo')
    observacoes = models.TextField(null=True, blank=True)
    laudo_tecnico = models.FileField(upload_to='pmoc_laudos/', null=True, blank=True, verbose_name="Laudo/PMOC (PDF)")

    def __str__(self): return f"{self.codigo} - {self.nome}"


# --- NR-13: MÁQUINAS E EQUIPAMENTOS ---
class EquipamentoNR13(models.Model):
    TIPOS = [
        ('caldeira', 'Caldeira'),
        ('vaso_pressao', 'Vaso de Pressão'),
        ('tubulacao', 'Tubulação'),
        ('tanque_metalico', 'Tanque Metálico'),
        ('compressor', 'Compressor'),
        ('autoclave', 'Autoclave'),
        ('outro', 'Outro'),
    ]
    
    STATUS = [
        ('ativo', '✅ Ativo'),
        ('manutencao', '🛠️ Em Manutenção'),
        ('inativo', '❌ Inativo'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome/Identificação")
    codigo = models.CharField(max_length=50, verbose_name="Código Tag")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='caldeira')
    
    fabricante = models.CharField(max_length=100, null=True, blank=True)
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    ano_fabricacao = models.IntegerField(null=True, blank=True)
    
    # Especificações Técnicas
    pressao_trabalho = models.CharField(max_length=50, null=True, blank=True, verbose_name="Pressão Trabalho")
    temperatura_trabalho = models.CharField(max_length=50, null=True, blank=True, verbose_name="Temp. Trabalho")
    capacidade = models.CharField(max_length=50, null=True, blank=True, verbose_name="Capacidade/Volume")
    
    localizacao = models.CharField(max_length=150, null=True, blank=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    
    # Datas de Controle
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    data_proxima_manutencao = models.DateField(null=True, blank=True)
    data_ultima_inspecao = models.DateField(null=True, blank=True)
    data_proxima_inspecao = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='ativo')
    observacoes = models.TextField(null=True, blank=True)
    laudo_tecnico = models.FileField(upload_to='nr13_laudos/', null=True, blank=True, verbose_name="Laudo Técnico (PDF)")

    def __str__(self): return f"{self.codigo} - {self.nome}"



class Risco(models.Model):
    TIPO_RISCO = [
        ('FISICO', 'Físico'),
        ('QUIMICO', 'Químico'),
        ('BIOLOGICO', 'Biológico'),
        ('ERGONOMICO', 'Ergonômico'),
        ('ACIDENTE', 'Acidente'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_RISCO)
    descricao = models.CharField(max_length=255)
    codigo_ghs = models.CharField(max_length=20, blank=True, null=True)

    necessita_epi = models.BooleanField(default=False)
    necessita_treinamento = models.BooleanField(default=False)
    necessita_exame = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.descricao} ({self.tipo})"
    


class Funcao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=120)

    def __str__(self):
        return self.nome


class InventarioRisco(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    funcao = models.ForeignKey(Funcao, on_delete=models.CASCADE)
    risco = models.ForeignKey(Risco, on_delete=models.CASCADE)

    epis_obrigatorios = models.ManyToManyField('EPI', blank=True)
    treinamentos_obrigatorios = models.ManyToManyField('Treinamento', blank=True)
    exames_obrigatorios = models.ManyToManyField('Exame', blank=True)
    epcs_obrigatorios = models.ManyToManyField('EPC', blank=True)
    placas_obrigatorias = models.ManyToManyField('PlacaSinalizacao', blank=True)

    def __str__(self):
        return f"{self.setor} - {self.funcao} - {self.risco}"
    

class InspecaoSeguranca(models.Model):
    TIPO = [
        ('PLACA', 'Placa de Sinalização'),
        ('EPC', 'EPC'),
        ('ROTA_FUGA', 'Rota de Fuga'),
        ('PAINEL', 'Painel Elétrico'),
        ('QUIMICO', 'Armazenamento Químico'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO)

    descricao = models.TextField()
    conforme = models.BooleanField(default=True)
    observacao = models.TextField(blank=True, null=True)
    data_inspecao = models.DateField(auto_now_add=True)

    foto = models.ImageField(upload_to='inspecoes/', blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.setor}"
class IncidenteSeguranca(models.Model):
    TIPO = [
        ('QUASE_ACIDENTE', 'Quase Acidente'),
        ('ATO_INSEGURO', 'Ato Inseguro'),
        ('CONDICAO_INSEGURA', 'Condição Insegura'),
        ('ACIDENTE', 'Acidente'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True)

    tipo = models.CharField(max_length=30, choices=TIPO)
    descricao = models.TextField()
    causa = models.TextField(blank=True, null=True)
    plano_acao = models.TextField(blank=True, null=True)
    data_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.setor}"
