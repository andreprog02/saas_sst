import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

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
# 2. CADASTROS BÁSICOS
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
    INTENSIDADES = [('PEQUENA', 'Pequena'), ('MEDIA', 'Média'), ('GRANDE', 'Grande')]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_RISCO)
    agente = models.CharField(max_length=100)
    fonte_geradora = models.CharField(max_length=100, blank=True, null=True)
    intensidade = models.CharField(max_length=20, choices=INTENSIDADES, default='PEQUENA')
    possiveis_danos = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.get_tipo_display()} - {self.agente}"

class Vacina(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    meses_reforco = models.IntegerField(default=0)

    def __str__(self): return self.nome

class TipoExame(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200, verbose_name="Nome do Exame")
    codigo_tuss = models.CharField(max_length=20, verbose_name="Código TUSS", blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.nome} (TUSS: {self.codigo_tuss or 'N/A'})"

# ==============================================================================
# 3. SETOR E ESTRUTURA
# ==============================================================================

class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    responsavel = models.CharField(max_length=100, null=True, blank=True)
    normas = models.ManyToManyField(NormaRegulamentadora, blank=True)
    riscos = models.ManyToManyField(RiscoOcupacional, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self): return self.nome

class Cargo(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome da Função/Cargo")
    descricao = models.TextField(null=True, blank=True)
    cbo = models.CharField(max_length=20, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self): return self.nome

# ==============================================================================
# 4. FUNCIONÁRIO
# ==============================================================================

class Funcionario(models.Model):
    SITUACAO_CHOICES = [
        ('ATIVO', '✅ Em Exercício'), ('FERIAS', '🏖️ Férias'),
        ('AFASTADO', '🏥 Afastado'), ('LICENCA', '👶 Licença'),
        ('SUSPENSO', '⚠️ Suspenso'), ('DESLIGADO', '❌ Desligado'),
    ]
    OPCOES_TURNO = [('TURNO_1', '1º Turno'), ('TURNO_2', '2º Turno'), ('TURNO_3', '3º Turno'), ('ADM', 'Administrativo')]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14)
    rg = models.CharField(max_length=20, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    cep = models.CharField(max_length=9, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    complemento = models.CharField(max_length=100, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=2, null=True, blank=True)

    matricula = models.CharField(max_length=20, null=True, blank=True)
    
    # --- MUDANÇA AQUI: Cargo agora é um link para a tabela Cargo ---
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, verbose_name="Cargo")
    # ---------------------------------------------------------------
    
    funcao = models.CharField(max_length=100, null=True, blank=True, verbose_name="Função Específica")
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True)
    
    turno = models.CharField(max_length=20, choices=OPCOES_TURNO, default='ADM')
    supervisor = models.CharField(max_length=100, null=True, blank=True)
    data_admissao = models.DateField()

    tipo_sanguineo = models.CharField(max_length=5, null=True, blank=True)
    alergias = models.TextField(null=True, blank=True)
    medicamentos = models.TextField(null=True, blank=True)
    observacoes_saude = models.TextField(null=True, blank=True)

    foto = models.ImageField(upload_to='funcionarios/', null=True, blank=True)
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default='ATIVO')
    motivo_afastamento = models.CharField(max_length=255, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self): return self.nome
        
    @property
    def cor_status(self):
        if self.situacao == 'ATIVO': return 'success'
        if self.situacao == 'FERIAS': return 'info'
        if self.situacao == 'AFASTADO': return 'warning'
        return 'secondary'
    
    
# ==============================================================================
# 5. EPIs (COM OS CAMPOS QUE O FORMULÁRIO PEDE)
# ==============================================================================

class Localizacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class CategoriaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class MarcaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class TamanhoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=20)
    def __str__(self): return self.tamanho

class TipoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class EPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    # Estes campos foram restaurados para corrigir o erro do form
    categoria = models.ForeignKey(CategoriaEPI, on_delete=models.PROTECT, null=True, blank=True)
    marca = models.ForeignKey(MarcaEPI, on_delete=models.PROTECT, null=True, blank=True)
    tamanho = models.ForeignKey(TamanhoEPI, on_delete=models.PROTECT, null=True, blank=True)
    tipo = models.ForeignKey(TipoEPI, on_delete=models.PROTECT, null=True, blank=True)
    local = models.ForeignKey(Localizacao, on_delete=models.PROTECT, null=True, blank=True)
    
    modelo = models.CharField(max_length=150, null=True, blank=True)
    ca = models.PositiveIntegerField(default=0)
    quantidade = models.PositiveIntegerField(default=0)
    quantidade_minima = models.PositiveIntegerField(default=5)
    data_validade = models.DateField(null=True, blank=True)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ativo = models.BooleanField(default=True)

    def __str__(self): 
        return f"{self.modelo or 'EPI'} (CA: {self.ca})"

class MovimentacaoEstoque(models.Model):
    TIPO = [('ENTRADA', '➕ Entrada'), ('SAIDA', '➖ Saída')]
    epi = models.ForeignKey(EPI, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO)
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
# 6. MATRIZ DE RISCOS
# ==============================================================================

class MatrizRiscoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    setor = models.ForeignKey(Setor, on_delete=models.CASCADE)
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    
    riscos = models.ManyToManyField(RiscoOcupacional, blank=True)
    epis_obrigatorios = models.ManyToManyField(TipoEPI, blank=True)
    nrs = models.ManyToManyField(NormaRegulamentadora, blank=True)
    vacinas = models.ManyToManyField(Vacina, blank=True)
    exames = models.ManyToManyField(TipoExame, blank=True)

    class Meta:
        unique_together = ('empresa', 'setor', 'cargo') 

    def __str__(self): return f"{self.setor.nome} - {self.cargo.nome}"

# ==============================================================================
# 7. PRONTUÁRIO E OCORRÊNCIAS
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
    motivo = models.CharField(max_length=50, default='Uso Normal')
    ca_registrado = models.CharField(max_length=50)
    validade_ca = models.DateField(null=True)
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

class Afastamento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='afastamentos')
    data_inicio = models.DateField()
    data_retorno = models.DateField(null=True, blank=True)
    motivo = models.TextField()
    laudo = models.FileField(upload_to='afastamentos_laudos/', blank=True, null=True)

class AcidenteTrabalho(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='acidentes')
    data_acidente = models.DateField()
    hora_acidente = models.TimeField(null=True, blank=True)
    local = models.CharField(max_length=255, null=True, blank=True)
    arquivo_evidencia = models.FileField(upload_to='acidentes_arquivos/', blank=True, null=True)
    descricao_motivo = models.TextField()
    cat_emitida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

# ==============================================================================
# 8. EXTINTORES E EQUIPAMENTOS
# ==============================================================================

class Extintor(models.Model):
    CLASSES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('ABC', 'ABC'), ('BC', 'BC'), ('K', 'K'), ('D', 'D')]
    AGENTES = [('AGUA', 'Água'), ('PQS', 'Pó'), ('CO2', 'CO2'), ('ESPUMA', 'Espuma')]
    SITUACAO = [('ATIVO', 'Ativo'), ('MANUTENCAO', 'Manutenção'), ('VENCIDO', 'Vencido')]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo_patrimonial = models.CharField(max_length=50)
    numero_serie = models.CharField(max_length=100)
    classe = models.CharField(max_length=5, choices=CLASSES)
    agente = models.CharField(max_length=20, choices=AGENTES)
    capacidade = models.IntegerField()
    fabricante = models.CharField(max_length=150, null=True, blank=True)
    data_fabricacao = models.DateField(null=True, blank=True)
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    classe_risco = models.CharField(max_length=100, blank=True)
    andar = models.CharField(max_length=50, null=True, blank=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    altura_instalacao = models.DecimalField(max_digits=4, decimal_places=2, default=1.60)
    sinalizacao_ok = models.BooleanField(default=True)
    acesso_livre = models.BooleanField(default=True)
    data_ultima_manutencao = models.DateField()
    data_proxima_manutencao = models.DateField()
    data_teste_hidrostatico = models.DateField()
    data_instalacao = models.DateField(null=True, blank=True)
    data_ultima_inspecao = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='ATIVO')
    qrcode_imagem = models.ImageField(upload_to='qrcodes_extintores/', blank=True, null=True)

    def __str__(self): return self.codigo_patrimonial
    
