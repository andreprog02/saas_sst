from django.db import models
from django.contrib.auth.models import User

# 1. EMPRESA (Base de tudo)
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

# 2. NORMA REGULAMENTADORA (Catálogo)
class NormaRegulamentadora(models.Model):
    codigo = models.CharField(max_length=10, unique=True) # Ex: NR-10
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.codigo} - {self.titulo}"

# 3. SETOR (Depende de Empresa e NR)
class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    
    # Relação com NRs (Muitas NRs para um Setor)
    nrs_obrigatorias = models.ManyToManyField(NormaRegulamentadora, blank=True, verbose_name="NRs Aplicáveis")
    
    # Campos de texto simples
    epis_obrigatorios = models.TextField(verbose_name="EPIs Obrigatórios", blank=True)
    vacinas_necessarias = models.TextField(verbose_name="Vacinas", blank=True)
    treinamentos = models.TextField(verbose_name="Treinamentos", blank=True)

    def __str__(self): return self.nome

# 4. FUNCIONÁRIO (Depende de Empresa e Setor)
class Funcionario(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    cargo = models.CharField(max_length=100)
    
    # Link para o Setor
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Setor de Trabalho")
    
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    ativo = models.BooleanField(default=True)

    def __str__(self): return f"{self.nome} - {self.cargo}"

# 5. PERFIL (Depende de Empresa)
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')
    is_admin = models.BooleanField(default=False)

    def __str__(self): return f"{self.usuario.username} - {self.empresa.nome_fantasia}"