class InspecaoExtintor(models.Model):
    extintor = models.ForeignKey(Extintor, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    lacre_intacto = models.BooleanField(default=True)
    manometro_pressao_ok = models.BooleanField(default=True)
    mangueira_integra = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)

class FotoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoExtintor, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='inspecoes_extintores/')

class Equipamento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=50)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, default='HIDRANTE')
    fabricante = models.CharField(max_length=150, null=True, blank=True)
    capacidade = models.CharField(max_length=100, null=True, blank=True)
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    pavimento = models.CharField(max_length=50, null=True, blank=True)
    data_instalacao = models.DateField(null=True, blank=True)
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    data_proxima_manutencao = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    situacao = models.CharField(max_length=20, default='OPERANTE')
    imagem = models.ImageField(upload_to='equipamentos_incendio/', null=True, blank=True)

    def __str__(self): return self.nome
    
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
# 9. QUIMICOS E OUTROS
# ==============================================================================

class ProdutoQuimico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    cas_number = models.CharField(max_length=20)
    concentracao = models.CharField(max_length=50)
    fabricante = models.CharField(max_length=200, blank=True)
    classificacao_ghs = models.CharField(max_length=200)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True)
    localizacao = models.CharField(max_length=100)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    unidade = models.CharField(max_length=10)
    data_validade_fispq = models.DateField()
    fispq = models.FileField(upload_to='produtos_quimicos_fispq/', blank=True, null=True)
    observacoes = models.TextField(blank=True)

    def __str__(self): return self.nome

    @property
    def lista_ghs(self):
        if self.classificacao_ghs:
            return [x.strip() for x in self.classificacao_ghs.split(',')]
        return []

class ExposicaoOcupacional(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    produto_quimico = models.ForeignKey(ProdutoQuimico, on_delete=models.CASCADE)
    limite_tolerancia = models.CharField(max_length=50)
    medicao_atual = models.CharField(max_length=50)
    percentual_exposicao = models.IntegerField()
    data_medicao = models.DateField(default=timezone.now)

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
    tipo = models.CharField(max_length=100)
    data_realizacao = models.DateField()
    data_vencimento = models.DateField(null=True, blank=True)
    observacoes = models.TextField(blank=True)
    arquivo = models.FileField(upload_to='exames_laudos/', null=True, blank=True)

    def __str__(self): return f"{self.tipo} - {self.funcionario.nome}"

class ArCondicionado(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, default='split')
    marca = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    capacidade_btu = models.CharField(max_length=50, null=True, blank=True)
    gas_refrigerante = models.CharField(max_length=50, null=True, blank=True)
    localizacao = models.CharField(max_length=150, null=True, blank=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    responsavel_tecnico = models.CharField(max_length=100, null=True, blank=True)
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    data_proxima_manutencao = models.DateField(null=True, blank=True)
    data_ultima_inspecao = models.DateField(null=True, blank=True)
    data_proxima_inspecao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='ativo')
    observacoes = models.TextField(null=True, blank=True)
    laudo_tecnico = models.FileField(upload_to='pmoc_laudos/', null=True, blank=True)

    def __str__(self): return self.codigo

class EquipamentoNR13(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=20, default='caldeira')
    fabricante = models.CharField(max_length=100, null=True, blank=True)
    numero_serie = models.CharField(max_length=100, null=True, blank=True)
    ano_fabricacao = models.IntegerField(null=True, blank=True)
    pressao_trabalho = models.CharField(max_length=50, null=True, blank=True)
    temperatura_trabalho = models.CharField(max_length=50, null=True, blank=True)
    capacidade = models.CharField(max_length=50, null=True, blank=True)
    localizacao = models.CharField(max_length=150, null=True, blank=True)
    setor = models.CharField(max_length=100, null=True, blank=True)
    data_ultima_manutencao = models.DateField(null=True, blank=True)
    data_proxima_manutencao = models.DateField(null=True, blank=True)
    data_ultima_inspecao = models.DateField(null=True, blank=True)
    data_proxima_inspecao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='ativo')
    observacoes = models.TextField(null=True, blank=True)
    laudo_tecnico = models.FileField(upload_to='nr13_laudos/', null=True, blank=True)

    def __str__(self): return self.codigo


####PGR da empresa

class PGR(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    data_geracao = models.DateTimeField(auto_now_add=True)
    gerado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"PGR gerado em {self.data_geracao}"